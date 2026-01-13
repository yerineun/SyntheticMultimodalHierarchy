"""
Raw Trip Processing Script

This script processes origin-destination pairs, fetches transit routes from Google Maps API,
calculates distances, and generates optimized route information.

It reads from random_od_pairs.csv and writes to trip2.csv with the following columns:
- Origin: Origin coordinates (lat,lon)
- Destination: Destination coordinates (lat,lon)
- distance_km: Haversine distance in kilometers
- Optimized Route: Formatted transit route string
"""

import requests
from datetime import datetime, timedelta
import csv
import logging
from math import radians, sin, cos, sqrt, atan2
from typing import Tuple, Optional

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth using the Haversine formula.
    
    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees
        
    Returns:
        Distance between the two points in kilometers
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    # Calculate the result using Earth radius from config
    distance = config.EARTH_RADIUS_KM * c
    return distance


def get_local_departure_time(lat: float, lon: float, api_key: str) -> Optional[int]:
    """
    Get the local departure time (noon) for a given location using Google Timezone API.
    
    Args:
        lat: Latitude of the location
        lon: Longitude of the location
        api_key: Google Maps API key
        
    Returns:
        Unix timestamp for local noon, or None if API call fails
    """
    try:
        tz_url = (
            f"{config.GOOGLE_TIMEZONE_API_URL}"
            f"?location={lat},{lon}"
            f"&timestamp={int(datetime.utcnow().timestamp())}"
            f"&key={api_key}"
        )
        
        response = requests.get(tz_url, timeout=10)
        response.raise_for_status()
        tz_data = response.json()
        
        if tz_data["status"] != "OK":
            logger.warning(f"Time Zone API Error: {tz_data.get('status', 'UNKNOWN')}")
            return None
        
        offset = tz_data["rawOffset"] + tz_data["dstOffset"]
        local_now = datetime.utcnow() + timedelta(seconds=offset)
        local_noon = local_now.replace(
            hour=config.DEPARTURE_HOUR,
            minute=0,
            second=0,
            microsecond=0
        )
        return int(local_noon.timestamp())
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch timezone data: {e}")
        return None
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing timezone response: {e}")
        return None


def fetch_transit_route(
    origin: str,
    destination: str,
    departure_time: int,
    api_key: str
) -> Optional[dict]:
    """
    Fetch transit route from Google Directions API.
    
    Args:
        origin: Origin coordinates as "lat,lon"
        destination: Destination coordinates as "lat,lon"
        departure_time: Unix timestamp for departure time
        api_key: Google Maps API key
        
    Returns:
        Directions API response dictionary, or None if API call fails
    """
    try:
        directions_url = (
            f"{config.GOOGLE_DIRECTIONS_API_URL}"
            f"?origin={origin}"
            f"&destination={destination}"
            f"&mode={config.TRANSIT_MODE}"
            f"&language={config.LANGUAGE}"
            f"&region={config.REGION}"
            f"&departure_time={departure_time}"
            f"&key={api_key}"
        )
        
        response = requests.get(directions_url, timeout=30)
        response.raise_for_status()
        directions_data = response.json()
        
        if directions_data["status"] != "OK":
            logger.warning(f"Directions API Error: {directions_data.get('status', 'UNKNOWN')}")
            return None
        
        return directions_data
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch directions: {e}")
        return None
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing directions response: {e}")
        return None


def format_route(steps: list) -> str:
    """
    Format route steps into a readable string representation.
    
    Args:
        steps: List of route step dictionaries from Google Directions API
        
    Returns:
        Formatted route string (e.g., "walking(5 min) -> subway(10 min)")
    """
    formatted_route = []
    
    for step in steps:
        travel_mode = step.get("travel_mode", "")
        
        if travel_mode == "WALKING":
            duration = step.get("duration", {}).get("text", "")
            formatted_route.append(f"walking({duration})")
            
        elif travel_mode == "TRANSIT":
            try:
                transit_details = step.get("transit_details", {})
                line = transit_details.get("line", {})
                vehicle = line.get("vehicle", {})
                transit_mode = vehicle.get("type", "transit").lower()
                duration = step.get("duration", {}).get("text", "")
                formatted_route.append(f"{transit_mode}({duration})")
            except (KeyError, AttributeError) as e:
                logger.warning(f"Error parsing transit step: {e}")
                # Fallback to generic transit
                duration = step.get("duration", {}).get("text", "")
                formatted_route.append(f"transit({duration})")
    
    return " -> ".join(formatted_route)


def process_od_pair(
    row: list,
    row_number: int,
    api_key: str
) -> Optional[Tuple[str, str, float, str]]:
    """
    Process a single origin-destination pair and return the results.
    
    Args:
        row: CSV row containing [origin_lat, origin_lon, destination_lat, destination_lon]
        row_number: Row number for logging purposes
        api_key: Google Maps API key
        
    Returns:
        Tuple of (origin, destination, distance_km, formatted_route) or None if processing fails
    """
    try:
        # Parse coordinates
        origin_lat = float(row[0])
        origin_lon = float(row[1])
        dest_lat = float(row[2])
        dest_lon = float(row[3])
        
        origin = f"{origin_lat},{origin_lon}"
        destination = f"{dest_lat},{dest_lon}"
        
        logger.info(f"[Row {row_number}] Processing: Origin={origin}, Destination={destination}")
        
        # Get local departure time
        departure_time = get_local_departure_time(origin_lat, origin_lon, api_key)
        if departure_time is None:
            logger.warning(f"[Row {row_number}] Failed to get departure time, skipping")
            return None
        
        # Fetch transit route
        directions_data = fetch_transit_route(origin, destination, departure_time, api_key)
        if directions_data is None:
            logger.warning(f"[Row {row_number}] Failed to fetch route, skipping")
            return None
        
        # Extract route information
        try:
            route = directions_data["routes"][0]["legs"][0]
            steps = route["steps"]
        except (KeyError, IndexError) as e:
            logger.error(f"[Row {row_number}] Error extracting route data: {e}")
            return None
        
        # Format route
        formatted_route = format_route(steps)
        
        # Calculate Haversine distance
        distance_km = haversine(origin_lat, origin_lon, dest_lat, dest_lon)
        
        logger.info(f"[Row {row_number}] Successfully processed")
        return (origin, destination, distance_km, formatted_route)
        
    except (ValueError, IndexError) as e:
        logger.error(f"[Row {row_number}] Error parsing coordinates: {e}")
        return None
    except Exception as e:
        logger.error(f"[Row {row_number}] Unexpected error: {e}", exc_info=True)
        return None


def main():
    """
    Main function to process origin-destination pairs and generate trip data.
    """
    try:
        # Get API key from config
        api_key = config.get_api_key()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please set GOOGLE_MAPS_API_KEY in your .env file or environment variables.")
        return
    
    # Get file paths from config
    input_csv = config.RANDOM_OD_PAIRS_CSV
    output_csv = config.TRIP2_CSV
    
    # Ensure output directory exists
    config.ensure_directory(output_csv)
    
    # Check if input file exists
    if not input_csv.exists():
        logger.error(f"Input file not found: {input_csv}")
        return
    
    logger.info(f"Reading from: {input_csv}")
    logger.info(f"Writing to: {output_csv}")
    
    processed_count = 0
    skipped_count = 0
    
    try:
        with open(input_csv, 'r', newline='', encoding='utf-8') as fin, \
             open(output_csv, 'a', newline='', encoding='utf-8') as fout:
            
            reader = csv.reader(fin)
            writer = csv.writer(fout)
            
            # Skip header row
            next(reader, None)
            
            # Write header if output file is empty
            if fout.tell() == 0:
                writer.writerow(config.TRIP2_COLUMNS)
                logger.info("Created new output file with header")
            
            # Process each row
            for row_number, row in enumerate(reader, start=1):
                if len(row) < 4:
                    logger.warning(f"[Row {row_number}] Insufficient columns, skipping")
                    skipped_count += 1
                    continue
                
                result = process_od_pair(row, row_number, api_key)
                
                if result is not None:
                    origin, destination, distance_km, formatted_route = result
                    writer.writerow([
                        origin,
                        destination,
                        f"{distance_km:.2f}",
                        formatted_route
                    ])
                    processed_count += 1
                else:
                    skipped_count += 1
                    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during file processing: {e}", exc_info=True)
    
    logger.info(f"\nProcessing complete!")
    logger.info(f"  Processed: {processed_count} rows")
    logger.info(f"  Skipped: {skipped_count} rows")
    logger.info(f"  Output saved to: {output_csv}")


if __name__ == "__main__":
    main()
