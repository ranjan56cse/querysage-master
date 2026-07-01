---
name: querysage-sql
description: Generates PostgreSQL SELECT queries from natural language business questions. Use when the user asks about data, metrics, reports, or analytics from a Neon Postgres database.
---

# QuerySage SQL Generation Skill

## Goal
Convert natural language business questions into valid PostgreSQL SELECT queries.

## Instructions
1. Analyze the user's natural language question to identify entities, metrics, filters.
2. Read the database schema from the Neon MCP connection.
3. Apply ontology rules from config/ontology.yaml.
4. Match against few-shot examples from config/few_shot_examples.yaml.
5. Generate a PostgreSQL SELECT query — ONLY SELECT, never mutations.
6. If the query fails, self-correct up to 3 times using error messages.

## Constraints
- Never generate DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE
- Always use table aliases for clarity
- Limit results to 1000 rows unless user specifies otherwise
