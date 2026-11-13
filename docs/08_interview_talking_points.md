# Interview Talking Points

## Why did you choose this problem?

Football clubs have high-value decisions across sporting and commercial operations, but data often lives in separate systems. This project shows I can turn ambiguous operational needs into trusted, reusable data products.

## How did you handle ambiguity?

I started with stakeholder personas, daily workflows, pain points, and success metrics. Then I worked backwards into datasets, marts, APIs, dashboards, and monitoring.

## How did you work backwards from stakeholder needs?

Each Gold table maps to a decision: readiness, matchday revenue, fan segmentation, campaign performance, and adoption. The dashboard pages and API endpoints follow the same structure.

## How did you design for reuse?

I used shared dimensions, clear table grains, standard ingestion metadata, quality checks, and reusable monitoring patterns. The same ingestion and validation patterns apply across football, commercial, fan, and corporate domains.

## How did you balance speed and maintainability?

The MVP runs locally with simple commands and no cloud credentials. The architecture still maps cleanly to Databricks, Delta, Lakeflow Jobs, Unity Catalog, and MLflow.

## How did you apply AI responsibly?

ClubOps Copilot only uses trusted tables, validates SQL, refuses unsupported or sensitive questions, logs source tables, tracks latency and estimated cost, and includes an evaluation set.

## How did you measure adoption and impact?

I modeled product adoption events, workflow events, active users, sessions, Copilot queries, and estimated minutes saved. The product is judged by changed workflows, not only completed pipelines.

## How would you productionize this on Azure Databricks?

Use ADLS Gen2 for landing and lakehouse storage, Delta tables for Bronze/Silver/Gold, Lakeflow Jobs for orchestration, Unity Catalog for governance, Databricks SQL or serving endpoints for consumption, MLflow for models, Key Vault for secrets, and GitHub Actions or Databricks Asset Bundles for deployment.

## What would you improve with real club data?

I would calibrate readiness signals with practitioner input, integrate vendor APIs, improve identity resolution, add privacy-preserving fan modeling, expand forecast features, and validate business impact with real adoption telemetry.

