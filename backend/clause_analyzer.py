"""
LangChain + Groq (Llama 3.3 70B) orchestration layer.

RAG Q&A:    LangChain LCEL chain — retriever | prompt | ChatGroq | StrOutputParser
Risk report: Agentic tool-use loop — ChatGroq.bind_tools → collect structured findings
"""

from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import tool
from langchain_groq import ChatGroq

GROQ_MODEL = "llama-3.3-70b-versatile"

ANALYSIS_SYSTEM = """You are ClauseGuard, an expert legal contract analyst specializing in risk identification.

Analyze contracts systematically:
1. Identify ALL significant clause types — and flag notable absences
2. For each clause: call extract_clause → flag_risk → compare_to_standard (for key clauses)
3. Common types: Non-Compete, Non-Solicitation, Confidentiality, IP Assignment, \
Indemnification, Limitation of Liability, Termination, Governing Law, Arbitration, \
Payment Terms, Representations & Warranties, Data Privacy, Force Majeure

Be thorough. After all tool calls, write a 2-3 sentence executive summary."""

QA_SYSTEM = (
    "You are ClauseGuard, a legal contract analyst. "
    "Answer questions about contracts concisely and precisely. "
    "Cite specific sections when possible. Note any risks relevant to the question."
)


# ── LangChain tools (structured output via function calling) ──────────────────

@tool
def extract_clause(clause_type: str, clause_text: str, section_reference: str) -> str:
    """Record a specific clause found in the contract. Call for each significant clause type identified."""
    return "Recorded."


@tool
def flag_risk(
    clause_type: str,
    risk_level: Literal["Critical", "High", "Medium", "Low", "None"],
    risk_score: int,
    issue_summary: str,
    detailed_analysis: str,
    recommendation: str,
) -> str:
    """Assess and record the risk level of a clause. Call after extract_clause for every clause with any risk.
    risk_score: 85-100=Critical, 60-84=High, 35-59=Medium, 10-34=Low, 0-9=None."""
    return "Recorded."


@tool
def compare_to_standard(
    clause_type: str,
    deviation: Literal["Favorable", "Market Standard", "Unfavorable", "Highly Unfavorable", "Missing"],
    what_is_standard: str,
    how_it_differs: str,
) -> str:
    """Compare a clause against market-standard language. Call for key clauses: \
non-compete, confidentiality, IP assignment, limitation of liability, indemnification, termination."""
    return "Recorded."


TOOLS = [extract_clause, flag_risk, compare_to_standard]


# ── Analyzer ──────────────────────────────────────────────────────────────────

class ClauseAnalyzer:
    def __init__(self, groq_api_key: str) -> None:
        self._llm = ChatGroq(model=GROQ_MODEL, api_key=groq_api_key, temperature=0)

    @property
    def llm(self) -> ChatGroq:
        return self._llm

    def answer_question(
        self,
        question: str,
        context_chunks: list[str],
        history: list[dict],
    ) -> str:
        context = "\n\n---\n\n".join(context_chunks) if context_chunks else "No relevant sections found."

        # Convert stored history dicts → LangChain message objects
        history_messages = []
        for msg in history[-8:]:
            content = msg["content"]
            if isinstance(content, list):
                content = " ".join(
                    b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
                )
            if msg["role"] == "user":
                history_messages.append(HumanMessage(content=str(content)))
            else:
                history_messages.append(AIMessage(content=str(content)))

        # LCEL chain: format context + history + question → Groq → string
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", QA_SYSTEM),
                MessagesPlaceholder("history"),
                ("human", "Relevant contract sections:\n\n{context}\n\nQuestion: {question}"),
            ]
        )

        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"context": context, "question": question, "history": history_messages})

    def generate_risk_report(self, contract_text: str) -> dict:
        llm_with_tools = self.llm.bind_tools(TOOLS)

        messages = [
            SystemMessage(content=ANALYSIS_SYSTEM),
            HumanMessage(
                content=(
                    "Analyze this contract comprehensively. For each significant clause: "
                    "(1) call extract_clause, (2) call flag_risk, "
                    "(3) call compare_to_standard for the most important clauses. "
                    "After all tool calls, write a 2-3 sentence executive summary.\n\n"
                    f"CONTRACT TEXT:\n\n{contract_text[:50000]}"
                )
            ),
        ]

        summary = ""

        for _ in range(30):
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            # Capture any executive summary text
            if isinstance(response.content, str) and response.content.strip():
                summary = response.content
            elif isinstance(response.content, list):
                for part in response.content:
                    if isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
                        summary = part["text"]

            # Return results for every tool call so the model can continue
            if response.tool_calls:
                for tc in response.tool_calls:
                    messages.append(ToolMessage(content="Recorded.", tool_call_id=tc["id"]))
            else:
                break  # no more tool calls → done

        # Harvest structured data from all AIMessages in the conversation
        extracted: dict = {}
        risks: dict = {}
        comparisons: dict = {}

        for msg in messages:
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for tc in msg.tool_calls:
                    name = tc["name"]
                    args = tc["args"]
                    key = args.get("clause_type", "")
                    if name == "extract_clause":
                        extracted[key] = args
                    elif name == "flag_risk":
                        risks[key] = args
                    elif name == "compare_to_standard":
                        comparisons[key] = args

        return self._build_report(extracted, risks, comparisons, summary)

    def _build_report(
        self,
        extracted: dict,
        risks: dict,
        comparisons: dict,
        summary: str,
    ) -> dict:
        findings: list[dict] = []

        for clause_type, risk in risks.items():
            findings.append(
                {
                    "clause_type": clause_type,
                    "risk_level": risk.get("risk_level", "None"),
                    "risk_score": risk.get("risk_score", 0),
                    "issue_summary": risk.get("issue_summary", ""),
                    "detailed_analysis": risk.get("detailed_analysis", ""),
                    "recommendation": risk.get("recommendation", ""),
                    "clause_excerpt": extracted.get(clause_type, {}).get("clause_text", "")[:500],
                    "section": extracted.get(clause_type, {}).get("section_reference", "—"),
                    "comparison": comparisons.get(clause_type),
                }
            )

        for clause_type, clause in extracted.items():
            if clause_type not in risks:
                findings.append(
                    {
                        "clause_type": clause_type,
                        "risk_level": "None",
                        "risk_score": 0,
                        "issue_summary": "Standard clause — no significant risk identified.",
                        "detailed_analysis": "",
                        "recommendation": "No changes needed.",
                        "clause_excerpt": clause.get("clause_text", "")[:500],
                        "section": clause.get("section_reference", "—"),
                        "comparison": comparisons.get(clause_type),
                    }
                )

        findings.sort(key=lambda x: x["risk_score"], reverse=True)

        scores = sorted([f["risk_score"] for f in findings if f["risk_score"] > 0], reverse=True)
        if scores:
            if len(scores) >= 3:
                overall = int(
                    scores[0] * 0.45 + scores[1] * 0.30 + (sum(scores[2:]) / (len(scores) - 2)) * 0.25
                )
            elif len(scores) == 2:
                overall = int(scores[0] * 0.6 + scores[1] * 0.4)
            else:
                overall = scores[0]
            overall = min(overall, 100)
        else:
            overall = 0

        return {
            "overall_score": overall,
            "findings": findings,
            "summary": summary,
            "total_clauses": len(extracted),
            "high_risk_count": len([f for f in findings if f["risk_score"] >= 60]),
        }
