# AI Governance

## ClubOps Copilot

ClubOps Copilot is a responsible assistant for operational questions over trusted club data. The local implementation is rule-based; the production design can use Azure OpenAI while preserving the same validation, semantic layer, logging, and refusal rules.

## RAG and Semantic Layer

The assistant uses `ai_assistant/semantic_layer.yml` as a compact semantic catalog:

- metric descriptions
- source tables
- owners
- allowed layers
- blocked topics
- default row limits

For production, embed metric docs, table descriptions, and dashboard definitions in a vector index. Retrieved context should be limited to governed Silver and Gold assets.

## Prompt Template

The prompt in `ai_assistant/prompt_template.md` instructs the assistant to:

- use only approved tables
- generate read-only SQL
- validate before execution
- explain metrics plainly
- refuse unsupported or sensitive questions
- show source tables

## SQL Validation Rules

Implemented in `ai_assistant/sql_validator.py`:

- Only `SELECT` statements.
- Tables must be allowlisted.
- DDL and DML keywords are blocked.
- Sensitive fan identifiers and birth dates require aggregation.
- Row limits are enforced.
- Source tables are extracted and returned.

## Evaluation Dataset

`ai_assistant/eval_dataset.jsonl` contains 30 questions covering:

- football operations
- commercial revenue
- fan segmentation
- campaign performance
- adoption and monitoring
- unsupported or sensitive requests

Metrics:

- answer accuracy
- SQL validity
- refusal precision
- source table citation coverage
- latency
- estimated cost per answer

## Cost Governance

- Log estimated tokens and cost per interaction.
- Enforce a daily budget from `COPILOT_DAILY_TOKEN_BUDGET_USD`.
- Cache repeated metric definitions.
- Prefer small aggregate queries over raw-row scans.
- Require user confirmation before expensive production queries.

