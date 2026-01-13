"""
Script 5: Transfer Counting

This script analyzes transit route transitions from stage 4 data. It extracts and counts
mode transitions (e.g., "walking -> subway", "subway -> bus") separately for ascending
and descending route segments. The results are combined into a single output file showing
transition frequencies for both route types.

Input: trip4.csv (from stage 4, must contain 'Ascending' and 'Descending' columns)
Output: final.csv (with 'Transition', 'Count', and 'Type' columns)
"""

import pandas as pd
from collections import Counter
import re
import logging
from pathlib import Path

from config import TRIP4_CSV, FINAL_CSV, ensure_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_transitions(column_data: pd.Series) -> Counter:
    """
    Extract and count mode transitions from a route column.
    
    Parses route strings in the format "mode1(time1) -> mode2(time2) -> ..."
    and counts all transitions between consecutive transportation modes.
    
    Args:
        column_data: Pandas Series containing route strings with mode transitions
        
    Returns:
        Counter object mapping transition strings (e.g., "walking -> subway") to counts
        
    Examples:
        >>> routes = pd.Series(["walking(5분) -> subway(10분) -> walking(3분)"])
        >>> counts = extract_transitions(routes)
        >>> counts["walking -> subway"]
        1
        >>> counts["subway -> walking"]
        1
    """
    transition_counts = Counter()
    
    # Process each route string, skipping NaN values
    for row in column_data.dropna():
        # Extract transportation modes using regex
        # Pattern matches: word characters followed by parentheses with any content
        # Example: "walking(5분)" -> "walking", "subway(10분)" -> "subway"
        modes = re.findall(r'(\w+)\(\d+.*?\)', row)
        
        # Count transitions between consecutive modes
        for i in range(len(modes) - 1):
            transition = f"{modes[i]} -> {modes[i+1]}"
            transition_counts[transition] += 1

    return transition_counts


def process_transitions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process ascending and descending transitions and combine into a single DataFrame.
    
    Extracts transitions from both 'Ascending' and 'Descending' columns, counts them,
    and combines the results with a 'Type' column to distinguish the route segment.
    
    Args:
        df: DataFrame containing 'Ascending' and 'Descending' columns with route strings
        
    Returns:
        DataFrame with columns: ['Transition', 'Count', 'Type']
        - Transition: Mode transition string (e.g., "walking -> subway")
        - Count: Number of times this transition occurred
        - Type: Either "Ascending" or "Descending"
        
    Raises:
        ValueError: If required columns are missing from the input DataFrame
    """
    # Check required columns
    required_columns = ['Ascending', 'Descending']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"Missing required columns in input file: {missing_columns}\n"
            f"Available columns: {list(df.columns)}"
        )
    
    logger.info("Extracting transitions from ascending routes...")
    ascending_transitions = extract_transitions(df["Ascending"])
    logger.info(f"Found {len(ascending_transitions)} unique ascending transitions")
    
    logger.info("Extracting transitions from descending routes...")
    descending_transitions = extract_transitions(df["Descending"])
    logger.info(f"Found {len(descending_transitions)} unique descending transitions")
    
    # Convert Counter objects to DataFrames for better visualization
    ascending_df = pd.DataFrame(
        ascending_transitions.items(), 
        columns=["Transition", "Count"]
    ).sort_values(by="Count", ascending=False)
    
    descending_df = pd.DataFrame(
        descending_transitions.items(), 
        columns=["Transition", "Count"]
    ).sort_values(by="Count", ascending=False)
    
    # Add Type column to distinguish ascending vs descending
    ascending_df["Type"] = "Ascending"
    descending_df["Type"] = "Descending"
    
    # Combine both DataFrames into a single result
    combined_df = pd.concat([ascending_df, descending_df], ignore_index=True)
    
    logger.info(f"Total transitions found: {len(combined_df)}")
    logger.info(f"  - Ascending: {len(ascending_df)}")
    logger.info(f"  - Descending: {len(descending_df)}")
    
    return combined_df


def main():
    """
    Main function to process trip data and count mode transitions.
    
    Reads trip4.csv, extracts transitions from ascending and descending routes,
    and saves the combined results to final.csv.
    """
    logger.info(f"Reading input file: {TRIP4_CSV}")
    
    # Check if input file exists
    if not TRIP4_CSV.exists():
        raise FileNotFoundError(
            f"Input file not found: {TRIP4_CSV}\n"
            "Please ensure stage 4 (4_ascending_descending.py) has been run successfully."
        )
    
    # Read the input data
    try:
        df = pd.read_csv(TRIP4_CSV)
        logger.info(f"Loaded {len(df)} trip records")
    except Exception as e:
        logger.error(f"Error reading input file: {e}")
        raise
    
    # Process transitions
    combined_df = process_transitions(df)
    
    # Display top transitions
    logger.info("\nTop 10 transitions (all types):")
    top_transitions = combined_df.nlargest(10, 'Count')
    for _, row in top_transitions.iterrows():
        logger.info(f"  {row['Transition']}: {row['Count']} ({row['Type']})")
    
    # Ensure output directory exists
    ensure_directory(FINAL_CSV)
    
    # Save the results
    logger.info(f"\nSaving output to: {FINAL_CSV}")
    try:
        combined_df.to_csv(FINAL_CSV, index=False)
        logger.info(f"Successfully saved {len(combined_df)} transition records to {FINAL_CSV}")
    except Exception as e:
        logger.error(f"Error saving output file: {e}")
        raise


if __name__ == "__main__":
    main()
