# Comprehensive Query Examples

## LLM-Powered Query Processor - All Supported Operations

The LLM understands SQL-like queries and translates them to Cypher dynamically.

---

## 1. Basic Aggregations

### Average/Mean
```
"Calculate the average of project size"
"What is the mean area?"
"Average revenue across all projects"
```

**LLM Understanding:**
```json
{
  "aggregation": "average",
  "dimension": "U",
  "neo4j_field": "totalUnits"
}
```

**Generated Cypher:**
```cypher
MATCH (p:Project)
RETURN avg(p.totalUnits) AS result, collect(p.totalUnits) AS values
```

### Sum/Total
```
"What is the total revenue?"
"Sum of all areas"
"Total units across projects"
```

### Statistical Operations
```
"Calculate median project size"
"What is the standard deviation of revenue?"
"Find the variance in project duration"
"Show me quartiles for area distribution"
```

---

## 2. Filtering Operations

### Top N
```
"Show me the top 5 projects by revenue"
"Top 10 largest projects"
"Which are the 3 biggest projects by area?"
```

**LLM Understanding:**
```json
{
  "aggregation": null,
  "filter_type": "top_n",
  "filter_value": 5,
  "sort_field": "totalRevenue",
  "sort_order": "descending"
}
```

**Generated Cypher:**
```cypher
MATCH (p:Project)
RETURN p.projectName, p.totalRevenue
ORDER BY p.totalRevenue DESC
LIMIT 5
```

### Bottom N
```
"Show me the bottom 5 projects by units"
"Which are the smallest 3 projects?"
"Lowest revenue projects, top 10"
```

### Comparison Filters
```
"Projects with revenue greater than 100 crore"
"Units less than 50"
"Revenue between 50 and 200 crore"
```

**Generated Cypher:**
```cypher
MATCH (p:Project)
WHERE p.totalRevenue > 1000000000
RETURN p.projectName, p.totalRevenue
```

---

## 3. Sorting Operations

```
"Sort all projects by revenue descending"
"Order by project size ascending"
"Show projects sorted by duration, largest first"
```

**Generated Cypher:**
```cypher
MATCH (p:Project)
RETURN p.projectName, p.totalUnits
ORDER BY p.totalUnits DESC
```

---

## 4. Grouping Operations

```
"Average project size by city"
"Total revenue grouped by location"
"Count of projects by developer"
"Mean area per micro-market"
```

**LLM Understanding:**
```json
{
  "aggregation": "average",
  "group_by": "city",
  "neo4j_field": "totalUnits"
}
```

**Generated Cypher:**
```cypher
MATCH (p:Project)
RETURN p.city AS city, avg(p.totalUnits) AS avg_units
ORDER BY avg_units DESC
```

---

## 5. Date Range Queries

```
"Projects launched in 2024"
"Revenue from Q3 projects"
"Projects between Jan 2024 and Jun 2024"
"Show me projects launched this year"
```

**Generated Cypher:**
```cypher
MATCH (p:Project)
WHERE p.launchDate >= date('2024-01-01')
  AND p.launchDate < date('2025-01-01')
RETURN p.projectName, p.launchDate, p.totalRevenue
```

---

## 6. Combined Operations

### Top N + Grouping
```
"Top 5 cities by average project size"
"Best 3 developers by total revenue"
"Which locations have the highest median PSF? Top 10"
```

**Generated Cypher:**
```cypher
MATCH (p:Project)
WITH p.city AS city, avg(p.totalUnits) AS avg_units
RETURN city, avg_units
ORDER BY avg_units DESC
LIMIT 5
```

### Filter + Sort + Limit
```
"Top 5 projects with revenue greater than 100 crore, sorted by size"
"Largest 10 projects in Pune, ordered by revenue"
```

**Generated Cypher:**
```cypher
MATCH (p:Project)
WHERE p.totalRevenue > 1000000000 AND p.city = 'Pune'
RETURN p.projectName, p.totalRevenue, p.totalUnits
ORDER BY p.totalRevenue DESC
LIMIT 10
```

### Date Range + Aggregation + Grouping
```
"Average project size by city for projects launched in 2024"
"Total revenue per developer in Q3 2024"
```

---

## 7. Distribution Analysis

```
"Show me the distribution of project sizes"
"Revenue distribution across all projects"
"Create a histogram of project durations"
```

**Generated Cypher:**
```cypher
MATCH (p:Project)
WITH p.totalUnits AS value
ORDER BY value
RETURN collect(value) AS values,
       count(value) AS count,
       min(value) AS min_value,
       max(value) AS max_value,
       avg(value) AS mean,
       stdev(value) AS stdev,
       percentileCont(value, 0.25) AS q1,
       percentileCont(value, 0.5) AS median,
       percentileCont(value, 0.75) AS q3
```

---

## 8. Complex Statistical Queries

```
"Find outliers in project revenue"
"What is the coefficient of variation for project sizes?"
"Show me the interquartile range of areas"
"Calculate skewness of revenue distribution"
```

---

## Response Format

All queries return:

```json
{
  "status": "success",
  "query": "Original user query",
  "understanding": {
    "layer": 0,
    "dimension": "U",
    "aggregation": "average",
    "filter_type": "top_n",
    "filter_value": 5,
    "sort_order": "descending",
    "group_by": "city"
  },
  "result": {
    "value": 90.0,
    "unit": "Units",
    "text": "90.0 Units"
  },
  "calculation": {
    "formula": "X = Σ U / 3",
    "breakdown": [...],
    "projectCount": 3
  },
  "provenance": {
    "cypherQuery": "MATCH (p:Project)...",
    "llmModel": "gemini-1.5-flash",
    "dataSource": "Liases Foras"
  }
}
```

---

## Key Points

1. **No Hardcoding:** LLM reads schema and understands dynamically
2. **SQL-Like:** Think SQL - group by, order by, where, limit
3. **Extensible:** Add new operations by updating schema
4. **Flexible:** Understands various phrasings
5. **Transparent:** Returns complete provenance and Cypher query
