# GraphRAG Demo - Presentation Guide

## 🎤 Conversation Script for Presentation

### Opening (30 seconds)

"Hi everyone! Today I'm going to show you a GraphRAG system I built for analyzing stock market data. 

What makes this interesting is that we're using a graph database - Neo4j - to store stock prices, and then we're using AI to let people ask questions in plain English. The system automatically converts those questions into database queries, gets the data, and gives you a natural language answer.

Let me show you what we built..."

---

### Part 1: The Data (1 minute)

"So first, let's talk about the data. We're working with S&P 500 top 10 stocks - companies like Apple, Microsoft, Google, Amazon, and so on. We have about 40,000 rows of historical price data going back to 2010.

The data includes things like:
- Daily prices: open, high, low, close
- Trading volume
- Adjusted close prices

We store this in two places:
1. PostgreSQL - for the raw relational data
2. Neo4j - as a knowledge graph where we can do graph analytics"

**Demo Query 1: See the raw data**
```cypher
// Show all companies in our database
MATCH (c:Company)
RETURN c.symbol AS Company
ORDER BY c.symbol
```

**Demo Query 2: Count the data**
```cypher
// How much data do we have?
MATCH (c:Company)-[:HAS_PRICE]->(p:PriceDay)
RETURN c.symbol AS Company, count(p) AS DaysOfData
ORDER BY DaysOfData DESC
```

---

### Part 2: The Graph Structure (1 minute)

"Now, here's where it gets interesting. Instead of just storing rows in a table, we're creating a graph. Each company is a node, each day's price is a node, and they're connected.

But we went further - we added time dimensions. So we have Year nodes, Quarter nodes, Month nodes. This lets us ask questions like 'What happened in 2022?' or 'Show me Q3 trends.'

We also created relationships like:
- PERFORMED_IN - which company performed best in a given year
- CORRELATED_WITH - which stocks move together
- GDS_SIMILAR - which companies are similar based on graph algorithms"

**Demo Query 3: See the graph structure**
```cypher
// Visualize the graph structure
MATCH (c:Company {symbol: 'AAPL'})-[:HAS_PRICE]->(p:PriceDay)-[:IN_YEAR]->(y:Year)
WHERE y.year = 2022
RETURN c, p, y
LIMIT 50
```

**Demo Query 4: Yearly performance**
```cypher
// Which companies performed best in 2022?
MATCH (c:Company)-[r:PERFORMED_IN]->(y:Year {year: 2022})
RETURN c.symbol AS Company, 
       round(r.return_pct, 2) AS Return_Percentage,
       round(r.start_price, 2) AS Start_Price,
       round(r.end_price, 2) AS End_Price
ORDER BY r.return_pct DESC
```

---

### Part 3: Graph Data Science - The Magic (2 minutes)

"This is where it gets really cool. We're using Neo4j's Graph Data Science library to find insights that you can't get from just looking at tables.

We ran four algorithms:

1. **Node Similarity** - Which companies have similar price patterns?
2. **PageRank** - Which companies are most influential in the network?
3. **Community Detection** - Which companies naturally group together?
4. **FastRP Embeddings** - We created vector embeddings for each company"

**Demo Query 5: Similar companies**
```cypher
// Which companies are similar to Apple?
MATCH (c1:Company {symbol: 'AAPL'})-[r:GDS_SIMILAR]-(c2:Company)
RETURN c2.symbol AS Similar_Company, 
       round(r.score, 3) AS Similarity_Score
ORDER BY r.score DESC
LIMIT 5
```

**Demo Query 6: Most influential companies (PageRank)**
```cypher
// Which companies are most central/influential?
MATCH (c:Company)
WHERE c.pagerank IS NOT NULL
RETURN c.symbol AS Company, 
       round(c.pagerank, 4) AS PageRank_Score
ORDER BY c.pagerank DESC
LIMIT 10
```

**Demo Query 7: Community detection**
```cypher
// Which companies are in the same community as Microsoft?
MATCH (c1:Company {symbol: 'MSFT'})
WHERE c1.community IS NOT NULL
MATCH (c2:Company)
WHERE c2.community = c1.community AND c2.symbol <> c1.symbol
RETURN c2.symbol AS Same_Community
ORDER BY c2.symbol
```

**Demo Query 8: Correlation analysis**
```cypher
// Which stocks are most correlated with Tesla?
MATCH (c1:Company {symbol: 'TSLA'})-[r:CORRELATED_WITH]-(c2:Company)
RETURN c2.symbol AS Correlated_Stock, 
       round(r.correlation, 3) AS Correlation_Value,
       r.sample_size AS Sample_Size
ORDER BY abs(r.correlation) DESC
LIMIT 5
```

---

### Part 4: The GraphRAG Chatbot (2 minutes)

"Now here's the fun part - the chatbot. Instead of writing Cypher queries, you can just ask questions in plain English.

The system:
1. Takes your question
2. Uses an LLM to generate a safe Cypher query
3. Runs it on Neo4j
4. Gets the results
5. Uses the LLM again to give you a natural language answer

And it remembers context! So if you ask 'What's the price of Microsoft?' and then say 'What about Apple?', it knows you're asking about Apple's price."

**Demo Questions to Try:**
- "What is the latest price of MSFT?"
- "Which stock outperformed AAPL in 2022?"
- "What companies are most correlated with TSLA?"
- "Show me the price trend of NVDA over the last 5 years"
- "What are the top 3 companies by PageRank?"
- "What companies are in the same group as MSFT?"

---

### Part 5: Advanced Features - RDF/OWL & Virtual Knowledge Graph (1 minute)

"We also integrated two advanced features:

**1. RDF/OWL Integration (n10s)**
This lets us add semantic meaning to our data. We can define ontologies and enforce governance rules. It's like adding a layer of meaning on top of the graph.

**2. Virtual Knowledge Graph (Ontop)**
This is really cool - we can query our PostgreSQL database using SPARQL, which is the standard query language for semantic web. So you can use graph queries on relational data!"

**Demo: Ontop SPARQL Query**
```sparql
# Get all companies from PostgreSQL via SPARQL
PREFIX : <http://kg-demo.org/stock#>

SELECT ?symbol WHERE {
  ?company a :Company .
  ?company :symbol ?symbol .
}
LIMIT 10
```

**Demo: Ontop SPARQL Query with Price Data**
```sparql
# Get recent price data for AAPL
PREFIX : <http://kg-demo.org/stock#>

SELECT ?symbol ?date ?close WHERE {
  ?company a :Company .
  ?company :symbol ?symbol .
  ?company :hasPrice ?price .
  ?price :date ?date .
  ?price :close ?close .
  FILTER(?symbol = 'AAPL')
}
ORDER BY DESC(?date)
LIMIT 5
```

---

### Part 6: Architecture Overview (1 minute)

"Let me quickly show you how everything fits together:

1. **Data Layer**: PostgreSQL for raw data, Neo4j for graph
2. **Analytics Layer**: Graph Data Science algorithms
3. **API Layer**: FastAPI backend that handles the chatbot
4. **Frontend**: Simple React interface where users chat
5. **AI Layer**: OpenAI GPT-4o-mini for query generation and answer synthesis

Everything is containerized with Docker, so it's easy to deploy."

---

### Closing (30 seconds)

"So to summarize:
- We built a complete GraphRAG system
- It uses graph databases for better analytics
- You can ask questions in plain English
- We added graph algorithms for deeper insights
- We integrated semantic web technologies

The key takeaway is that graph databases aren't just for social networks - they're powerful for financial data too, especially when combined with AI.

Any questions?"

---

## 📊 Quick Reference: Cypher Queries for Demo

### Basic Data Exploration

```cypher
// 1. List all companies
MATCH (c:Company)
RETURN c.symbol AS Company
ORDER BY c.symbol

// 2. Count price data per company
MATCH (c:Company)-[:HAS_PRICE]->(p:PriceDay)
RETURN c.symbol AS Company, count(p) AS TotalDays
ORDER BY TotalDays DESC

// 3. Latest price for a company
MATCH (c:Company {symbol: 'AAPL'})-[:HAS_PRICE]->(p:PriceDay)
RETURN p.date AS Date, p.close AS ClosePrice, p.volume AS Volume
ORDER BY p.date DESC
LIMIT 1
```

### Time-Based Queries

```cypher
// 4. Prices in a specific year
MATCH (c:Company {symbol: 'MSFT'})-[:HAS_PRICE]->(p:PriceDay)-[:IN_YEAR]->(y:Year {year: 2022})
RETURN p.date AS Date, p.close AS ClosePrice
ORDER BY p.date

// 5. Yearly performance comparison
MATCH (c:Company)-[r:PERFORMED_IN]->(y:Year {year: 2022})
RETURN c.symbol AS Company, 
       round(r.return_pct, 2) AS Return_Percent
ORDER BY r.return_pct DESC
```

### Graph Data Science Queries

```cypher
// 6. Similar companies (Node Similarity)
MATCH (c1:Company {symbol: 'AAPL'})-[r:GDS_SIMILAR]-(c2:Company)
RETURN c2.symbol AS Similar_Company, round(r.score, 3) AS Score
ORDER BY r.score DESC
LIMIT 5

// 7. Most influential (PageRank)
MATCH (c:Company)
WHERE c.pagerank IS NOT NULL
RETURN c.symbol AS Company, round(c.pagerank, 4) AS PageRank
ORDER BY c.pagerank DESC
LIMIT 10

// 8. Community members
MATCH (c1:Company {symbol: 'MSFT'})
WHERE c1.community IS NOT NULL
MATCH (c2:Company)
WHERE c2.community = c1.community AND c2.symbol <> c1.symbol
RETURN c2.symbol AS Community_Member
ORDER BY c2.symbol

// 9. Correlated stocks
MATCH (c1:Company {symbol: 'TSLA'})-[r:CORRELATED_WITH]-(c2:Company)
RETURN c2.symbol AS Correlated_Stock, 
       round(r.correlation, 3) AS Correlation
ORDER BY abs(r.correlation) DESC
LIMIT 5
```

### Complex Analytics

```cypher
// 10. Price trend over time (last 5 years)
MATCH (c:Company {symbol: 'NVDA'})-[:HAS_PRICE]->(p:PriceDay)-[:IN_YEAR]->(y:Year)
WHERE y.year >= date().year - 5
WITH y.year AS Year, avg(p.close) AS AvgPrice, min(p.close) AS MinPrice, max(p.close) AS MaxPrice
RETURN Year, round(AvgPrice, 2) AS Avg_Price, round(MinPrice, 2) AS Min_Price, round(MaxPrice, 2) AS Max_Price
ORDER BY Year

// 11. Which stock outperformed another in a year
MATCH (c1:Company {symbol: 'AAPL'})-[r1:PERFORMED_IN]->(y:Year {year: 2022})
MATCH (c2:Company)-[r2:PERFORMED_IN]->(y)
WHERE c2.symbol <> c1.symbol AND r2.return_pct > r1.return_pct
RETURN c2.symbol AS Outperformed_Company, 
       round(r2.return_pct, 2) AS Their_Return,
       round(r1.return_pct, 2) AS AAPL_Return
ORDER BY r2.return_pct DESC
LIMIT 5

// 12. Multi-company comparison
MATCH (c1:Company {symbol: 'MSFT'})-[r1:PERFORMED_IN]->(y:Year {year: 2023})
MATCH (c2:Company {symbol: 'GOOG'})-[r2:PERFORMED_IN]->(y)
RETURN c1.symbol AS Company1, round(r1.return_pct, 2) AS Return1,
       c2.symbol AS Company2, round(r2.return_pct, 2) AS Return2,
       round(r1.return_pct - r2.return_pct, 2) AS Difference
```

---

## 🔍 Ontop SPARQL Queries for Demo

### Basic SPARQL Queries

```sparql
# 1. List all companies (from PostgreSQL via Ontop)
PREFIX : <http://kg-demo.org/stock#>

SELECT ?symbol WHERE {
  ?company a :Company .
  ?company :symbol ?symbol .
}
ORDER BY ?symbol
LIMIT 10
```

```sparql
# 2. Get price data for a company
PREFIX : <http://kg-demo.org/stock#>

SELECT ?symbol ?date ?close ?volume WHERE {
  ?company a :Company .
  ?company :symbol ?symbol .
  ?company :hasPrice ?price .
  ?price :date ?date .
  ?price :close ?close .
  ?price :volume ?volume .
  FILTER(?symbol = 'AAPL')
}
ORDER BY DESC(?date)
LIMIT 10
```

```sparql
# 3. Get companies with their latest prices
PREFIX : <http://kg-demo.org/stock#>

SELECT ?symbol ?date ?close WHERE {
  ?company a :Company .
  ?company :symbol ?symbol .
  ?company :hasPrice ?price .
  ?price :date ?date .
  ?price :close ?close .
}
ORDER BY DESC(?date)
LIMIT 10
```

---

## 🎯 Presentation Tips

### Before You Start
1. **Test all queries** - Run them in Neo4j Browser first
2. **Have Neo4j Browser open** - Ready to paste queries
3. **Have chatbot ready** - Frontend should be running
4. **Have Ontop running** - If showing SPARQL queries

### During Presentation
1. **Start simple** - Show basic queries first
2. **Build complexity** - Move from simple to advanced
3. **Explain the "why"** - Not just the "what"
4. **Use visuals** - Neo4j Browser graph visualization is powerful
5. **Tell a story** - Connect queries to real business questions

### Key Points to Emphasize
- **Graph databases** are great for relationships
- **Graph Data Science** finds patterns you can't see in tables
- **GraphRAG** makes databases accessible to non-technical users
- **Semantic web** technologies add meaning and governance
- **Virtual Knowledge Graphs** bridge relational and graph worlds

### Common Questions & Answers

**Q: Why use a graph database for stock prices?**
A: "Because relationships matter. Which stocks move together? Which companies are similar? These are relationship questions that graphs answer naturally."

**Q: How is this different from a regular database?**
A: "In a regular database, you'd need complex JOINs. In a graph, relationships are first-class citizens. Plus, we can run graph algorithms that find patterns automatically."

**Q: What's the advantage of GraphRAG?**
A: "It makes the database accessible. You don't need to know SQL or Cypher - just ask questions in English. The AI handles the complexity."

**Q: Is this production-ready?**
A: "The architecture is solid. For production, you'd want to add authentication, rate limiting, and maybe caching. But the core GraphRAG pattern is production-ready."

---

## 🚀 Quick Start Commands for Demo

```bash
# 1. Start all services
cd /Users/adarshvuppala/kg_demo
./start_all.sh

# 2. Open Neo4j Browser
# Go to: http://localhost:7474
# Username: neo4j
# Password: test12345

# 3. Open chatbot frontend
# Go to: http://localhost:3001

# 4. Start Ontop (if showing SPARQL)
cd chatbot/backend
./start_ontop.sh
# Then go to: http://localhost:8081/sparql
```

---

## 📝 Notes for Presenter

- **Timing**: Total presentation ~8-10 minutes
- **Audience**: Technical but may not know graphs
- **Focus**: Show the power of graph + AI together
- **Demo**: Live queries work best, but have screenshots as backup
- **Ending**: Leave time for questions about use cases

Good luck with your presentation! 🎉

---

## 📁 Repository File Reference

### Root Directory Files

**README.md** - Main project documentation with overview, setup instructions, and quick start guide

**PROJECT_DOCUMENTATION.md** - Complete technical documentation covering architecture, data pipeline, Neo4j schema, GDS, GraphRAG implementation, and all components

**PRESENTATION_GUIDE.md** - This file: conversation script, demo queries, and presentation tips

**MANUAL_COMMANDS.md** - Step-by-step manual commands for starting/stopping services and troubleshooting

**START_COMMANDS.md** - Detailed command reference for all services with verification steps

**start_all.sh** - Automated script to start all services (Docker, backend, frontend, Ontop)

**stop_all.sh** - Automated script to stop all services and clear ports

**setup_docker_containers.sh** - Script to create and configure Docker containers for PostgreSQL and Neo4j

**.gitignore** - Git ignore rules to exclude venv, node_modules, logs, and other unnecessary files

---

### Data Pipeline (`rawdata_cleanupscripts/`)

**download_prices_clean.py** - Downloads stock price data from Yahoo Finance, cleans it, and outputs long-format CSV

**stock_prices_pg.csv** - Clean stock price data in long format (date, open, high, low, close, adj_close, volume, symbol)

---

### Backend (`chatbot/backend/`)

**app.py** - Main FastAPI application that handles chat requests, intent classification, Cypher generation, and answer synthesis

**graph.py** - Neo4j database connection and query execution functions with connection pooling

**llm.py** - OpenAI integration for Cypher query generation and natural language answer synthesis

**prompts.py** - Schema-safe prompt templates for LLM to generate valid Cypher queries and format answers

**intent_classifier.py** - Classifies user questions as data queries, conversational, clarification, or confirmation

**load_data_to_neo4j.py** - Loads stock price CSV data into Neo4j, creating Company and PriceDay nodes with HAS_PRICE relationships

**load_schema_extension.py** - Extends Neo4j schema by creating time dimension nodes (Year, Quarter, Month) and derived relationships (PERFORMED_IN, CORRELATED_WITH)

**gds_setup.py** - Sets up Graph Data Science algorithms: Node Similarity, PageRank, Community Detection, and FastRP Embeddings

**gds_setup.cypher** - Cypher script with all GDS algorithm definitions and verification queries

**schema_extension.cypher** - Cypher script defining extended schema with time dimensions and derived relationships

**test_gds_insights.py** - Test script to verify GDS outputs and how they improve GraphRAG answers

**import_n10s_ontology.py** - Imports RDF/OWL ontology into Neo4j using n10s plugin and maps existing nodes

**install_gds_docker.sh** - Installs Neo4j Graph Data Science plugin into Docker container

**install_n10s_docker.sh** - Installs n10s (neosemantics) RDF/OWL plugin into Neo4j Docker container

**setup_ontop_from_zip.sh** - Helper script to extract and set up Ontop CLI from downloaded ZIP file

**start_ontop.sh** - Starts Ontop Virtual Knowledge Graph endpoint for SPARQL queries over PostgreSQL

**stock_ontology.ttl** - RDF/OWL ontology file for n10s plugin defining stock data concepts

**stock_ontology_ontop.owl** - OWL ontology file for Ontop Virtual Knowledge Graph

**stock_mapping.obda** - OBDA mapping file that maps PostgreSQL stock_prices table to RDF/OWL concepts for Ontop

**stock_ontop.properties** - Properties file for Ontop with PostgreSQL connection details and file paths

**requirements.txt** - Python dependencies list (neo4j, fastapi, openai, pandas, etc.)

---

### Frontend (`chatbot/frontend/`)

**index.html** - Main HTML structure for the chatbot interface with welcome message and example questions

**app.js** - JavaScript code that handles user input, API calls to backend, message display, and conversation context

**style.css** - CSS styling for the chatbot interface with dark theme and responsive design

**package.json** - Package configuration with start script to run simple HTTP server on port 3001

---

### Quick File Purpose Summary

**Core Application:**
- `app.py` - Main API server
- `graph.py` - Database connection
- `llm.py` - AI integration
- `prompts.py` - Query generation prompts

**Data Loading:**
- `load_data_to_neo4j.py` - Initial data load
- `load_schema_extension.py` - Schema enrichment
- `gds_setup.py` - Graph analytics setup

**Frontend:**
- `index.html` - UI structure
- `app.js` - Frontend logic
- `style.css` - Styling

**Documentation:**
- `README.md` - Quick start
- `PROJECT_DOCUMENTATION.md` - Full technical docs
- `PRESENTATION_GUIDE.md` - Presentation script
- `MANUAL_COMMANDS.md` - Command reference

**Setup Scripts:**
- `start_all.sh` - Start everything
- `stop_all.sh` - Stop everything
- `setup_docker_containers.sh` - Docker setup

