"""
Script 3: Simplified Trip Processing (Walking Merged)

This script processes raw trip data from stage 2 and simplifies transit routes by:
- Merging consecutive segments of the same transit mode
- Absorbing intermediate walking segments into adjacent transit modes
- Preserving only the first and last walking segments of each trip

Input: trip2.csv (from stage 2)
Output: trip3.csv (simplified routes with 'Total Trip' column)
"""

import re
import pandas as pd
import logging
from pathlib import Path

from config import TRIP2_CSV, TRIP3_CSV, ensure_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convert_time_to_minutes(time_str: str) -> int:
    """
    Convert Korean time string to total minutes.
    
    Parses time strings in Korean format (e.g., '1시간 8분', '29분', '1시간')
    and converts them to total minutes as an integer.
    
    Args:
        time_str: Time string in Korean format (e.g., '1시간 8분', '29분')
        
    Returns:
        Total minutes as integer
        
    Examples:
        >>> convert_time_to_minutes('1시간 8분')
        68
        >>> convert_time_to_minutes('29분')
        29
        >>> convert_time_to_minutes('1시간')
        60
    """
    hours = 0
    minutes = 0
    
    if '시간' in time_str:
        hours_match = re.search(r'(\d+)\s*시간', time_str)
        if hours_match:
            hours = int(hours_match.group(1))
    
    if '분' in time_str:
        minutes_match = re.search(r'(\d+\.?\d*)\s*분', time_str)
        if minutes_match:
            minutes = float(minutes_match.group(1))
    
    return int(hours * 60 + minutes)


def convert_minutes_to_time(minutes: int) -> str:
    """
    Convert total minutes to Korean time string format.
    
    Converts an integer number of minutes back to Korean time format,
    showing hours and/or minutes as appropriate.
    
    Args:
        minutes: Total minutes as integer
        
    Returns:
        Time string in Korean format (e.g., '1시간 8분', '29분', '1시간')
        
    Examples:
        >>> convert_minutes_to_time(68)
        '1시간 8분'
        >>> convert_minutes_to_time(29)
        '29분'
        >>> convert_minutes_to_time(60)
        '1시간'
    """
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0 and mins > 0:
        return f"{hours}시간 {mins}분"
    elif hours > 0:
        return f"{hours}시간"
    else:
        return f"{mins}분"


def simplify_trip(trip: str) -> str:
    """
    Simplify a transit trip route by merging consecutive modes and handling walking segments.
    
    This function processes a trip route string and applies the following simplifications:
    1. Merges consecutive segments of the same transit mode (e.g., bus, subway)
    2. Absorbs intermediate walking segments into adjacent transit modes
    3. Preserves only the first and last walking segments of the trip
    
    Args:
        trip: Trip route string in format 'mode1(time1) -> mode2(time2) -> ...'
              Example: 'walking(5분) -> bus(15분) -> walking(3분) -> subway(20분) -> walking(2분)'
        
    Returns:
        Simplified trip route string with merged modes and reduced walking segments
        Example: 'walking(5분) -> bus(15분) -> subway(20분) -> walking(2분)'
        
    Note:
        The function uses regex to parse segments in the format 'mode(time)'
        and processes them sequentially to apply the simplification rules.
    """
    # Extract all segments matching pattern: mode(time)
    segments = re.findall(r'(\w+\(\d+\.?\d*[^\)]+\))', trip)
    processed_segments = []
    total_time = 0
    current_mode = None
    
    for i, segment in enumerate(segments):
        match = re.match(r'(\w+)\((.+)\)', segment)
        if not match:
            logger.warning(f"Could not parse segment: {segment}")
            continue
            
        mode, time = match.groups()

        # Handle walking: absorb intermediate, keep first and last
        if mode == "walking":
            if i == 0 or i == len(segments) - 1:  # Keep first and last walking
                # Save accumulated time for previous mode if exists
                if current_mode:
                    processed_segments.append(
                        f"{current_mode}({convert_minutes_to_time(total_time)})"
                    )
                # Add the walking segment
                processed_segments.append(segment)
                current_mode = None
                total_time = 0
            else:
                # Absorb walking into the previous mode (add to total time)
                total_time += convert_time_to_minutes(time)
            continue

        # Accumulate time for the same mode
        if mode == current_mode:
            total_time += convert_time_to_minutes(time)
        else:
            # Save previous mode if exists
            if current_mode:
                processed_segments.append(
                    f"{current_mode}({convert_minutes_to_time(total_time)})"
                )
            # Start new mode
            current_mode = mode
            total_time = convert_time_to_minutes(time)

    # Append the last accumulated mode
    if current_mode:
        processed_segments.append(
            f"{current_mode}({convert_minutes_to_time(total_time)})"
        )

    return " -> ".join(processed_segments)


def main():
    """
    Main function to process trip data and generate simplified routes.
    
    Reads trip2.csv, applies simplification to routes, and saves results to trip3.csv.
    """
    logger.info(f"Reading input file: {TRIP2_CSV}")
    
    # Check if input file exists
    if not TRIP2_CSV.exists():
        raise FileNotFoundError(
            f"Input file not found: {TRIP2_CSV}\n"
            "Please ensure stage 2 (2_raw_trip.py) has been run successfully."
        )
    
    # Read the input data
    try:
        data = pd.read_csv(TRIP2_CSV)
        logger.info(f"Loaded {len(data)} trip records")
    except Exception as e:
        logger.error(f"Error reading input file: {e}")
        raise
    
    # Check required columns
    required_columns = ['Optimized Route']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        raise ValueError(
            f"Missing required columns in input file: {missing_columns}\n"
            f"Available columns: {list(data.columns)}"
        )
    
    # Apply the simplification function
    logger.info("Simplifying trip routes...")
    data['Total Trip'] = data['Optimized Route'].apply(simplify_trip)
    
    # Ensure output directory exists
    ensure_directory(TRIP3_CSV)
    
    # Save the modified dataset
    logger.info(f"Saving output to: {TRIP3_CSV}")
    try:
        data.to_csv(TRIP3_CSV, index=False)
        logger.info(f"Successfully saved {len(data)} simplified trip records")
    except Exception as e:
        logger.error(f"Error saving output file: {e}")
        raise


if __name__ == "__main__":
    main()
