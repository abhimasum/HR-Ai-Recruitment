# AI HR Recruitment System

Learning project for an AI-assisted recruitment workflow: job management, resume screening (LangGraph),
human-in-the-loop review, DeepEval quality metrics, and a manually built policy RAG assistant
(pgvector + LangGraph).

## Run locally

    cp .env.example .env        # add your OPENAI_API_KEY
    docker compose up --build

- Frontend (production build served by Nginx): http://localhost:5173
- Backend API docs: http://localhost:8000/docs
- Policy chat: POST /api/v1/chat/policy  {"question": "What is the remote work policy?"}
- Jobs API: GET/POST /api/v1/jobs; update/archive at /api/v1/jobs/{id}

## Deploy to GCP

The GitHub Actions workflow at `.github/workflows/deploy-gcp.yml` provisions the GCP resources
with Terraform, deploys both Cloud Run services, and smoke tests the live frontend and API.
For project `hr-ai-recruitment` (number `278189990066`), run these commands in PowerShell:

    gcloud auth login abhimasum2@gmail.com
    gh auth login
    .\infra\terraform\gcp\setup-github-actions.ps1

The script sets up keyless GitHub authentication and the repo variables/secrets. Review billing,
then run the workflow manually from GitHub Actions. See
[infra/terraform/README.md](./infra/terraform/README.md).

## Tests

With the backend requirements installed, run from the `backend` directory:

    python -m unittest discover -s tests

## Structure

- backend/app/api/v1/endpoints/jobs.py: create, update, list, and archive open positions
- backend/app/api/v1/endpoints/candidates.py and review.py: resume screening, candidate listing, and HR decisions
- backend/app/workflows/rag_graph.py: guardrail, retrieve, grade, rewrite, generate, hallucination check
- backend/app/workflows/screening_graph.py: score and route to AUTO_ACCEPTED / PENDING_HUMAN_REVIEW / AUTO_REJECTED
- backend/app/db/vector_store.py: custom pgvector search (cosine via <=>)
- backend/app/seed/hr_policies.py: seeds sample HR policies on startup (RecursiveCharacterTextSplitter 500/50)
- backend/app/seed/jobs.py: seeds example roles for local learning and demos
- backend/app/evaluation/deepeval_runner.py: GEval, Hallucination, and Bias metrics, logged to Postgres
- frontend/src: candidate application/policy chat and HR candidate review/job management
- infra/terraform/gcp: Cloud Run frontend/backend and Cloud SQL PostgreSQL with pgvector

## Assumptions

- LLM and embeddings use OpenAI by default; set `LLM_PROVIDER=vertexai` and
  `EMBEDDING_PROVIDER=vertexai` to use Gemini and Vertex AI embeddings on GCP.
- Thresholds follow the coding brief: score > 80 is AUTO_ACCEPTED, 60-80 is
  PENDING_HUMAN_REVIEW, and score < 60 is AUTO_REJECTED (set in `.env`).
- The GCP GitHub Actions workflow applies the Terraform infrastructure after its validation job.
- This is a learning project: authentication, tenant isolation, and production handling of candidate
  personal data are not implemented. Do not expose the HR review API publicly or use real candidate data.
- DeepEval failures are recorded in evaluation details and logged; metrics may be null when an evaluator
  or its provider is unavailable.
