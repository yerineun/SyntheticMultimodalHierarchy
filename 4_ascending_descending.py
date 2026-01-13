"""
Script 4: Ascending/Descending Route Split

This script processes simplified trip data from stage 3 and splits each route
into ascending and descending segments based on the midpoint of total trip duration.
The route is divided at the 50% time point, with segments split if necessary.

Input: trip3.csv (from stage 3, must contain 'Total Trip' column)
Output: trip4.csv (with 'Ascending' and 'Descending' columns)
"""

import re
import pandas as pd
import logging
from pathlib import Path

from config import TRIP3_CSV, TRIP4_CSV, ensure_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_duration_to_minutes(duration_str: str) -> float:
    """
    Convert Korean time string format to total minutes as float.
    
    Parses time strings in Korean format (e.g., "1시간 30분", "45분", "2시간")
    and converts them to total minutes as a float value.
    
    Args:
        duration_str: Time string in Korean format
        
    Returns:
        Total minutes as float
        
    Examples:
        >>> parse_duration_to_minutes("1시간 30분")
        90.0
        >>> parse_duration_to_minutes("45분")
        45.0
        >>> parse_duration_to_minutes("2시간")
        120.0
    """
    hours_pattern = re.search(r'(\d+)\s*시간', duration_str)
    mins_pattern = re.search(r'(\d+)\s*분', duration_str)

    hours = float(hours_pattern.group(1)) if hours_pattern else 0.0
    mins = float(mins_pattern.group(1)) if mins_pattern else 0.0

    return hours * 60.0 + mins


def format_minutes_to_string(minutes: float) -> str:
    """
    Convert float minutes to Korean time string format.
    
    Converts a float number of minutes back to Korean time format,
    showing hours and/or minutes as appropriate. Supports decimal minutes.
    
    Args:
        minutes: Total minutes as float (can include decimals)
        
    Returns:
        Time string in Korean format (e.g., "1시간 30분", "45분", "2.5분")
        
    Examples:
        >>> format_minutes_to_string(90.0)
        "1시간 30분"
        >>> format_minutes_to_string(45.0)
        "45분"
        >>> format_minutes_to_string(2.5)
        "2.5분"
    """
    # Calculate hours and remaining minutes (minutes can be decimal)
    h = int(minutes // 60)
    m = minutes % 60  # Remaining minutes (can be decimal)

    # Format based on whether we have hours and/or minutes
    if h > 0 and m > 0:
        # If decimal minutes exist, they will be displayed as-is
        return f"{h}시간 {m}분"
    elif h > 0:
        return f"{h}시간"
    else:
        return f"{m}분"  # Example: "2.5분"


def split_route_in_half(route_str: str) -> tuple[str, str]:
    """
    Split a route string into ascending and descending segments at the midpoint.
    
    Divides a transit route string at the 50% time point. If a segment spans
    the midpoint, it is split proportionally between ascending and descending.
    
    Args:
        route_str: Route string in format "mode1(time1) -> mode2(time2) -> ..."
                  Example: "walking(7분) -> subway(6분) -> walking(6분)"
        
    Returns:
        Tuple of (ascending_str, descending_str) where:
        - ascending_str: Route segments up to the midpoint
        - descending_str: Route segments after the midpoint (or "N/A" if empty)
        
    Note:
        The function calculates total trip duration, finds the midpoint,
        and distributes segments accordingly. Segments crossing the midpoint
        are split proportionally.
    """
    # Split route by "->" delimiter to get individual steps
    raw_steps = [s.strip() for s in route_str.split("->") if s.strip()]

    # Store each step with its duration in minutes (as float)
    steps_with_minutes = []
    total_minutes = 0.0

    for step in raw_steps:
        # Parse duration from parentheses. Example: "walking(7분)" -> "7분"
        match = re.search(r"\(([^)]+)\)", step)
        if match:
            duration_str = match.group(1)  # Example: "7분"
            dur_min = parse_duration_to_minutes(duration_str)
        else:
            dur_min = 0.0  # If no time info, treat as 0 minutes

        steps_with_minutes.append((step, dur_min))
        total_minutes += dur_min

    # Calculate midpoint (can be decimal)
    half_time = total_minutes / 2.0

    ascending, descending = [], []
    accumulated = 0.0
    half_reached = False

    for i, (step_text, dur_min) in enumerate(steps_with_minutes):
        if half_reached:
            # Already past midpoint, add all remaining steps to descending
            descending.append((step_text, dur_min))
            continue

        if accumulated + dur_min < half_time:
            # Not yet at midpoint, add entire step to ascending
            ascending.append((step_text, dur_min))
            accumulated += dur_min
        elif abs(accumulated + dur_min - half_time) < 1e-9:
            # Exactly at midpoint
            ascending.append((step_text, dur_min))
            accumulated += dur_min
            half_reached = True
        else:
            # Step crosses midpoint → need to split this step
            # Add remaining portion to ascending, rest to descending
            remain_to_half = half_time - accumulated  # Example: 2.5
            if remain_to_half < 0:
                # Already exceeded half_time, add all to descending
                descending.append((step_text, dur_min))
            else:
                # Split the step proportionally
                ascending_part = remain_to_half
                descending_part = dur_min - remain_to_half

                # Extract base mode name from step_text
                # Example: "walking(7분)" -> "walking"
                base_name = step_text.split("(")[0].strip()

                # Create new step strings for ascending and descending portions
                ascend_text = f"{base_name}({format_minutes_to_string(ascending_part)})"
                descend_text = f"{base_name}({format_minutes_to_string(descending_part)})"

                ascending.append((ascend_text, ascending_part))
                if descending_part > 0:
                    descending.append((descend_text, descending_part))

            # Mark that we've reached the midpoint
            half_reached = True

    # Reconstruct ascending route string
    ascending_str = " -> ".join(
        f"{stp[0]}" for stp in ascending
    )
    # Reconstruct descending route string
    descending_str = " -> ".join(
        f"{stp[0]}" for stp in descending
    ) if descending else "N/A"

    return ascending_str, descending_str


def main():
    """
    Main function to process trip data and split routes into ascending/descending segments.
    
    Reads trip3.csv, splits each route at the midpoint, and saves results to trip4.csv.
    """
    logger.info(f"Reading input file: {TRIP3_CSV}")
    
    # Check if input file exists
    if not TRIP3_CSV.exists():
        raise FileNotFoundError(
            f"Input file not found: {TRIP3_CSV}\n"
            "Please ensure stage 3 (3_simplified_trip.py) has been run successfully."
        )
    
    # Read the input data
    try:
        data = pd.read_csv(TRIP3_CSV)
        logger.info(f"Loaded {len(data)} trip records")
    except Exception as e:
        logger.error(f"Error reading input file: {e}")
        raise
    
    # Check required columns
    required_columns = ['Total Trip']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        raise ValueError(
            f"Missing required columns in input file: {missing_columns}\n"
            f"Available columns: {list(data.columns)}"
        )
    
    # Initialize result columns
    logger.info("Splitting routes into ascending and descending segments...")
    data["Ascending"] = ""
    data["Descending"] = ""
    
    # Process each row
    for i, row in data.iterrows():
        route_str = row["Total Trip"]
        
        ascending_str, descending_str = split_route_in_half(route_str)
        
        # Record results in DataFrame
        data.at[i, "Ascending"] = ascending_str
        data.at[i, "Descending"] = descending_str
        
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{len(data)} records")
    
    logger.info(f"Completed processing {len(data)} records")
    
    # Display sample results
    logger.info("Sample results:")
    logger.info(f"\n{data[['Total Trip', 'Ascending', 'Descending']].head()}")
    
    # Extract only Ascending and Descending columns for output
    required_columns = ["Ascending", "Descending"]
    filtered_data = data[required_columns]
    
    # Ensure output directory exists
    ensure_directory(TRIP4_CSV)
    
    # Save the results
    logger.info(f"Saving output to: {TRIP4_CSV}")
    try:
        filtered_data.to_csv(TRIP4_CSV, index=False)
        logger.info(f"Successfully saved {len(filtered_data)} records to {TRIP4_CSV}")
    except Exception as e:
        logger.error(f"Error saving output file: {e}")
        raise


if __name__ == "__main__":
    main()
