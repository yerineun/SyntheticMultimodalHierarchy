"""
Configuration module for transit route analysis project.

This module centralizes all file paths, constants, and configuration settings
to improve maintainability and portability across different environments.
"""

import os
from pathlib import Path

# Try to load environment variables from .env file if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, using environment variables only
    pass

# ============================================================================
# Environment Variables
# ============================================================================

# Google Maps API Key (should be set in .env file)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# ============================================================================
# Base Directory Paths
# ============================================================================

# Base directory for all data (configurable via environment variable)
# Defaults to current working directory if not set
BASE_DATA_DIR = Path(os.getenv("BASE_DATA_DIR", "."))

# Subdirectories for organization
PRE_DIR = BASE_DATA_DIR / os.getenv("PRE_DIR", "pre")
RESULT_DIR = BASE_DATA_DIR / os.getenv("RESULT_DIR", "result")
RESULT_POPULATION_DIR = BASE_DATA_DIR / os.getenv("RESULT_POPULATION_DIR", "result2_population_base")
RESULT_AREA_DIR = BASE_DATA_DIR / os.getenv("RESULT_AREA_DIR", "result3_area_base")

# ============================================================================
# Input File Paths
# ============================================================================

# City district boundary file (GeoJSON)
CITY_GEOJSON_FILE = PRE_DIR / os.getenv("CITY_GEOJSON_FILE", "Amsterdam.geojson")

# Random points file (GeoJSON)
RANDOM_POINTS_GEOJSON = RESULT_DIR / os.getenv("RANDOM_POINTS_GEOJSON", "random_points.geojson")

# Random points file (CSV)
RANDOM_POINTS_CSV = RESULT_DIR / os.getenv("RANDOM_POINTS_CSV", "random_points.csv")

# Random points with districts (GeoJSON)
RANDOM_POINTS_WITH_DISTRICTS_GEOJSON = RESULT_DIR / os.getenv(
    "RANDOM_POINTS_WITH_DISTRICTS_GEOJSON", "random_points_with_districts.geojson"
)

# Population product combinations file
POPULATION_PRODUCT_COMBINATIONS_CSV = RESULT_DIR / os.getenv(
    "POPULATION_PRODUCT_COMBINATIONS_CSV", "population_product_combinations.csv"
)

# Area product combinations file
AREA_PRODUCT_COMBINATIONS_CSV = RESULT_DIR / os.getenv(
    "AREA_PRODUCT_COMBINATIONS_CSV", "area_product_combinations.csv"
)

# Origin-destination pairs file
RANDOM_OD_PAIRS_CSV = BASE_DATA_DIR / os.getenv("RANDOM_OD_PAIRS_CSV", "random_od_pairs.csv")

# ============================================================================
# Output File Paths (Pipeline Stages)
# ============================================================================

# Stage 2: Raw trip data (distance, optimized route)
TRIP2_CSV = BASE_DATA_DIR / os.getenv("TRIP2_CSV", "trip2.csv")

# Stage 3: Simplified trip (walking merged)
TRIP3_CSV = BASE_DATA_DIR / os.getenv("TRIP3_CSV", "trip3.csv")

# Stage 4: Ascending/descending split
TRIP4_CSV = BASE_DATA_DIR / os.getenv("TRIP4_CSV", "trip4.csv")

# Stage 5: Final transfer counting results
FINAL_CSV = BASE_DATA_DIR / os.getenv("FINAL_CSV", "final.csv")

# Alternative OD pair files (for different analysis bases)
OD_PAIRS_POPULATION_CSV = RESULT_POPULATION_DIR / os.getenv(
    "OD_PAIRS_POPULATION_CSV", "random_od_pairs.csv"
)
OD_PAIRS_AREA_CSV = RESULT_AREA_DIR / os.getenv("OD_PAIRS_AREA_CSV", "random_od_pairs.csv")

# ============================================================================
# Processing Constants
# ============================================================================

# Number of random points to generate
NUM_RANDOM_POINTS = int(os.getenv("NUM_RANDOM_POINTS", "10000"))

# Population product scaling factor
POPULATION_SCALING_FACTOR = float(os.getenv("POPULATION_SCALING_FACTOR", "0.000000014"))

# Area product scaling factor
AREA_SCALING_FACTOR = float(os.getenv("AREA_SCALING_FACTOR", "0.94"))

# Coordinate Reference System (CRS) for latitude/longitude
WGS84_EPSG = int(os.getenv("WGS84_EPSG", "4326"))

# Earth radius in kilometers (for Haversine distance calculation)
EARTH_RADIUS_KM = float(os.getenv("EARTH_RADIUS_KM", "6371.0"))

# Departure time hour (24-hour format, for transit route queries)
DEPARTURE_HOUR = int(os.getenv("DEPARTURE_HOUR", "12"))

# ============================================================================
# Google Maps API Configuration
# ============================================================================

# API Base URLs
GOOGLE_TIMEZONE_API_URL = "https://maps.googleapis.com/maps/api/timezone/json"
GOOGLE_DIRECTIONS_API_URL = "https://maps.googleapis.com/maps/api/directions/json"

# API Request Parameters
TRANSIT_MODE = "transit"
LANGUAGE = "ko"
REGION = "KR"

# ============================================================================
# CSV Column Names
# ============================================================================

# Input CSV columns for OD pairs
OD_COLUMNS = ["origin_lat", "origin_lon", "destination_lat", "destination_lon"]

# Output CSV columns
TRIP2_COLUMNS = ["Origin", "Destination", "distance_km", "Optimized Route"]
TRIP3_COLUMNS = ["Origin", "Destination", "distance_km", "Optimized Route", "Total Trip"]
TRIP4_COLUMNS = ["Ascending", "Descending"]
FINAL_COLUMNS = ["Transition", "Count", "Type"]

# ============================================================================
# Helper Functions
# ============================================================================


def ensure_directory(path: Path) -> Path:
    """
    Ensure that the directory for the given path exists.
    
    Args:
        path: File path (Path object)
        
    Returns:
        The path object (for chaining)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_api_key() -> str:
    """
    Get Google Maps API key from environment variable.
    
    Returns:
        API key string
        
    Raises:
        ValueError: If API key is not set
    """
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError(
            "GOOGLE_MAPS_API_KEY not set. Please set it in your .env file or environment."
        )
    return GOOGLE_MAPS_API_KEY


# ============================================================================
# Validation
# ============================================================================

# Validate that critical directories exist or can be created
for directory in [PRE_DIR, RESULT_DIR, RESULT_POPULATION_DIR, RESULT_AREA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
