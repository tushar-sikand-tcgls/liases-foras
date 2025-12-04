# Neo4J Setup Guide

This guide explains how to set up Neo4J for the Liases Foras Knowledge Graph.

## Quick Start with Docker (Recommended)

### Prerequisites
- Docker installed and running
- Colima (for macOS with Apple Silicon)

### Start Neo4J Container

```bash
# Make sure Docker/Colima is running
colima start

# Run Neo4J container
docker run -d \
  --name neo4j-lf \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/liasesforas123 \
  neo4j:latest

# Wait for Neo4J to start (check logs)
docker logs -f neo4j-lf
```

### Load Data into Neo4J

```bash
# Set environment variables
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="liasesforas123"

# Run the loader script
python3 scripts/load_to_neo4j.py
```

Expected output:
```
============================================================
NEO4J KNOWLEDGE GRAPH LOADER
============================================================

Loading data from: /Users/.../lf_projects_layer0.json
✓ Loaded 10 projects

Connecting to Neo4J at bolt://localhost:7687...

Creating indexes...
✓ Indexes created

Loading projects into knowledge graph...
  1. Sara City
  2. Pradnyesh Shriniwas
  3. Sara Nilaay
  ...
  10. Shubhan Karoti

============================================================
LOAD COMPLETE
============================================================

Database Statistics:
  Projects: 10
  Developers: 8
  Locations: 2
  Layer 1 Metrics: 10
```

## Alternative: Neo4J Desktop

### 1. Download Neo4J Desktop
- Visit: https://neo4j.com/download/
- Download Neo4J Desktop for macOS

### 2. Create a New Database
- Open Neo4J Desktop
- Click "New" → "Create Project"
- Name: "Liases Foras"
- Click "Add" → "Local DBMS"
- Set password: `liasesforas123`
- Version: 5.x (latest)
- Click "Create"

### 3. Start the Database
- Click "Start" button
- Wait for status to show "Active"

### 4. Configure Connection
```bash
# Set environment variables
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="liasesforas123"
```

### 5. Load Data
```bash
python3 scripts/load_to_neo4j.py
```

## Verify Installation

### Check Neo4J Browser
- Open: http://localhost:7474
- Login with credentials: neo4j / liasesforas123
- Run query:

```cypher
MATCH (p:Project)-[:DEVELOPED_BY]->(d:Developer)
MATCH (p)-[:LOCATED_IN]->(l:Location)
RETURN p, d, l
LIMIT 10
```

### Query Sara City Data

```cypher
MATCH (p:Project {name: "Sara City"})-[:DEVELOPED_BY]->(d:Developer)
MATCH (p)-[:LOCATED_IN]->(l:Location)
OPTIONAL MATCH (p)-[:HAS_METRIC_L1]->(m:Metric_L1)
RETURN p, d, l, m
```

Expected result:
- Project: Sara City
- Developer: Sara Builders & Developers (Sara Group)
- Location: Chakan
- Total Units: 1,109
- Total Area: 550,125 sqft
- Current Price PSF: ₹3,996

## Troubleshooting

### Docker Connection Issues

If you see "Cannot connect to Docker daemon":

```bash
# Fix 1: Restart Colima
colima stop
colima start

# Fix 2: Reset Colima
colima delete
colima start --cpu 2 --memory 4

# Fix 3: Use Docker Desktop instead
# Download from https://www.docker.com/products/docker-desktop/
```

### Port Already in Use

```bash
# Stop existing Neo4J container
docker stop neo4j-lf
docker rm neo4j-lf

# Check what's using port 7687
lsof -i :7687

# If needed, kill the process
kill -9 <PID>
```

### Connection Timeout

```bash
# Check if Neo4J is running
docker ps | grep neo4j

# Check Neo4J logs
docker logs neo4j-lf

# Restart container if needed
docker restart neo4j-lf
```

## Next Steps

Once Neo4J is running and data is loaded:

1. **Access Neo4J Browser**: http://localhost:7474
2. **View Knowledge Graph**: Use the graph visualization in the 3-dots dropdown menu in the Streamlit app
3. **Query Projects**: Use the Analytics AI Chat to query project data
4. **Explore Relationships**: Navigate the graph to see Project → Developer → Location connections

## Knowledge Graph Schema

### Nodes
- `(:Project)` - Real estate projects with Layer 0 properties (U, L², T, CF)
- `(:Developer)` - Property developers/builders
- `(:Location)` - Geographic locations/micro-markets
- `(:Metric_L1)` - Derived Layer 1 metrics (PSF, ASP, Absorption Rate)

### Relationships
- `(Project)-[:DEVELOPED_BY]->(Developer)` - Project to developer relationship
- `(Project)-[:LOCATED_IN]->(Location)` - Project location
- `(Project)-[:HAS_METRIC_L1]->(Metric_L1)` - Project to calculated metrics

## Configuration

### Environment Variables

Add to `.env` file:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=liasesforas123
```

### Python Requirements

Ensure `neo4j` package is installed:

```bash
pip install neo4j==5.28.1
```

## Support

For issues:
- Neo4J Documentation: https://neo4j.com/docs/
- Neo4J Community: https://community.neo4j.com/
- Colima Issues: https://github.com/abiosoft/colima/issues
