# GraphRAG Demo - Stock Market Knowledge Graph

A comprehensive GraphRAG (Graph Retrieval-Augmented Generation) system for stock market data analysis using Neo4j, PostgreSQL, and LLMs.

## 🎯 Overview

This project demonstrates a complete GraphRAG pipeline for analyzing S&P 500 stock data:

- **Data Pipeline**: Yahoo Finance data ingestion and cleaning
- **Graph Database**: Neo4j with extended schema (time dimensions, relationships)
- **Graph Data Science**: Node Similarity, PageRank, Community Detection, FastRP Embeddings
- **GraphRAG Chatbot**: LLM-powered natural language query interface
- **RDF/OWL Integration**: n10s plugin for ontology management
- **Virtual Knowledge Graph**: Ontop for SPARQL queries over PostgreSQL

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend    │────▶│   Neo4j     │
│  (React)    │     │  (FastAPI)   │     │  (Graph DB) │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                    │
                            │                    │
                     ┌──────▼──────┐     ┌──────▼──────┐
                     │  PostgreSQL  │     │     GDS     │
                     │  (Relational)│     │  (Analytics)│
                     └─────────────┘     └─────────────┘
                            │
                            │
                     ┌──────▼──────┐
                     │    Ontop    │
                     │  (VKG/SPARQL)│
                     └─────────────┘
```

## 📁 Project Structure

```
kg_demo/
├── rawdata_cleanupscripts/    # Data download and cleaning
│   ├── download_prices_clean.py
│   └── stock_prices_pg.csv
├── chatbot/
│   ├── backend/               # FastAPI backend
│   │   ├── app.py            # Main API server
│   │   ├── graph.py          # Neo4j connection
│   │   ├── llm.py             # LLM integration
│   │   ├── prompts.py         # Schema-safe prompts
│   │   ├── intent_classifier.py
│   │   ├── gds_setup.py       # GDS algorithms
│   │   ├── schema_extension.cypher
│   │   └── ...
│   └── frontend/              # React frontend
│       ├── app.js
│       ├── style.css
│       └── index.html
├── start_all.sh               # Start all services
├── stop_all.sh                # Stop all services
└── START_COMMANDS.md          # Detailed commands
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop
- Python 3.9+
- Node.js 16+
- OpenAI API key

### 1. Clone Repository

```bash
git clone https://github.com/adarshvuppala-nu/kg_demo.git
cd kg_demo
```

### 2. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r chatbot/backend/requirements.txt

# Install frontend dependencies
cd chatbot/frontend
npm install
cd ../..
```

### 3. Configure Environment

Create `.env` file in root:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=test12345
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Start All Services

```bash
# Make scripts executable
chmod +x start_all.sh stop_all.sh

# Start everything
./start_all.sh
```

Or manually:

```bash
# Start Docker containers
docker start postgres-local-snp neo4j-local

# Start Backend (Terminal 1)
cd chatbot/backend
source ../../venv/bin/activate
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Start Frontend (Terminal 2)
cd chatbot/frontend
npm start
```

### 5. Access Services

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **Neo4j Browser**: http://localhost:7474
- **PostgreSQL**: localhost:5434
- **Ontop SPARQL**: http://localhost:8081/sparql

## 📊 Data Pipeline

### Download Stock Data

```bash
cd rawdata_cleanupscripts
python3 download_prices_clean.py
```

This creates `stock_prices_pg.csv` with clean, long-format data.

### Load to PostgreSQL

```bash
docker exec -i postgres-local-snp psql -U postgres -d kg_demo << EOF
\copy stock_prices FROM '/path/to/stock_prices_pg.csv' CSV HEADER;
EOF
```

### Load to Neo4j

```bash
cd chatbot/backend
source ../../venv/bin/activate
python3 load_data_to_neo4j.py
python3 load_schema_extension.py
```

## 🔬 Graph Data Science (GDS)

### Install GDS Plugin

```bash
cd chatbot/backend
./install_gds_docker.sh
```

### Run GDS Algorithms

```bash
python3 gds_setup.py
```

This creates:
- **Node Similarity**: `GDS_SIMILAR` relationships
- **PageRank**: `Company.pagerank` property
- **Community Detection**: `Company.community` property
- **FastRP Embeddings**: `Company.embedding` property

### Test GDS Insights

```bash
python3 test_gds_insights.py
```

## 💬 GraphRAG Chatbot

### Features

- **Natural Language Queries**: Ask questions in plain English
- **Schema-Safe Cypher Generation**: LLM generates valid Neo4j queries
- **Conversation Context**: Remembers previous questions
- **Complex Query Support**: Trends, comparisons, correlations, GDS queries

### Example Queries

- "What is the latest price of MSFT?"
- "Which stock outperformed AAPL in 2022?"
- "What companies are most correlated with TSLA?"
- "Show me the price trend of NVDA over the last 5 years"
- "What are the top 3 companies by PageRank?"
- "What companies are in the same group as MSFT?"

## 🔧 Advanced Features

### RDF/OWL Integration (n10s)

```bash
cd chatbot/backend
./install_n10s_docker.sh
python3 import_n10s_ontology.py
```

### Virtual Knowledge Graph (Ontop)

```bash
cd chatbot/backend
./setup_ontop_from_zip.sh  # First time only
./start_ontop.sh
```

Query PostgreSQL via SPARQL at http://localhost:8081/sparql

## 📝 API Endpoints

### POST `/chat`

Chat with the GraphRAG system.

**Request:**
```json
{
  "question": "What is the price of MSFT?",
  "conversation_id": "optional-conversation-id"
}
```

**Response:**
```json
{
  "answer": "The price of MSFT on 2026-01-02 was $472.94...",
  "generated_query": "MATCH (c:Company {symbol: $symbol})...",
  "confidence": 0.85,
  "query_type": "price",
  "processing_time_ms": 1234
}
```

### GET `/`

Health check endpoint.

## 🛠️ Development

### Project Phases

- ✅ **Phase 0**: Foundations (Docker, Python, Node.js)
- ✅ **Phase 1**: Data Pipeline (Yahoo Finance, CSV cleaning)
- ✅ **Phase 2**: Neo4j Base Graph (Company, PriceDay nodes)
- ✅ **Phase 3**: Graph Enrichment (Time dimensions, relationships)
- ✅ **Phase 4**: GraphRAG Core Pipeline
- ✅ **Phase 5**: LLM Prompt Quality
- ✅ **Phase 6**: Advanced Relationships (GDS)
- ✅ **Phase 7**: Query Depth & Reasoning
- ✅ **Phase 8**: UX/Product Polish (Chat memory, confidence scoring)

### Key Technologies

- **Neo4j**: Graph database with GDS plugin
- **PostgreSQL**: Relational database
- **FastAPI**: Python web framework
- **React**: Frontend framework
- **OpenAI GPT-4o-mini**: LLM for query generation and answer synthesis
- **n10s**: Neo4j RDF/OWL plugin
- **Ontop**: Virtual Knowledge Graph engine

## 📚 Documentation

- `PROJECT_DOCUMENTATION.md`: Complete project documentation
- `START_COMMANDS.md`: Detailed startup commands
- `chatbot/backend/gds_setup.cypher`: GDS algorithm definitions
- `chatbot/backend/schema_extension.cypher`: Extended graph schema

## 🔒 Security Notes

- Never commit `.env` files
- Use environment variables for API keys
- In production, use proper authentication
- Secure Neo4j and PostgreSQL with strong passwords

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is for demonstration purposes.

## 🙏 Acknowledgments

- Neo4j Graph Data Science Library
- OpenAI for LLM APIs
- Ontop Virtual Knowledge Graph
- n10s (Neosemantics) for RDF/OWL support

## 📞 Support

For issues or questions, please open an issue on GitHub.

---

**Repository**: https://github.com/adarshvuppala-nu/kg_demo.git

