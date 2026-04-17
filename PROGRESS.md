# DataPilot Build Progress

## Stack
- Backend: Python FastAPI
- Frontend: Next.js (not started yet)
- Database: CSV -> DuckDB/Postgres later
- LLM: Anthropic Claude API
- OS: Windows

## Completed Steps
- [x] Step 1: GitHub repo created
- [x] Step 2: Folder structure created
- [x] Step 3: Python venv created and activated
- [x] Step 4: Core schemas defined (models/schemas.py)
- [x] Step 5: Metric registry built (registry/metric_registry.py)
- [x] Step 6: Synthetic data generated (data/analytics_data.csv)
- [x] Step 7: Query service built (services/query_service.py)
- [x] Step 8: All 6 evidence checks built
  - formula_sanity.py
  - numerator_denominator.py
  - segment_concentration.py
  - supporting_metrics.py
  - data_freshness.py
  - structural_anomaly.py

## Next Steps
- [ ] Step 9: Verdict engine + driver analysis engine
- [ ] Step 10: Narrative service (Claude API)
- [ ] Step 11: Investigation API endpoint
- [ ] Step 12: Wire everything together and test full flow
- [ ] Step 13: Next.js frontend
- [ ] Step 14: Deploy

## Key File Locations
- Backend entry point: backend/app/main.py
- Schemas: backend/app/models/schemas.py
- Metric registry: backend/app/registry/metric_registry.py
- Query service: backend/app/services/query_service.py
- Checks: backend/app/checks/
- Data: backend/data/analytics_data.csv

## Notes
- venv lives in backend/venv
- Activate venv: backend\venv\Scripts\activate
- Run server: uvicorn app.main:app --reload (from backend folder)
- Server runs on http://127.0.0.1:8000