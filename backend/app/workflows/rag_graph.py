"""Agentic RAG loop built manually with LangGraph.

guardrail -> retrieve -> grade -> (rewrite -> retrieve)* -> generate -> hallucination_check
"""
from typing import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.db.vector_store import similarity_search

llm = ChatOpenAI(model=settings.llm_model, api_key=settings.openai_api_key or None, temperature=0)

MAX_REWRITES = 2
REFUSAL_MESSAGE = (
    "I can only help with questions about HR policies, the recruitment process, and life at "
    "the company, such as leave, remote work, benefits, interview stages, and culture. "
    "Please ask a question in one of those areas."
)
FALLBACK_MESSAGE = (
    "I could not find a clear answer to that in our policy documents. "
    "Please contact the HR team for help."
)


class RAGState(TypedDict, total=False):
    original_question: str
    question: str
    in_scope: bool
    documents: list[dict]
    relevant: bool
    retries: int
    answer: str
    grounded: bool
    sources: list[str]


def _is_yes(text: str) -> bool:
    return text.strip().upper().startswith("YES")


def _context(documents: list[dict]) -> str:
    return "\n---\n".join(d["content"] for d in documents)


async def guardrail_node(state: RAGState) -> dict:
    prompt = (
        "Decide whether the question is about HR policies, recruitment procedures, or life at the "
        "company (leave, benefits, remote work, interviews, culture, work environment). "
        "Reply with exactly YES or NO.\n\nQuestion: " + state["question"]
    )
    result = await llm.ainvoke(prompt)
    return {"in_scope": _is_yes(result.content)}


def route_guardrail(state: RAGState) -> str:
    return "retrieve" if state["in_scope"] else "refuse"


async def refuse_node(state: RAGState) -> dict:
    return {"answer": REFUSAL_MESSAGE, "sources": [], "grounded": True}


async def retrieve_node(state: RAGState) -> dict:
    return {"documents": await similarity_search(state["question"])}


async def grade_node(state: RAGState) -> dict:
    prompt = (
        f"Question: {state['question']}\n\nRetrieved excerpts:\n{_context(state['documents'])}\n\n"
        "Are these excerpts relevant enough to answer the question? Reply YES or NO."
    )
    result = await llm.ainvoke(prompt)
    return {"relevant": _is_yes(result.content)}


def route_grade(state: RAGState) -> str:
    if state["relevant"] or state.get("retries", 0) >= MAX_REWRITES:
        return "generate"
    return "rewrite"


async def rewrite_node(state: RAGState) -> dict:
    result = await llm.ainvoke(
        "Rewrite this employee question so it better matches formal HR policy wording. "
        "Return only the rewritten question.\n\n" + state["question"]
    )
    return {"question": result.content.strip(), "retries": state.get("retries", 0) + 1}


async def generate_node(state: RAGState) -> dict:
    prompt = (
        "Answer the question using ONLY the context below. If the context does not contain the "
        "answer, say that you do not have that information.\n\n"
        f"Context:\n{_context(state['documents'])}\n\n"
        f"Question: {state['original_question']}"
    )
    result = await llm.ainvoke(prompt)
    sources = sorted({d["source"] for d in state["documents"]})
    return {"answer": result.content, "sources": sources}


async def hallucination_node(state: RAGState) -> dict:
    prompt = (
        f"Context:\n{_context(state['documents'])}\n\nAnswer:\n{state['answer']}\n\n"
        "Is every factual claim in the answer supported by the context? Reply YES or NO."
    )
    result = await llm.ainvoke(prompt)
    grounded = _is_yes(result.content)
    return {
        "grounded": grounded,
        "answer": state["answer"] if grounded else FALLBACK_MESSAGE,
    }


builder = StateGraph(RAGState)
builder.add_node("guardrail", guardrail_node)
builder.add_node("refuse", refuse_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("grade", grade_node)
builder.add_node("rewrite", rewrite_node)
builder.add_node("generate", generate_node)
builder.add_node("hallucination", hallucination_node)

builder.set_entry_point("guardrail")
builder.add_conditional_edges("guardrail", route_guardrail, {"retrieve": "retrieve", "refuse": "refuse"})
builder.add_edge("refuse", END)
builder.add_edge("retrieve", "grade")
builder.add_conditional_edges("grade", route_grade, {"generate": "generate", "rewrite": "rewrite"})
builder.add_edge("rewrite", "retrieve")
builder.add_edge("generate", "hallucination")
builder.add_edge("hallucination", END)

rag_graph = builder.compile()


async def answer_policy_question(question: str) -> dict:
    final = await rag_graph.ainvoke({
        "original_question": question,
        "question": question,
        "retries": 0,
    })
    return {
        "answer": final["answer"],
        "sources": final.get("sources", []),
        "grounded": final.get("grounded", False),
    }
