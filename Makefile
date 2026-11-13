.PHONY: setup generate bronze transform quality pipeline api dashboard copilot test lint typecheck clean

setup:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

generate:
	python -m data_generator.generate --output data/landing --days 60 --fans 1500 --seed 7

bronze:
	python -m ingestion.load_bronze --landing-path data/landing --lakehouse-path lakehouse_local

transform:
	python -m transformations.run_transformations --lakehouse-path lakehouse_local

quality:
	python -m quality.run_checks --lakehouse-path lakehouse_local

pipeline:
	python -m orchestration.run_pipeline --days 60 --fans 1500

api:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

dashboard:
	streamlit run dashboard/app.py --server.port 8501

copilot:
	python -m ai_assistant.copilot "Which players have the lowest readiness this week?"

test:
	pytest

lint:
	ruff check .

typecheck:
	mypy .

clean:
	python -m orchestration.clean_local

