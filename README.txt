================================================================================
SAMPLEAD PROSPECT MATCHER PROJECT
================================================================================

PROJECT OVERVIEW
----------------
A python prospect-to-user matching system that matches prospects with users based on location 
preferences. The system supports complex location conventions including countries,
regions (EMEA, APAC, North America, etc.), and US state-level conventions.


SYSTEM ARCHITECTURE
--------------------
The project consists of 4 main components:

1. MAIN APPLICATION (src/main.py)
   - Entry point for the application
   - Orchestrates the matching workflow
   - Handles command-line arguments and logging
   - Manages database connections

2. PROSPECT MATCHER (src/prospect_matcher.py)
   - Core business logic for prospect-user matching
   - Creates user-location preference matrix
   - Implements matching algorithm:
     - For US prospects: matches on state-level if specified
     - For other countries: matches on country-level
   - Handles region expansions ("EMEA" -> all EMEA countries)
   - Resolves include/exclude conflicts (exclude takes priority)

3. DATABASE HANDLER (src/db_handler.py)
   - PostgreSQL connection management using SQLAlchemy
   - Upsert functionality for prospects_users_matches table
   - Connection pooling and resource cleanup

4. POSTGRESQL DATABASE
   - Stores users, prospects, and matching results
   - Schema includes:
     * users: User account information
     * prospects: Company/prospect data with location
     * prospects_users_matches: Matched user-prospect pairs
   - Runs in Docker container


DATA FILES
----------
data/country-to-regions-mapping.json (OR user-provided)
  - Maps location codes (countries/states) to region groupings
  - Example: "DE": ["Europe", "EMEA", "DACH"]
  - Supports hierarchical locations

data/users-locations-settings.json (OR user-provided)
  - User-specific location preferences
  - Format: {user_id: {location_include: [], location_exclude: []}}
  - Supports: specific countries, regions, "All", US states
  - Example: {"location_include": ["EMEA"], "location_exclude": ["FR"]}

data/prospects.csv (user-provided)
  - Input file containing prospects to be matched
  - Required columns:
    - user_id: UUID of the user (used as a filter/context)
    - prospect_id: Unique prospect identifier
    - company_country: 2-letter country code
    - company_state: 2-letter state code (for US only)


DATABASE SCHEMA
---------------
Table: users
  - id (UUID, primary key)
  - username, email, password_hash
  - created_at, updated_at

Table: prospects  
  - id (UUID, primary key)
  - name, description
  - company_country (VARCHAR(2))
  - company_state (VARCHAR(2), nullable)
  - created_at, updated_at

Table: prospects_users_matches
  - id (UUID, primary key)
  - user_id (UUID, references users)
  - prospect_id (UUID, references prospects)
  - company_country (VARCHAR(2))
  - company_state (VARCHAR(2), nullable)
  - created_at
  - UNIQUE constraint on (user_id, prospect_id)
  - Indexes on: user_id, prospect_id, company_country


SETUP INSTRUCTIONS
------------------

PREREQUISITES:
  - Python 3.10+ installed
  - Docker installed (for PostgreSQL)
  - pip package manager

STEP 1: Install Python Dependencies
  $ pip install -r requirements.txt

STEP 2: Set Up PostgreSQL Database
  # Build the Docker image
  $ docker build -t samplead-postgres .
  
  # Run the PostgreSQL container
  $ docker run -d \
      --name samplead_postgres_container \
      -p 5432:5432 \
      -v postgres_data:/var/lib/postgresql/data \
      -e POSTGRES_PASSWORD=dbpassword \
      samplead-postgres
  
  # verify container is running
  $ docker ps
  
  # check logs
  $ docker logs samplead_postgres_container

STEP 3: Configure Environment Variables
  The application uses these environment variables (with defaults):
  
  export POSTGRES_USER=dbuser
  export POSTGRES_PASSWORD=dbpassword
  export DB_HOST=localhost
  export DB_PORT=5432
  export POSTGRES_DB=samplead_db

STEP 4: Prepare Your Prospects Data
  Create a CSV file with the following columns:
  - user_id
  - prospect_id  
  - company_country
  - company_state (optional for non-US)
  
  Example: data/prospects.csv


RUNNING THE APPLICATION
------------------------

BASIC USAGE EXAMPLE:
  $ python src/main.py -p data/prospects.csv

FULL USAGE WITH ALL OPTIONS EXAMPLE:
  $ python src/main.py \
      --prospects-path data/prospects.csv \
      --country-regions-map-path data/country-to-regions-mapping.json \
      --users-locations-settings-path data/users-locations-settings.json

COMMAND-LINE ARGUMENTS:
  -p, --prospects-path (REQUIRED)
      Path to the CSV file containing prospects to match
      
  -c, --country-regions-map-path (Optional, default: data/country-to-regions-mapping.json)
      Path to the country-to-regions mapping JSON file
      
  -u, --users-locations-settings-path (Optional, default: data/users-locations-settings.json)
      Path to the users location settings JSON file


OUTPUT AND LOGGING
------------------
The application logs to both:
  1. Console (stdout)- for real-time monitoring
  2. File: samplead-excersize.log- for persistent logs



MATCHING ALGORITHM DETAILS
---------------------------

1. INITIALIZATION:
   - Load country-to-regions mapping
   - Load user location preferences
   - Create reverse mapping (region -> countries)
   - Build user-location matrix (users x locations)

2. MATRIX CREATION:
   For each user:
     a. Start with all locations as False (not included)
     b. Process location_include list:
        - "All"-> include all locations
        - Region name-> include all countries in that region
        - Country code-> include that country
        - State code (US-XX)-> include that state
     c. Process location_exclude list
     d. Resolve conflicts: exclude overrides include

3. PROSPECT MATCHING:
   For each prospect:
     a. Check if prospect's user_id exists in settings
     b. If company_country == "US":
        - Match on company_state (if provided)
     c. Else:
        - Match on company_country
     d. Look up in user-location matrix
     e. If True -> add to matches

4. DATABASE UPSERT:
   - Insert matched prospects into prospects_users_matches table
   - Use ON CONFLICT to handle duplicates (update timestamp)



PERFORMANCE CONSIDERATIONS
---------------------------
- Uses pandas DataFrames for efficient bulk operations
- Pre-builds user-location matrix (one-time cost per run)
- Batch database upserts instead of row-by-row inserts
- Indexes on database for faster queries
- Connection pooling via SQLAlchemy



