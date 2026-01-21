# SMH (Synthetic Multimodal Hierarchy)

**Repository title:** SMH (Synthetic Multimodal Hierarchy)  
**Study title:** Identifying Public Transit Multimodal Hierarchy Using Artificially Generated Trip Chains

SMH provides the Phase 1 implementation for generating and pre-processing synthetic multimodal itineraries that feed a broader framework for quantifying urban transit hierarchies.

## Abstract

Establishing a clear hierarchical structure of public transit modes is fundamental to integrated urban planning and functional network analysis. Higher-tier modes exhibit lower spatial accessibility but greater mobility efficiency, enabling longer travel within fixed time budgets. Prior work in South Korea identified an “ascending–descending” travel pattern using empirical multimodal itineraries, yet many cities lack access to such granular data because of privacy and institutional constraints.

This study introduces a methodology to quantify macroscopic urban transit hierarchies using synthetic multimodal itineraries generated via the Google Maps Directions API. By segmenting itineraries into directional phases and analyzing intermodal transfers, we derive mode-specific hierarchy scores. Validation against Seoul smart card data shows simulated hierarchies (Walking < Local Bus < Urban Bus < Metro) align with observed behavior. Applications in Amsterdam and Brisbane demonstrate adaptability and scalability where empirical data are scarce.

## Methodology Overview

The research employs a two-stage pipeline that converts raw spatial data into quantified modal hierarchy scores, implemented across five primary scripts.

### Phase 1: Synthetic Itinerary Generation
- **Spatial-temporal sampling:** Construct origin–destination pairs.  
- **Data retrieval:** Extract multimodal routes via a public routing API (Google Maps Directions API).  
- **Repository scope:** This codebase delivers Phase 1 (data acquisition and pre-processing).

### Phase 2: Hierarchy Quantification
- **Temporal segmentation:** Bisect each trip into ascending and descending phases at the temporal midpoint.  
- **Transfer matrix construction:** Capture directional transitions between modes in each phase.  
- **Scoring:** Compute pairwise hierarchical differences and aggregate them into normalized scores in the \[0, 1\] range.

*For conceptual schematics and transfer logic, see Figures 1–3 in the manuscript.*

### Target cities and inputs
- **Pre-processing (common):** From GIS data (SHP/GeoJSON), remove parks, green areas, and waterways to retain only the serviceable area.  
- **Weights:** Population and land-use area.  
- **Tools:** Scripts 1–5 (this repository) plus the Google Maps Directions API.

### Seoul (deep dive, four scenarios)
- **S1 – Empirical / Empirical:** Empirical OD + empirical itineraries.  
- **S2 – Empirical / Artificial:** Empirical OD + API-generated itineraries.  
- **S3 – Artificial (Population) / Artificial:** Population-based synthetic OD + API itineraries.  
- **S4 – Artificial (Land Use) / Artificial:** Land-use-based synthetic OD + API itineraries.

### Amsterdam & Brisbane (case studies)
- **Input:** GIS plus population and land-use indicators.  
- **Process:** (1) Generate synthetic OD pairs; (2) collect API-based itineraries.  
- **Goal:** Demonstrate hierarchy analysis where only synthetic data are available.

## Repository Scope and Pipeline

This repository focuses on generating OD pairs and fetching, simplifying, and structuring itineraries; downstream hierarchy scoring is described in the paper but not implemented here.

1. **1_points_generation.ipynb** — Generate random points within districts and build OD pairs.  
2. **2_raw_trip.py** — Fetch multimodal routes via Google Maps Directions API for each OD pair.  
3. **3_simplified_trip.py** — Merge consecutive segments and simplify walking segments.  
4. **4_ascending_descending.py** — Split each trip into ascending and descending phases at the midpoint.  
5. **5_transfer_counting.py** — Count mode transitions separately for ascending and descending segments.

Primary outputs: `random_od_pairs.csv`, `trip2.csv`, `trip3.csv`, `trip4.csv`, `final.csv`.

## Installation and Setup

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
- Output: `walking(5분) -> bus(18분) -> subway(20분) -> walking(2분)`

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
│ Stage 1: Points Generation (1_points_generation.ipynb)          │
│                                                                 │
│ Input:  City district GeoJSON (pre/Amsterdam.geojson)           │
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

## Acknowledgments

- Google Maps Platform for transit route data
- GeoPandas and Shapely communities for geospatial tools
- OpenStreetMap for network analysis capabilities

## Notes and Cautions

- Keep API keys out of version control; `.gitignore` excludes sensitive files.  
- Large OD sets may require batching or reduced `NUM_RANDOM_POINTS`.  
- Figures referenced in the paper provide visual details for the hierarchy concept and transfer logic.
