# Local development. Requires the organizers' dataset mirror (see CLAUDE.md) for `make data`.
PY := backend/.venv/bin/python

.PHONY: setup data model eval eval-llm test api web dev

setup:            ## create the Python venv and install both apps
	python3 -m venv backend/.venv
	$(PY) -m pip install -q -e "backend[dev]"
	cd frontend && npm install

data:             ## build the Parquet warehouse and quality report from the local mirror
	cd backend && .venv/bin/python -m app.data.build

model:            ## train and compare fraud-risk models (MLflow), write backend/data/models/
	cd backend && MLFLOW_DISABLE_AGENT_HINT=1 .venv/bin/python -m app.ml.fraud

eval:             ## build dev/test case sets and evaluate in rules mode (free), then write docs/evaluation.md
	cd backend && .venv/bin/python -m app.eval.cases --seed 7 --name dev && .venv/bin/python -m app.eval.cases --seed 8 --name test-seen \
	  && .venv/bin/python -m app.eval.cases --seed 9 --heldout --name test-heldout
	cd backend && for s in dev test-seen test-heldout; do LLM_DISABLED=1 .venv/bin/python -m app.eval.run --mode rules --cases $$s > /dev/null; done
	cd backend && .venv/bin/python -m app.eval.report

eval-llm:         ## evaluate both test sets with Claude (costs about $1 per set), then rewrite the report
	cd backend && for s in test-seen test-heldout; do .venv/bin/python -m app.eval.run --mode llm --cases $$s > /dev/null; done
	cd backend && .venv/bin/python -m app.eval.report

test:             ## workflow tests (rules only, no LLM calls)
	cd backend && .venv/bin/python -m pytest -q

api:              ## API on http://127.0.0.1:8000
	cd backend && .venv/bin/python -m uvicorn app.api.main:app --reload --port 8000

web:              ## React dev server on http://localhost:5173 (proxies /api to :8000)
	cd frontend && npm run dev

dev:              ## API and web together
	$(MAKE) -j2 api web
