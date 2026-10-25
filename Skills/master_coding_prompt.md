# Master Coding Prompt: AI HR Recruitment & Agentic RAG System

## 1. Context & Overview
You are an expert full-stack engineer, AI system architect, and cloud engineer. Build a multi-tenant AI HR Recruitment System featuring:
1. Automated resume parsing & Job Description (JD) matching.
2. A Human-in-the-Loop (HITL) screening workflow.
3. Automated LLM output evaluation using **DeepEval**.
4. A custom **Agentic RAG Pipeline** built manually (without managed RAG services) to answer candidate queries strictly regarding HR policies, recruitment procedures, and life at the company.
5. Interactive React UI (HR Portal + Candidate Screening & Policy Chat View).
6. A multi-cloud deployment setup (AWS, GCP, Azure).

The backend orchestration MUST rely strictly on **LangChain** and **LangGraph**.

---

## 2. Strictly Specified Tech Stack

### Frontend
- **Framework:** React (TypeScript, Vite)
- **Styling:** Tailwind CSS, Lucide Icons
- **HTTP Client:** Axios / React Query

### Backend Framework & AI Engine
- **Framework:** Python (FastAPI, Pydantic v2, Uvicorn)
- **Agent & Flow Orchestration:** **LangGraph** (State graphs, conditional routing, loopbacks, tools)
- **LLM / Prompting / Chains:** **LangChain** (LangChain Core, LangChain Community, Text Splitters, Embeddings, Chat Models)
- **LLM Evaluation:** **DeepEval** (GEval, Hallucination, and Bias metrics)
- **File Parsing Utilities:** `pypdf`/`pdfplumber` (PDFs), `python-docx` (DOCX)

### Custom Vector Store & Database
- **Database:** PostgreSQL with `pgvector` extension enabled
- **Vector Search:** Custom PGVector implementation using LangChain's `PGVector` store or direct SQLAlchemy `pgvector` queries (no managed vector databases like Pinecone/Weaviate)
- **ORM:** SQLAlchemy / SQLModel (Async Engine)

### Infrastructure & Deployment
- **Containers:** Docker, Docker Compose
- **IaC:** Terraform configurations targeting **AWS** (ECS Fargate/Aurora), **GCP** (Cloud Run/Cloud SQL), and **Azure** (App Service/Azure DB for Postgres)

---

## 3. Core Functional Requirements & Logic

### A. Resume Screening Engine Rules (LangGraph)
Calculate an overall match score ($S$) between $0\%$ and $100\%$:
1. **Condition 1 ($S > 80\%$):** 
   - Status: `AUTO_ACCEPTED`
2. **Condition 2 ($60\% \le S \le 80\%$):** 
   - Status: `PENDING_HUMAN_REVIEW` (Triggers Human-in-the-Loop review for HR)
3. **Condition 3 ($S < 60\%$):** 
   - Status: `AUTO_REJECTED`

### B. Agentic RAG & Candidate Policy Chat (Custom Built)
Build a manual Agentic RAG workflow in **LangGraph** for candidate Q&A:
1. **Scope Restriction & Guardrails:**
   - The RAG agent must ONLY answer questions related to **HR Policies**, **Recruitment Processes**, and **Life at the Company** (e.g., leave policies, remote work, benefits, interview stages, company culture).
   - Off-topic questions (e.g., general coding help, math, external knowledge) MUST be politely declined with a domain guardrail refusal message.
2. **Manual Pipeline Strategy (Self-Correction / Agentic Loop):**
   - **Node 1 (`QuestionGuardrailCheck`):** Classify if the candidate's query pertains to HR/Recruitment/Company Life.
   - **Node 2 (`RetrieveDocuments`):** Search Postgres `pgvector` store using cosine similarity for sample HR policy documents chunked via `RecursiveCharacterTextSplitter`.
   - **Node 3 (`GradeRelevance`):** LLM node checking if retrieved chunks are relevant to the query. If irrelevant, trigger a query rewrite.
   - **Node 4 (`GenerateAnswer`):** Synthesize answer strictly based on retrieved context.
   - **Node 5 (`HallucinationCheck`):** Ensure generated response is grounded in retrieved chunks.

---

## 4. Architectural Layout & File Tree

Generate the codebase structured exactly as follows:

```
/ai-hr-recruitment-system
├── /backend
│   ├── /app
│   │   ├── /api
│   │   │   └── /v1
│   │   │       ├── endpoints/
│   │   │       │   ├── jobs.py
│   │   │       │   ├── candidates.py
│   │   │       │   ├── review.py
│   │   │       │   └── chat.py         # Candidate Policy Chat Endpoint
│   │   │       └── router.py
│   │   ├── /core
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── /data
│   │   │   └── sample_hr_policies.json  # Seed policy docs (Leave, Benefits, Culture)
│   │   ├── /evals
│   │   │   └── deepeval_runner.py
│   │   ├── /models
│   │   │   ├── job.py
│   │   │   ├── candidate.py
│   │   │   └── policy_vector.py
│   │   ├── /workflows
│   │   │   ├── screening_graph.py     # LangGraph for resume screening
│   │   │   ├── rag_graph.py           # LangGraph for Agentic Policy Chat RAG
│   │   │   ├── nodes.py               # Shared processing nodes
│   │   │   └── state.py               # ScreeningState & RAGState
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── /frontend
│   ├── /src
│   │   ├── /components
│   │   │   ├── HRDashboard.tsx
│   │   │   ├── CandidateUpload.tsx
│   │   │   ├── CandidatePolicyChat.tsx # UI chat widget for candidates
│   │   │   ├── ReviewModal.tsx
│   │   │   └── Layout.tsx
│   │   ├── /services
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   └── package.json
└── /infra
    ├── /terraform
    │   ├── /aws/main.tf
    │   ├── /gcp/main.tf
    │   └── /azure/main.tf
    └── docker-compose.yml
```

---

## 5. Implementation Code Specifications

### Step 1: Database Setup & Seed HR Policies
1. Enable `pgvector` in PostgreSQL: `CREATE EXTENSION IF NOT EXISTS vector;`.
2. Seed sample HR documents into Postgres vector table on startup:
   - **Sample Topics:** Work From Home Policy, Paid Leave Policy, Health Insurance, Hiring Pipeline Steps, Diversity & Life at Company.
3. Use LangChain's `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)` and `OpenAIEmbeddings` / `HuggingFaceEmbeddings` to populate vector tables in Postgres.

### Step 2: Agentic RAG Flow Definition (`backend/app/workflows/rag_graph.py`)

Implement the Agentic RAG loop using LangGraph and LangChain components:

```python
from typing import TypedDict, List, Literal, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import PGVector

# 1. State Definition
class RAGState(TypedDict):
    question: str
    is_hr_related: bool
    documents: List[Document]
    generation: str
    relevance_score: str
    retry_count: int

# 2. Node Implementations
llm = ChatOpenAI(model="gpt-4o", temperature=0)

def guardrail_node(state: RAGState) -> Dict[str, Any]:
    """Node 1: Classify if question is within HR / Recruitment / Life at Company scope."""
    prompt = f"""
    Determine if the following user question is related ONLY to HR policies, leave/benefits, 
    recruitment processes, or life at company.
    
    Question: {state['question']}
    
    Respond strictly with 'YES' or 'NO'.
    """
    res = llm.invoke(prompt).content.strip().upper()
    return {"is_hr_related": "YES" in res}

def retrieve_node(state: RAGState, vectorstore: PGVector) -> Dict[str, Any]:
    """Node 2: Retrieve relevant policy chunks from Postgres pgvector."""
    docs = vectorstore.similarity_search(state["question"], k=3)
    return {"documents": docs}

def grade_documents_node(state: RAGState) -> Dict[str, Any]:
    """Node 3: Filter retrieved documents for direct relevance."""
    relevant_docs = []
    for doc in state["documents"]:
        prompt = f"""
        Is the document snippet relevant to the question?
        Document: {doc.page_content}
        Question: {state['question']}
        Respond with 'YES' or 'NO'.
        """
        if "YES" in llm.invoke(prompt).content.strip().upper():
            relevant_docs.append(doc)
            
    relevance = "RELEVANT" if len(relevant_docs) > 0 else "NOT_RELEVANT"
    return {"documents": relevant_docs, "relevance_score": relevance}

def generate_answer_node(state: RAGState) -> Dict[str, Any]:
    """Node 4: Synthesize answer based strictly on retrieved context."""
    context = "\n\n".join([d.page_content for d in state["documents"]])
    prompt = f"""
    Answer the candidate's question using ONLY the provided HR policy context.
    If context is insufficient, state that you don't have that specific policy details.

    Context:
    {context}

    Question: {state['question']}
    """
    res = llm.invoke(prompt).content
    return {"generation": res}

def refusal_node(state: RAGState) -> Dict[str, Any]:
    """Guardrail refusal for off-topic questions."""
    return {
        "generation": "I am an HR Assistant. I can only answer questions related to HR policies, recruitment processes, and life at our company. Please ask an HR-related question."
    }

# 3. Router Decisions
def route_guardrail(state: RAGState) -> Literal["retrieve", "refusal"]:
    return "retrieve" if state["is_hr_related"] else "refusal"

def route_relevance(state: RAGState) -> Literal["generate", "refusal"]:
    if state["relevance_score"] == "RELEVANT":
        return "generate"
    return "refusal"

# 4. Graph Construction
def build_rag_graph(vectorstore: PGVector):
    workflow = StateGraph(RAGState)

    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("retrieve", lambda s: retrieve_node(s, vectorstore))
    workflow.add_node("grade_docs", grade_documents_node)
    workflow.add_node("generate", generate_answer_node)
    workflow.add_node("refusal", refusal_node)

    workflow.set_entry_point("guardrail")
    workflow.add_conditional_edges("guardrail", route_guardrail, {"retrieve": "retrieve", "refusal": "refusal"})
    workflow.add_edge("retrieve", "grade_docs")
    workflow.add_conditional_edges("grade_docs", route_relevance, {"generate": "generate", "refusal": "refusal"})
    workflow.add_edge("generate", END)
    workflow.add_edge("refusal", END)

    return workflow.compile()
```

### Step 3: Fast API Chat Endpoint (`backend/app/api/v1/endpoints/chat.py`)
- `POST /api/v1/chat/policy`: Accepts `{ "question": "What is the policy for working from home?" }`. Executes `rag_graph.ainvoke(...)` and returns the generated answer + retrieved policy source references.

### Step 4: React UI Updates
1. **Candidate View:**
   - **Tab 1: Apply / Upload Resume:** Drag-and-drop resume loader + JD Selector.
   - **Tab 2: Candidate Policy Assistant:** A clean messaging chat window allowing candidates to ask questions about company culture, leave policies, interview processes, and work environment. Includes pre-set prompt chips (e.g., *"What is the remote work policy?"*, *"How many paid leaves do I get?"*, *"What are the recruitment stages?"*).
2. **HR Portal View:**
   - Dashboard showing screening scores, DeepEval quality metrics, match reasoning, and HITL action buttons (`Approve` / `Reject`).

---

## 6. Acceptance Criteria
1. **RAG Scope Restriction:** Non-HR questions (e.g., *"Write a Python script"* or *"Who is the president?"*) are blocked at Node 1 (`guardrail_node`) and return the domain restriction message.
2. **Manual RAG Implementation:** Vector search and document grading are executed via custom LangGraph loops without managed third-party RAG SaaS platforms.
3. **Resume Screening Workflow:** $80\%/60-80\%/<60\%$ score logic routes candidate resumes correctly to `AUTO_ACCEPTED`, `PENDING_HUMAN_REVIEW`, or `AUTO_REJECTED`.
4. **DeepEval Validation:** Every screening evaluation logs GEval, Hallucination, and Bias metrics into PostgreSQL.
5. **Multi-Cloud Target:** Containers build cleanly via `docker-compose` and Terraform configs deploy to AWS, GCP, and Azure.