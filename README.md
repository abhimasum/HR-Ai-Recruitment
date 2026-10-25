# AI HR Recruitment System

Multi-tenant-ready HR recruitment platform with resume screening (LangGraph), human-in-the-loop review,
DeepEval quality metrics, and a manually built Agentic RAG policy assistant (pgvector + LangGraph).

## Run locally

    cp .env.example .env        # add your OPENAI_API_KEY
    docker compose up --build

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs
- Policy chat: POST /api/v1/chat/policy  {"question": "What is the remote work policy?"}

## Structure

- backend/app/workflows/rag_graph.py: guardrail, retrieve, grade, rewrite, generate, hallucination check
- backend/app/workflows/screening_graph.py: score and route to AUTO_ACCEPTED / PENDING_HUMAN_REVIEW / AUTO_REJECTED
- backend/app/db/vector_store.py: custom pgvector search (cosine via <=>)
- backend/app/seed/hr_policies.py: seeds sample HR policies on startup (RecursiveCharacterTextSplitter 500/50)
- backend/app/evaluation/deepeval_runner.py: GEval, Hallucination, and Bias metrics, logged to Postgres
- frontend/src: candidate view (upload + policy chat) and HR portal (scores, metrics, Approve/Reject)
- infra/terraform: multi-cloud IaC plan (not yet implemented)

## Assumptions

- LLM and embeddings use OpenAI. Swap in HuggingFaceEmbeddings in vector_store.py to run without a key.
- Thresholds: score >= 80 AUTO_ACCEPTED, 50 to 79 PENDING_HUMAN_REVIEW, < 50 AUTO_REJECTED (set in .env).
- Terraform for AWS, GCP, and Azure is a documented plan, not yet written.
- Auth, multi-tenancy isolation, and tests are not included in this first version.
