# SMH (Synthetic Multimodal Hierarchy)

A Python-based transit route analysis system that processes city district data, generates origin-destination pairs, fetches transit routes via Google Maps API, and analyzes route transitions. The project creates a synthetic multimodal transportation hierarchy by analyzing transit patterns across city districts.

## Overview

This project processes city district boundaries to:
1. Generate random points within districts
2. Create origin-destination (OD) pairs based on population and area products
3. Fetch transit routes from Google Maps API
4. Simplify and analyze route transitions
5. Generate statistics on transportation mode transitions

The analysis produces insights into how people transition between different transportation modes (walking, subway, bus, etc.) during transit journeys, split into ascending (first half) and descending (second half) segments of trips.

## Features

- **Geospatial Processing**: Uses GeoPandas and Shapely for district boundary analysis
- **Google Maps Integration**: Fetches real transit routes via Google Maps Directions API
- **Route Simplification**: Merges consecutive segments and handles walking segments intelligently
- **Transition Analysis**: Counts mode transitions separately for ascending and descending route segments
- **Configurable**: Centralized configuration via `config.py` and environment variables
- **Portable**: No hardcoded paths, works across different operating systems

## Installation

### Prerequisites

- Python 3.8 or higher
- Google Maps API key with Directions API and Timezone API enabled

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd SMH
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Google Maps API key:
   ```
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

3. Optionally configure other settings (see [Configuration](#configuration) section)

### Step 4: Prepare Input Data

Place your city district GeoJSON file in the `pre/` directory. The file should contain:
- District boundaries as polygons
- A `layer` column with district names
- A `population` column with population values
- An `area` column with area values

Example structure:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "layer": "District Name",
        "population": 100000,
        "area": 50.5
      },
      "geometry": { ... }
    }
  ]
}
```

## Usage

The project follows a sequential pipeline. Run each script in order:

### Stage 1: Points Generation

Generate random points within city districts and create origin-destination pairs.

```bash
jupyter notebook 1_points_generation.ipynb
```

**What it does:**
- Generates random points within city district boundaries
- Calculates district combinations and their population/area products
- Creates OD pairs based on scaled products
- Outputs: `random_points.geojson`, `random_points.csv`, `random_od_pairs.csv`

**Configuration:**
- `NUM_RANDOM_POINTS`: Number of random points to generate (default: 10000)
- `POPULATION_SCALING_FACTOR`: Scaling factor for population products (default: 0.000000014)
- `AREA_SCALING_FACTOR`: Scaling factor for area products (default: 0.94)

### Stage 2: Raw Trip Processing

Fetch transit routes from Google Maps API for each OD pair.

```bash
python 2_raw_trip.py
```

**What it does:**
- Reads origin-destination pairs from `random_od_pairs.csv`
- Fetches transit routes via Google Maps Directions API
- Calculates Haversine distances between origin and destination
- Formats route information
- Outputs: `trip2.csv` with columns: `Origin`, `Destination`, `distance_km`, `Optimized Route`

**Note:** This stage makes API calls to Google Maps. Processing time depends on the number of OD pairs and API rate limits.

### Stage 3: Simplified Trip Processing

Simplify routes by merging consecutive segments and handling walking segments.

```bash
python 3_simplified_trip.py
```

**What it does:**
- Reads `trip2.csv`
- Merges consecutive segments of the same transit mode
- Absorbs intermediate walking segments into adjacent transit modes
- Preserves only first and last walking segments
- Outputs: `trip3.csv` with an additional `Total Trip` column

**Example transformation:**
- Input: `walking(5분) -> bus(15분) -> walking(3분) -> subway(20분) -> walking(2분)`
- Output: `walking(5분) -> bus(15분) -> subway(20분) -> walking(2분)`

### Stage 4: Ascending/Descending Split

Split each route at the midpoint into ascending and descending segments.

```bash
python 4_ascending_descending.py
```

**What it does:**
- Reads `trip3.csv`
- Splits each route at the 50% time point
- Handles segments that cross the midpoint by splitting them proportionally
- Outputs: `trip4.csv` with `Ascending` and `Descending` columns

**Example:**
- Total Trip: `walking(7분) -> subway(6분) -> walking(6분)` (19 minutes total)
- Ascending: `walking(7분) -> subway(2.5분)` (first 9.5 minutes)
- Descending: `subway(3.5분) -> walking(6분)` (remaining 9.5 minutes)

### Stage 5: Transfer Counting

Count mode transitions in ascending and descending segments.

```bash
python 5_transfer_counting.py
```

**What it does:**
- Reads `trip4.csv`
- Extracts mode transitions (e.g., "walking -> subway", "subway -> bus")
- Counts transitions separately for ascending and descending segments
- Outputs: `final.csv` with columns: `Transition`, `Count`, `Type`

**Example output:**
```
Transition,Count,Type
walking -> subway,150,Ascending
subway -> walking,120,Descending
bus -> subway,85,Ascending
...
```

## Configuration

Configuration is managed through `config.py` and environment variables. Key settings:

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Required
GOOGLE_MAPS_API_KEY=your_api_key_here

# Optional - Directory paths (defaults shown)
BASE_DATA_DIR=.
PRE_DIR=pre
RESULT_DIR=result
RESULT_POPULATION_DIR=result2_population_base
RESULT_AREA_DIR=result3_area_base

# Optional - File names (defaults shown)
CITY_GEOJSON_FILE=Amsterdam.geojson
RANDOM_OD_PAIRS_CSV=random_od_pairs.csv
TRIP2_CSV=trip2.csv
TRIP3_CSV=trip3.csv
TRIP4_CSV=trip4.csv
FINAL_CSV=final.csv

# Optional - Processing constants
NUM_RANDOM_POINTS=10000
POPULATION_SCALING_FACTOR=0.000000014
AREA_SCALING_FACTOR=0.94
DEPARTURE_HOUR=12
```

### Direct Configuration

You can also modify `config.py` directly, but using environment variables is recommended for portability.

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: Points Generation (1_points_generation.ipynb)         │
│                                                                 │
│ Input:  City district GeoJSON (pre/Amsterdam.geojson)          │
│ Output: Random points, OD pairs                                 │
│         - random_points.geojson                                 │
│         - random_points.csv                                     │
│         - random_od_pairs.csv                                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2: Raw Trip Processing (2_raw_trip.py)                    │
│                                                                 │
│ Input:  random_od_pairs.csv                                     │
│ Output: trip2.csv                                               │
│         - Origin, Destination, distance_km, Optimized Route     │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3: Simplified Trip (3_simplified_trip.py)                 │
│                                                                 │
│ Input:  trip2.csv                                               │
│ Output: trip3.csv                                               │
│         - Adds: Total Trip (simplified route)                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 4: Ascending/Descending Split (4_ascending_descending.py) │
│                                                                 │
│ Input:  trip3.csv                                               │
│ Output: trip4.csv                                               │
│         - Ascending, Descending                                 │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 5: Transfer Counting (5_transfer_counting.py)             │
│                                                                 │
│ Input:  trip4.csv                                               │
│ Output: final.csv                                               │
│         - Transition, Count, Type                               │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
SMH/
├── README.md                          # This file
├── requirements.txt                    # Python dependencies
├── config.py                          # Centralized configuration
├── .env.example                       # Environment variable template
├── .gitignore                         # Git ignore rules
│
├── 1_points_generation.ipynb          # Stage 1: Generate points and OD pairs
├── 2_raw_trip.py                      # Stage 2: Fetch transit routes
├── 3_simplified_trip.py               # Stage 3: Simplify routes
├── 4_ascending_descending.py           # Stage 4: Split routes
└── 5_transfer_counting.py             # Stage 5: Count transitions
│
├── pre/                               # Input data directory
│   └── Amsterdam.geojson              # City district boundaries (example)
│
├── result/                            # Intermediate results
│   ├── random_points.geojson
│   ├── random_points.csv
│   ├── population_product_combinations.csv
│   └── area_product_combinations.csv
│
├── result2_population_base/           # Population-based OD pairs
│   └── random_od_pairs.csv
│
├── result3_area_base/                 # Area-based OD pairs
│   └── random_od_pairs.csv
│
└── [Output files in root]            # Pipeline stage outputs
    ├── random_od_pairs.csv            # Main OD pairs file
    ├── trip2.csv                      # Raw trip data
    ├── trip3.csv                      # Simplified trips
    ├── trip4.csv                      # Split routes
    └── final.csv                      # Final transition counts
```

## Dependencies

- **pandas** (≥2.0.0): Data manipulation and analysis
- **geopandas** (≥0.14.0): Geospatial data processing
- **shapely** (≥2.0.0): Geometric operations
- **osmnx** (≥1.6.0): OpenStreetMap network analysis
- **matplotlib** (≥3.7.0): Visualization
- **requests** (≥2.31.0): HTTP requests for Google Maps API
- **python-dotenv** (≥1.0.0): Environment variable management

## API Requirements

This project requires a Google Maps API key with the following APIs enabled:
- **Directions API**: For fetching transit routes
- **Timezone API**: For determining local departure times

**Important:** Keep your API key secure. Never commit `.env` files to version control. The `.gitignore` file is configured to exclude sensitive files.

## Troubleshooting

### API Key Issues

**Error:** `GOOGLE_MAPS_API_KEY not set`
- **Solution:** Ensure your `.env` file exists and contains `GOOGLE_MAPS_API_KEY=your_key_here`

**Error:** `Directions API Error: REQUEST_DENIED`
- **Solution:** Check that your API key has Directions API enabled and billing is set up

### File Not Found Errors

**Error:** `Input file not found`
- **Solution:** Ensure you've run previous pipeline stages in order. Each stage depends on the output of the previous stage.

### Memory Issues

If processing large numbers of OD pairs:
- Process in batches by modifying the scripts
- Increase system memory
- Use a smaller `NUM_RANDOM_POINTS` value

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Specify your license here]

## Acknowledgments

- Google Maps Platform for transit route data
- GeoPandas and Shapely communities for geospatial tools
- OpenStreetMap for network analysis capabilities

## Contact

[Add contact information or project maintainer details]
