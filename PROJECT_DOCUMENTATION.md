# GraphRAG Stock Market Knowledge Graph - Complete Project Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Directory Structure](#directory-structure)
4. [File Descriptions](#file-descriptions)
5. [Data Pipeline](#data-pipeline)
6. [Neo4j Graph Schema](#neo4j-graph-schema)
7. [Graph Data Science (GDS)](#graph-data-science-gds)
8. [GraphRAG Implementation](#graphrag-implementation)
9. [Containerization](#containerization)
10. [API Endpoints](#api-endpoints)
11. [Frontend](#frontend)
12. [Ontology & RDF Integration](#ontology--rdf-integration)
13. [Setup & Installation](#setup--installation)
14. [Usage Guide](#usage-guide)
15. [What's Next](#whats-next)

---

## Project Overview

This project is a **Graph Retrieval-Augmented Generation (GraphRAG)** system for stock market data analysis. It combines:

- **Neo4j Graph Database**: Stores stock price data as a knowledge graph
- **Graph Data Science (GDS)**: Provides network analytics (similarity, centrality, community detection)
- **OpenAI LLM**: Generates Cypher queries from natural language and synthesizes answers
- **FastAPI Backend**: RESTful API for the chatbot
- **Web Frontend**: Interactive chat interface
- **PostgreSQL**: Relational database for raw data storage
- **RDF/OWL Ontology**: Semantic layer using n10s plugin
- **Ontop VKG**: Virtual Knowledge Graph for SPARQL queries over PostgreSQL

### Key Features
- Natural language queries about stock prices
- Graph-based analytics (correlations, similarities, communities)
- Schema-safe Cypher generation (prevents hallucination)
- Company name to ticker symbol mapping
- Context-aware follow-up questions
- Confidence scoring and query traces

---

## Architecture

```
┌─────────────────┐
│   Frontend      │  (HTML/CSS/JS)
│   (Chatbot UI)  │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│   FastAPI       │  (Python Backend)
│   /chat         │
└────────┬────────┘
         │
    ┌────┴────┐
    │        │
    ▼        ▼
┌────────┐ ┌──────────┐
│ Neo4j  │ │ OpenAI   │
│ Graph  │ │ LLM      │
│        │ │          │
│ - GDS  │ │ - Query  │
│ - n10s │ │   Gen    │
└────────┘ │ - Answer │
           │   Synth  │
           └──────────┘
                │
                ▼
         ┌──────────────┐
         │  PostgreSQL  │
         │  (Raw Data)  │
         └──────────────┘
```

### Data Flow
1. User asks question in natural language
2. Intent classifier determines if query needs database
3. LLM generates schema-safe Cypher query
4. Query executes on Neo4j
5. Results returned to LLM for natural language synthesis
6. Answer displayed to user with metadata (confidence, query trace)

---

## Directory Structure

```
kg_demo/
├── chatbot/
│   ├── backend/          # FastAPI backend + scripts
│   │   ├── app.py                    # Main FastAPI application
│   │   ├── graph.py                   # Neo4j connection & queries
│   │   ├── llm.py                     # OpenAI integration
│   │   ├── prompts.py                 # LLM prompt templates
│   │   ├── intent_classifier.py      # Intent classification
│   │   ├── gds_setup.py              # GDS algorithms setup
│   │   ├── gds_setup.cypher          # GDS Cypher scripts
│   │   ├── load_data_to_neo4j.py     # Data loader
│   │   ├── load_schema_extension.py  # Schema extension loader
│   │   ├── schema_extension.cypher   # Extended schema definition
│   │   ├── import_n10s_ontology.py   # n10s ontology import
│   │   ├── explore_n10s_ontology.py  # n10s exploration script
│   │   ├── explore_ontop.py         # Ontop exploration script
│   │   ├── test_gds_insights.py      # GDS testing script
│   │   ├── load_companies_to_neo4j.py # Companies metadata loader
│   │   ├── graph_visualization_queries.cypher # Neo4j visualization queries
│   │   ├── n10s_visualization_queries.cypher # n10s visualization queries
│   │   ├── install_gds_docker.sh     # GDS installation script
│   │   ├── install_n10s_docker.sh    # n10s installation script
│   │   ├── install_n10s_neo4j_5.18.sh # n10s for Neo4j 5.18
│   │   ├── start_ontop.sh            # Ontop startup script
│   │   ├── start_ontop_docker.sh     # Ontop Docker startup
│   │   ├── stock_ontology.ttl         # RDF/OWL ontology (n10s)
│   │   ├── stock_ontology_ontop.owl   # OWL ontology (Ontop)
│   │   ├── stock_mapping.obda         # OBDA mapping (Ontop)
│   │   ├── stock_ontop.properties    # Ontop properties file
│   │   ├── GDS_GRAPHRAG_USAGE.md     # GDS usage documentation
│   │   └── requirements.txt          # Python dependencies
│   └── frontend/          # Web UI
│       ├── index.html      # Main HTML page
│       ├── app.js          # Frontend JavaScript
│       └── style.css       # Styling
├── rawdata_cleanupscripts/
│   ├── download_prices_clean.py  # Data download script
│   └── stock_prices_pg.csv       # Clean CSV data (39,529 rows)
├── ontop/                  # Ontop tutorial (reference)
│   └── ontop-tutorial/     # Ontop examples (not used in production)
├── venv/                   # Python virtual environment
├── .env                    # Environment variables
└── PROJECT_DOCUMENTATION.md # This file
```

---

## File Descriptions

### Backend Core Files

#### `app.py`
**Purpose**: Main FastAPI application serving the chatbot API

**Key Features**:
- `/` - Health check endpoint
- `/chat` - Main chat endpoint (POST)
  - Accepts: `question`, `conversation_id`, `context`
  - Returns: `answer`, `confidence`, `query_trace`, `generated_query`, `processing_time`
- CORS middleware for frontend access
- In-memory conversation context cache
- Error handling and logging

**Dependencies**: `graph.py`, `llm.py`, `intent_classifier.py`, `prompts.py`

---

#### `graph.py`
**Purpose**: Neo4j database connection and query execution

**Key Functions**:
- `run_cypher(query, params, read_only)`: Execute Cypher queries with connection pooling
- `validate_schema_connection()`: Verify Neo4j connection and schema
- `close_driver()`: Cleanup connection

**Configuration**: Reads from `.env`:
- `NEO4J_URI`: bolt://localhost:7687
- `NEO4J_USER`: neo4j
- `NEO4J_PASSWORD`: test12345

**Optimizations**:
- Connection pooling (max 50 connections)
- Read/write transaction separation
- Error handling with detailed logging

---

#### `llm.py`
**Purpose**: OpenAI integration for Cypher generation and answer synthesis

**Key Functions**:
- `generate_cypher_query(question, schema_prompt, context)`: Generate schema-safe Cypher from natural language
- `explain(question, data, query)`: Synthesize natural language answers from query results
- `extract_symbol_from_question(question)`: Extract ticker symbols from questions
  - Handles: direct symbols (AAPL), company names (apple → AAPL)
  - Disambiguation: fruit "apple" vs Apple Inc.
  - Context-aware: uses stock keywords to disambiguate

**Features**:
- Query caching (LRU cache, max 100 entries)
- Schema validation before returning queries
- Parameter extraction ($symbol, $year, etc.)
- Company name mapping (apple → AAPL, microsoft → MSFT, etc.)

**Models Used**: `gpt-4o-mini` (cost-effective, fast)

---

#### `prompts.py`
**Purpose**: LLM prompt templates with schema safety enforcement

**Key Components**:
- `EXTENDED_GRAPH_SCHEMA`: Complete Neo4j schema definition (strict)
- `GRAPH_SCHEMA`: Legacy schema (backward compatibility)
- `get_cypher_generation_prompt()`: Schema-safe prompt for query generation
- `get_qa_prompt()`: Answer synthesis prompt with query type detection
- `validate_cypher_query()`: Schema validation function
- `detect_query_type()`: Detect query type (price, trend, correlation, etc.)

**Schema Safety**:
- Only allows defined node types: Company, PriceDay, Year, Quarter, Month
- Only allows defined relationship types: HAS_PRICE, IN_YEAR, IN_QUARTER, IN_MONTH, PERFORMED_IN, CORRELATED_WITH, GDS_SIMILAR
- Prevents LLM from inventing new labels/properties
- Validates against regex patterns

**Few-Shot Examples**: Includes examples for:
- Latest price queries
- Trend queries
- Correlation queries
- GDS queries (similarity, PageRank, community)

---

#### `intent_classifier.py`
**Purpose**: Classify user intent to determine if database query is needed

**Intent Types**:
- `data_query`: Needs Cypher query (e.g., "What is the price of MSFT?")
- `conversational`: General chat (e.g., "thanks", "hello")
- `clarification`: Asking about previous answer (e.g., "what do you mean?")
- `confirmation`: Asking for confirmation (e.g., "are you sure?")

**Features**:
- Pattern matching for common intents (fast path)
- LLM fallback for ambiguous cases
- Context-aware (uses previous conversation)

---

### Data Loading Scripts

#### `load_data_to_neo4j.py`
**Purpose**: Load stock price data from CSV into Neo4j

**Process**:
1. Reads `rawdata_cleanupscripts/stock_prices_pg.csv`
2. Creates `Company` nodes (10 companies)
3. Creates `PriceDay` nodes (~39,529 nodes)
4. Creates `HAS_PRICE` relationships
5. Adds constraints and indexes

**Output**:
- 10 Company nodes
- 39,529 PriceDay nodes
- 39,529 HAS_PRICE relationships

**Usage**: `python load_data_to_neo4j.py`

---

#### `load_schema_extension.py`
**Purpose**: Extend graph schema with time dimensions and derived relationships

**Creates**:
- **Time Dimension Nodes**:
  - `Year` nodes (17 years: 2010-2026)
  - `Quarter` nodes (65 quarters)
  - `Month` nodes (193 months)
- **Time Relationships**:
  - `(:PriceDay)-[:IN_YEAR]->(:Year)`
  - `(:PriceDay)-[:IN_QUARTER]->(:Quarter)`
  - `(:PriceDay)-[:IN_MONTH]->(:Month)`
- **Derived Relationships**:
  - `(:Company)-[:PERFORMED_IN {return_pct, start_price, end_price}]->(:Year)` (168 relationships)
  - `(:Company)-[:CORRELATED_WITH {correlation, sample_size}]-(:Company)` (35 relationships)

**Usage**: `python load_schema_extension.py`

**Note**: Requires `schema_extension.cypher` file

---

#### `load_companies_to_neo4j.py`
**Purpose**: Load company metadata (sector, location, employees, market cap) from Postgres to Neo4j

**Process**:
1. Connects to Postgres and reads `companies` table (502 companies)
2. Enriches existing Company nodes with:
   - `sector` (Technology, Financial Services, Healthcare, etc.)
   - `fulltimeemployees` (number of employees)
   - `marketcap` (market capitalization)
3. Creates new nodes:
   - `Sector` nodes (11 sectors)
   - `Country` nodes (8 countries)
   - `State` nodes (41 states)
   - `City` nodes (233 cities)
4. Creates relationships:
   - `IN_SECTOR`, `LOCATED_IN`, `IN_STATE`, `IN_CITY`
   - Location hierarchy: `City → State → Country`

**Output**:
- 11 Sector nodes
- 8 Country nodes
- 41 State nodes
- 233 City nodes
- 10 Company nodes enriched (the ones with stock price data)

**Usage**: `python load_companies_to_neo4j.py`

**Requirements**: 
- PostgreSQL `companies` table must exist
- Neo4j Company nodes must exist (from `load_data_to_neo4j.py`)

**New Capabilities**:
- Query companies by sector
- Find companies in same sector
- Sector-based GDS analysis
- Location-based queries

---

#### `schema_extension.cypher`
**Purpose**: Cypher script defining extended schema

**Contents**:
- Time dimension node creation
- Time relationship creation (IN_YEAR, IN_QUARTER, IN_MONTH)
- PERFORMED_IN relationship calculation (yearly returns)
- CORRELATED_WITH relationship calculation (pairwise correlation)

**Algorithm for CORRELATED_WITH**:
- Calculates daily returns for each company pair
- Computes Pearson correlation coefficient
- Only creates relationships if |correlation| >= 0.3 and sample_size >= 30

---

### Graph Data Science (GDS)

#### `gds_setup.py`
**Purpose**: Setup and run GDS algorithms on the graph

**Algorithms**:
1. **Node Similarity**: Creates `GDS_SIMILAR` relationships (100 relationships)
   - Measures structural similarity between companies
   - Top-K: 5 most similar companies per company
   - Similarity cutoff: 0.1

2. **PageRank**: Adds `Company.pagerank` property
   - Measures network centrality/influence
   - Uses CORRELATED_WITH relationships with correlation weights
   - Max iterations: 20, Damping factor: 0.85

3. **Louvain Community Detection**: Adds `Company.community` property
   - Groups companies into communities (2 communities found)
   - Community 5: Tech stocks (AAPL, AMZN, GOOG, META, MSFT, NVDA, TSLA)
   - Community 4: Finance/Healthcare (BRK-B, JPM, UNH)

4. **FastRP Embeddings**: Adds `Company.embedding` property (128-dim vectors)
   - Graph embeddings for similarity search
   - Can be used for cosine similarity queries

**Projection**: `company-graph` (in-memory graph projection)

**Usage**: `python gds_setup.py`

**Requirements**:
- GDS plugin installed in Neo4j
- CORRELATED_WITH relationships must exist

---

#### `gds_setup.cypher`
**Purpose**: Cypher script for GDS operations (alternative to Python script)

**Contents**:
- GDS version check
- Graph projection creation
- Node Similarity execution
- PageRank execution
- Louvain execution
- FastRP execution
- Verification queries

**Usage**: Can be run in Neo4j Browser or cypher-shell

---

#### `test_gds_insights.py`
**Purpose**: Test GDS outputs and their impact on GraphRAG

**Tests**:
- Direct GDS queries (similarity, PageRank, community)
- GraphRAG questions using GDS outputs
- Comparison: with vs without GDS

**Usage**: `python test_gds_insights.py`

---

#### `GDS_GRAPHRAG_USAGE.md`
**Purpose**: Documentation on how to use GDS outputs in GraphRAG

**Contents**:
- Explanation of each GDS algorithm
- Query patterns for each algorithm
- Example questions
- Integration with GraphRAG prompts
- Best practices

---

### Installation Scripts

#### `install_gds_docker.sh`
**Purpose**: Install GDS plugin in Neo4j Docker container

**Process**:
1. Downloads GDS JAR (version 2.6.9, compatible with Neo4j 5.18)
2. Copies to container's plugins directory
3. Restarts container

**Usage**: `./install_gds_docker.sh`

**Note**: Requires Neo4j container named `neo4j-local`

---

#### `install_n10s_docker.sh`
**Purpose**: Install n10s (Neosemantics) plugin in Neo4j Docker container

**Process**:
1. Uses `NEO4J_PLUGINS` environment variable
2. Downloads n10s plugin automatically
3. Restarts container

**Usage**: `./install_n10s_docker.sh`

**Note**: Compatible with Neo4j 5.18 (not 5.19)

---

#### `install_n10s_neo4j_5.18.sh`
**Purpose**: Alternative n10s installation for Neo4j 5.18

**Process**:
1. Recreates Neo4j container with Neo4j 5.18
2. Installs both GDS and n10s plugins
3. Verifies installation

**Usage**: `./install_n10s_neo4j_5.18.sh`

**Warning**: Recreates container (data will be lost, need to reload)

---

### Ontology & RDF Integration

#### `import_n10s_ontology.py`
**Purpose**: Import RDF/OWL ontology into Neo4j using n10s

**Process**:
1. Checks n10s installation
2. Imports `stock_ontology.ttl` into Neo4j
3. Adds namespace prefix: `stock → http://kg-demo.org/stock#`
4. Maps Neo4j nodes to RDF classes:
   - Company → http://kg-demo.org/stock#Company
   - PriceDay → http://kg-demo.org/stock#PriceDay
   - Year → http://kg-demo.org/stock#Year
   - Quarter → http://kg-demo.org/stock#Quarter
   - Month → http://kg-demo.org/stock#Month

**Usage**: `python import_n10s_ontology.py`

**Requirements**: n10s plugin must be installed

---

#### `explore_n10s_ontology.py`
**Purpose**: Generate RDF/OWL ontology from Neo4j schema

**Output**: `stock_ontology.ttl` (Turtle format)

**Contents**:
- RDF classes for each node type
- Object properties for relationships
- Data properties for node attributes

---

#### `stock_ontology.ttl`
**Purpose**: RDF/OWL ontology in Turtle format (for n10s)

**Namespace**: `http://kg-demo.org/stock#`

**Classes**: Company, PriceDay, Year, Quarter, Month

**Properties**: symbol, date, open, high, low, close, adj_close, volume, year, quarter, month, correlation, return_pct, etc.

---

#### `explore_ontop.py`
**Purpose**: Generate Ontop VKG files (OBDA mapping, OWL ontology, properties)

**Outputs**:
- `stock_mapping.obda`: OBDA mapping file
- `stock_ontology_ontop.owl`: OWL ontology
- `stock_ontop.properties`: PostgreSQL connection properties

---

#### `stock_mapping.obda`
**Purpose**: OBDA mapping file for Ontop (maps PostgreSQL to RDF)

**Maps**: `stock_prices` table → RDF triples

**Usage**: Used by Ontop to create Virtual Knowledge Graph

---

#### `stock_ontology_ontop.owl`
**Purpose**: OWL ontology for Ontop

**Format**: OWL/XML

**Usage**: Used by Ontop for SPARQL queries

---

#### `stock_ontop.properties`
**Purpose**: Ontop properties file (PostgreSQL connection)

**Contents**:
- `jdbc.url`: jdbc:postgresql://localhost:5434/kg_demo
- `jdbc.user`: postgres
- `jdbc.password`: postgres
- `jdbc.driver`: org.postgresql.Driver

---

#### `start_ontop.sh`
**Purpose**: Start Ontop VKG endpoint

**Process**:
1. Checks for Ontop JAR (prompts for download if missing)
2. Starts Ontop endpoint on port 8080
3. Uses `stock_mapping.obda`, `stock_ontology_ontop.owl`, `stock_ontop.properties`

**Usage**: `./start_ontop.sh`

**Access**: http://localhost:8080/sparql

---

#### `start_ontop_docker.sh`
**Purpose**: Start Ontop using Docker (from ontop-tutorial)

**Usage**: `./start_ontop_docker.sh`

**Note**: Uses ontop-tutorial Docker setup (needs customization for stock data)

---

### Frontend Files

#### `index.html`
**Purpose**: Main HTML page for chatbot UI

**Features**:
- Chat interface
- Example questions
- Responsive design

---

#### `app.js`
**Purpose**: Frontend JavaScript for chatbot

**Features**:
- Sends questions to `/chat` endpoint
- Displays answers with metadata (confidence, query trace, processing time)
- Handles errors
- Manages conversation context

---

#### `style.css`
**Purpose**: Styling for chatbot UI

**Features**:
- Modern, clean design
- Responsive layout
- Chat bubble styling
- Metadata display styling

---

### Data Files

#### `rawdata_cleanupscripts/download_prices_clean.py`
**Purpose**: Download stock prices from Yahoo Finance

**Process**:
1. Downloads data for 10 symbols (AAPL, MSFT, GOOG, AMZN, META, NVDA, TSLA, JPM, UNH, BRK-B)
2. Date range: 2010-01-01 to present
3. Cleans data (handles NaNs, converts types)
4. Outputs long-format CSV: `stock_prices_pg.csv`

**Output Schema**: `date,open,high,low,close,adj_close,volume,symbol`

**Usage**: `python download_prices_clean.py`

---

#### `rawdata_cleanupscripts/stock_prices_pg.csv`
**Purpose**: Clean stock price data (source of truth)

**Statistics**:
- Rows: 39,529
- Companies: 10
- Date range: 2010-01-01 to ~2024
- Format: Long format (one row per date-symbol pair)

---

### Configuration Files

#### `.env`
**Purpose**: Environment variables

**Contents**:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=test12345
OPENAI_API_KEY=your_key_here
```

---

#### `requirements.txt`
**Purpose**: Python dependencies

**Contents**:
```
fastapi
uvicorn
neo4j
openai
python-dotenv
requests
```

**Note**: Additional dependencies (pandas, yfinance) used in data scripts but not in production backend

---

## Data Pipeline

### Step 1: Data Download
```bash
cd rawdata_cleanupscripts
python download_prices_clean.py
```

**Output**: `stock_prices_pg.csv` (39,529 rows)

### Step 2: Load to PostgreSQL (Optional)
```bash
docker exec -i postgres-local-snp psql -U postgres -d kg_demo << EOF
\copy stock_prices FROM '/path/to/stock_prices_pg.csv' WITH CSV HEADER;
EOF
```

### Step 3: Load to Neo4j
```bash
cd chatbot/backend
python load_data_to_neo4j.py
```

**Output**: 10 Company nodes, 39,529 PriceDay nodes, 39,529 HAS_PRICE relationships

### Step 4: Extend Schema
```bash
python load_schema_extension.py
```

**Output**: Time dimensions + PERFORMED_IN + CORRELATED_WITH relationships

### Step 5: Setup GDS
```bash
python gds_setup.py
```

**Output**: GDS_SIMILAR relationships, PageRank, Community, Embeddings

### Step 6: Load Companies Metadata (Optional but Recommended)
```bash
python load_companies_to_neo4j.py
```

**Output**: Sector, Country, State, City nodes and relationships

### Step 7: Import Ontology (Optional)
```bash
python import_n10s_ontology.py
```

**Output**: RDF/OWL ontology imported, mappings created

---

## Neo4j Graph Schema

### Node Types

1. **Company**
   - Properties: `symbol` (String), `sector` (String), `fulltimeemployees` (Integer), `marketcap` (Float)
   - GDS Properties: `pagerank` (Float), `community` (Integer), `embedding` (List<Float>)
   - Count: 10 (with stock data), 502 total in companies table

2. **PriceDay**
   - Properties: `date` (Date), `open` (Float), `high` (Float), `low` (Float), `close` (Float), `adj_close` (Float), `volume` (Integer)
   - Count: 39,529

3. **Year**
   - Properties: `year` (Integer)
   - Count: 17 (2010-2026)

4. **Quarter**
   - Properties: `year` (Integer), `quarter` (Integer)
   - Count: 65

5. **Month**
   - Properties: `year` (Integer), `month` (Integer)
   - Count: 193

6. **Sector**
   - Properties: `name` (String)
   - Count: 11 (Technology, Financial Services, Healthcare, etc.)

7. **Country**
   - Properties: `name` (String)
   - Count: 8

8. **State**
   - Properties: `name` (String), `country` (String)
   - Count: 41

9. **City**
   - Properties: `name` (String), `state` (String), `country` (String)
   - Count: 233

### Relationship Types

1. **HAS_PRICE**
   - `(:Company)-[:HAS_PRICE]->(:PriceDay)`
   - Count: 39,529

2. **IN_YEAR**
   - `(:PriceDay)-[:IN_YEAR]->(:Year)`
   - Count: 39,529

3. **IN_QUARTER**
   - `(:PriceDay)-[:IN_QUARTER]->(:Quarter)`
   - Count: 39,529

4. **IN_MONTH**
   - `(:PriceDay)-[:IN_MONTH]->(:Month)`
   - Count: 39,529

5. **PERFORMED_IN**
   - `(:Company)-[:PERFORMED_IN {return_pct: Float, start_price: Float, end_price: Float}]->(:Year)`
   - Count: 168 (10 companies × ~17 years)

6. **CORRELATED_WITH**
   - `(:Company)-[:CORRELATED_WITH {correlation: Float, sample_size: Integer}]-(:Company)`
   - Count: 35 (undirected, |correlation| >= 0.3)

7. **GDS_SIMILAR**
   - `(:Company)-[:GDS_SIMILAR {score: Float}]-(:Company)`
   - Count: 100 (from GDS Node Similarity, top-K=5)

8. **IN_SECTOR**
   - `(:Company)-[:IN_SECTOR]->(:Sector)`
   - Count: 10 (companies with stock data)

9. **LOCATED_IN**
   - `(:Company)-[:LOCATED_IN]->(:Country)`
   - Count: 10

10. **IN_STATE**
    - `(:Company)-[:IN_STATE]->(:State)`
    - Count: 10

11. **IN_CITY**
    - `(:Company)-[:IN_CITY]->(:City)`
    - Count: 10

12. **IN_COUNTRY**
    - `(:State)-[:IN_COUNTRY]->(:Country)`
    - Count: 41

### Constraints & Indexes

- `CREATE CONSTRAINT company_symbol_unique FOR (c:Company) REQUIRE c.symbol IS UNIQUE`
- `CREATE INDEX priceday_date_idx FOR (p:PriceDay) ON (p.date)`
- `CREATE INDEX year_year_idx FOR (y:Year) ON (y.year)`

---

## Graph Data Science (GDS)

### Algorithms Used

1. **Node Similarity**
   - **Output**: `GDS_SIMILAR` relationships
   - **Score Range**: 0.0 - 1.0
   - **Top-K**: 5 most similar companies per company
   - **Use Case**: Find companies with similar correlation patterns

2. **PageRank**
   - **Output**: `Company.pagerank` property
   - **Range**: Typically 0.5 - 2.0
   - **Use Case**: Identify most influential/central companies in the network

3. **Louvain Community Detection**
   - **Output**: `Company.community` property
   - **Communities Found**: 2
   - **Use Case**: Group companies by market segments

4. **FastRP Embeddings**
   - **Output**: `Company.embedding` property (128 dimensions)
   - **Use Case**: Semantic similarity search using cosine similarity

### GDS Projection

- **Name**: `company-graph`
- **Node Label**: `Company`
- **Relationship Type**: `CORRELATED_WITH` (undirected, weighted by correlation)
- **In-Memory**: Yes (projected graph, not stored)

---

## GraphRAG Implementation

### Query Generation Flow

1. **Intent Classification**: Determine if question needs database query
2. **Symbol Extraction**: Extract ticker symbol from question (handles company names)
3. **Cypher Generation**: LLM generates schema-safe Cypher query
4. **Schema Validation**: Validate query against allowed schema
5. **Query Execution**: Execute on Neo4j
6. **Answer Synthesis**: LLM synthesizes natural language answer from results

### Schema Safety

- **Strict Schema Enforcement**: Only allows defined node/relationship types
- **Parameter Usage**: Forces use of parameters ($symbol, $year, etc.)
- **Validation**: Regex-based validation before execution
- **Few-Shot Examples**: Provides examples to guide LLM

### Context Management

- **Conversation ID**: Tracks conversation context
- **Last Symbol**: Remembers last company discussed
- **Follow-up Detection**: Handles "What about AAPL?" type questions

### Confidence Scoring

- **Query Type**: Different confidence levels for different query types
- **Result Count**: Higher confidence with more results
- **Data Quality**: Checks for missing/null values

---

## Containerization

### Docker Containers

1. **Neo4j** (`neo4j-local`)
   - **Image**: `neo4j:5.18`
   - **Ports**: 7474 (HTTP), 7687 (Bolt)
   - **Plugins**: GDS 2.6.9, n10s 5.18.0
   - **Auth**: neo4j/test12345

2. **PostgreSQL** (`postgres-local-snp`)
   - **Image**: `postgres:15`
   - **Port**: 5434 (host) → 5432 (container)
   - **Database**: `kg_demo`
   - **User**: postgres/postgres

3. **Other Containers** (not used in this project):
   - `grafana`: Monitoring (port 3000)
   - `mongo`: MongoDB (port 27017)
   - `ngrok`: Tunneling service

### Container Management

**Start Neo4j**:
```bash
docker start neo4j-local
```

**Start PostgreSQL**:
```bash
docker start postgres-local-snp
```

**Stop Containers**:
```bash
docker stop neo4j-local postgres-local-snp
```

**View Logs**:
```bash
docker logs neo4j-local
docker logs postgres-local-snp
```

---

## API Endpoints

### `GET /`
**Purpose**: Health check

**Response**:
```json
{"status": "ok"}
```

---

### `POST /chat`
**Purpose**: Main chat endpoint

**Request Body**:
```json
{
  "question": "What is the latest price of MSFT?",
  "conversation_id": "optional-conversation-id",
  "context": []
}
```

**Response**:
```json
{
  "answer": "The latest price of MSFT was $420.50 on 2024-01-15.",
  "confidence": 0.95,
  "query_trace": "MATCH (c:Company {symbol: $symbol})...",
  "generated_query": "MATCH (c:Company {symbol: $symbol})...",
  "processing_time": 1.23,
  "error": null
}
```

**Error Response**:
```json
{
  "answer": "I'm sorry, I couldn't process your question.",
  "confidence": 0.0,
  "error": "Error message here"
}
```

---

## Frontend

### Features

- **Chat Interface**: Real-time chat with the chatbot
- **Example Questions**: Quick buttons for common queries
- **Metadata Display**: Shows confidence, query trace, processing time
- **Error Handling**: Displays errors gracefully
- **Responsive Design**: Works on desktop and mobile

### Access

Open `chatbot/frontend/index.html` in a web browser, or serve via HTTP server:

```bash
cd chatbot/frontend
python -m http.server 8000
```

Then open: http://localhost:8000

---

## Ontology & RDF Integration

### n10s (Neosemantics)

**Purpose**: RDF/OWL integration with Neo4j

**Features**:
- Import RDF/OWL ontologies
- Export Neo4j data as RDF
- Map Neo4j nodes to RDF classes
- SPARQL queries (with additional configuration)

**Status**: ✅ Installed and configured
- Ontology imported: `stock_ontology.ttl`
- Namespace prefix: `stock → http://kg-demo.org/stock#`
- Mappings: 5 node types mapped

---

### Ontop Virtual Knowledge Graph

**Purpose**: SPARQL queries over PostgreSQL

**Features**:
- Virtual RDF layer over relational database
- SPARQL endpoint (port 8080)
- OBDA mapping (PostgreSQL → RDF)

**Status**: ⏳ Ready to start (needs Ontop JAR download)

**Files**:
- `stock_mapping.obda`: OBDA mapping
- `stock_ontology_ontop.owl`: OWL ontology
- `stock_ontop.properties`: Connection properties

**Start**:
```bash
./start_ontop.sh
```

**Access**: http://localhost:8080/sparql

---

## Setup & Installation

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- Neo4j 5.18 (with GDS and n10s plugins)
- PostgreSQL 15
- OpenAI API key

### Step-by-Step Setup

1. **Clone/Download Project**
   ```bash
   cd kg_demo
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   cd chatbot/backend
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   # Create .env file in root
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=test12345
   OPENAI_API_KEY=your_key_here
   ```

5. **Start Docker Containers**
   ```bash
   docker start neo4j-local postgres-local-snp
   # Or create new containers if needed
   ```

6. **Install GDS Plugin** (if not already installed)
   ```bash
   cd chatbot/backend
   ./install_gds_docker.sh
   ```

7. **Install n10s Plugin** (optional)
   ```bash
   ./install_n10s_neo4j_5.18.sh
   # Note: This recreates Neo4j container, need to reload data
   ```

8. **Download Data**
   ```bash
   cd rawdata_cleanupscripts
   python download_prices_clean.py
   ```

9. **Load Data to Neo4j**
   ```bash
   cd chatbot/backend
   python load_data_to_neo4j.py
   ```

10. **Extend Schema**
    ```bash
    python load_schema_extension.py
    ```

11. **Setup GDS**
    ```bash
    python gds_setup.py
    ```

12. **Import Ontology** (optional)
    ```bash
    python import_n10s_ontology.py
    ```

13. **Start Backend**
    ```bash
    uvicorn app:app --reload --port 8000
    ```

14. **Open Frontend**
    ```bash
    cd ../frontend
    python -m http.server 8000
    # Or open index.html directly in browser
    ```

---

## Usage Guide

### Starting the System

**Terminal 1 - Backend**:
```bash
cd chatbot/backend
source ../../venv/bin/activate
uvicorn app:app --reload --port 8000
```

**Terminal 2 - Frontend** (optional, if serving via HTTP):
```bash
cd chatbot/frontend
python -m http.server 8080
```

**Browser**: Open `chatbot/frontend/index.html` or http://localhost:8080

---

### Example Questions

1. **Basic Price Query**:
   - "What is the latest price of MSFT?"
   - "Show me the price of AAPL"
   - "Tell me about GOOG stock price"

2. **Company Name**:
   - "What is the price of Apple?"
   - "Show me Microsoft stock price"

3. **List Companies**:
   - "What companies are in the database?"
   - "List all companies"

4. **GDS Queries** (after GDS setup):
   - "Which companies are similar to AAPL?"
   - "What are the most influential companies?"
   - "What companies are in the same group as MSFT?"

5. **Sector Queries** (after companies data loaded):
   - "What sector does Apple belong to?"
   - "What other companies are in Technology sector?"
   - "Which companies in same sector as Apple move together?"

5. **Follow-up Questions**:
   - "What about NVDA?"
   - "Show me the price" (uses context)

---

### Testing

**Test GDS Insights**:
```bash
cd chatbot/backend
python test_gds_insights.py
```

**Test API** (using curl):
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the latest price of MSFT?"}'
```

**Test Sector Queries**:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What sector does Apple belong to?"}'

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Which companies in same sector as Apple move together?"}'
```

**Graph Visualizations**:
Run queries from `graph_visualization_queries.cypher` in Neo4j Browser for beautiful graph visualizations.

---

## What's Next

### Completed ✅

- [x] Data pipeline (download, clean, load)
- [x] Neo4j base graph (Company, PriceDay, HAS_PRICE)
- [x] Schema extension (time dimensions, PERFORMED_IN, CORRELATED_WITH)
- [x] GraphRAG core pipeline (intent classification, Cypher generation, answer synthesis)
- [x] GDS integration (Node Similarity, PageRank, Community Detection, FastRP)
- [x] n10s integration (RDF/OWL ontology)
- [x] Frontend chatbot UI
- [x] Schema safety enforcement
- [x] Companies metadata loading (sector, location, employees, market cap)
- [x] Sector-based queries and GDS analysis
- [x] Graph visualization queries
- [x] Production-ready chatbot with explanation question handling

### In Progress / Partial ⏳

- [ ] Ontop VKG startup (files ready, need JAR download)
- [ ] SPARQL queries via n10s (requires additional configuration)
- [ ] Advanced query types (volatility, rolling averages, etc.)

### Future Enhancements 🚀

1. **Unstructured Data Integration**
   - Add company news, earnings reports, SEC filings
   - Use embeddings for semantic search
   - Link to existing graph nodes

2. **Enhanced GraphRAG**
   - Multi-hop reasoning (e.g., "Which tech stock outperformed AAPL in 2022?")
   - Temporal reasoning (e.g., "Show price trend over last 5 years")
   - Comparative analysis (e.g., "Compare AAPL vs MSFT performance")

3. **Advanced Analytics**
   - Volatility calculations
   - Moving averages
   - Technical indicators (RSI, MACD, etc.)
   - Sector/industry classification

4. **Production Readiness**
   - Redis for conversation context (replace in-memory cache)
   - Query caching
   - Rate limiting
   - Authentication/authorization
   - Monitoring & logging (Grafana, Prometheus)

5. **UI Enhancements**
   - Chat history
   - Export conversations
   - Query visualization
   - Graph visualization (Neo4j Bloom integration)

6. **Data Expansion**
   - More companies (S&P 500 full list)
   - Real-time data updates
   - Options data
   - Fundamental data (P/E ratio, market cap, etc.)

---

## Troubleshooting

### Neo4j Connection Issues

**Error**: `Neo.ClientError.Security.Unauthorized`
- **Solution**: Check `.env` file, ensure password matches container

**Error**: `GDS not found`
- **Solution**: Run `./install_gds_docker.sh`

### OpenAI API Issues

**Error**: `OpenAI API key not found`
- **Solution**: Add `OPENAI_API_KEY` to `.env` file

**Error**: `Rate limit exceeded`
- **Solution**: Wait or upgrade OpenAI plan

### Data Loading Issues

**Error**: `No Company nodes found`
- **Solution**: Run `python load_data_to_neo4j.py`

**Error**: `CORRELATED_WITH relationships missing`
- **Solution**: Run `python load_schema_extension.py`

### GDS Issues

**Error**: `GDS projection not found`
- **Solution**: Run `python gds_setup.py`

**Error**: `CORRELATED_WITH not in projection`
- **Solution**: Ensure CORRELATED_WITH relationships exist before running GDS setup

---

## Summary

This project demonstrates a complete **GraphRAG system** for stock market data:

- **Data Layer**: Clean CSV → PostgreSQL → Neo4j graph
- **Graph Layer**: Extended schema with time dimensions and derived relationships
- **Analytics Layer**: GDS algorithms (similarity, centrality, community, embeddings)
- **Semantic Layer**: RDF/OWL ontology (n10s) and Virtual Knowledge Graph (Ontop)
- **Application Layer**: GraphRAG chatbot with schema-safe query generation
- **UI Layer**: Interactive web interface

**Key Achievements**:
- ✅ Schema-safe Cypher generation (prevents hallucination)
- ✅ GDS integration for network analytics
- ✅ RDF/OWL ontology for governance
- ✅ Production-ready code structure
- ✅ Comprehensive documentation

**Next Steps**: Expand data, enhance queries, add unstructured data, productionize

---

**Last Updated**: 2026-01-07
**Version**: 2.0.0
**Author**: GraphRAG Stock Market Knowledge Graph Project

---

## Recent Updates (v2.0.0)

### Companies Data Integration
- ✅ Loaded 502 companies from Postgres `companies` table
- ✅ Enriched Company nodes with sector, location, employees, market cap
- ✅ Created Sector, Country, State, City nodes and relationships
- ✅ Enabled sector-based queries and GDS analysis

### Production-Ready Chatbot
- ✅ Added explanation question detection ("how is that calculated")
- ✅ Added methodology explanation for GDS algorithms
- ✅ Improved follow-up question handling
- ✅ Enhanced error handling with retry logic
- ✅ Better context management and conversation flow

### Graph Visualizations
- ✅ Created `graph_visualization_queries.cypher` with 10 visualization queries
- ✅ Sector-based network visualizations
- ✅ Cross-sector similarity visualizations
- ✅ Complete company network with all relationships

