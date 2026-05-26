"""
LangChain + Groq (Llama 3.3 70B) orchestration layer.

- Jurisdiction-aware system prompts (India / US)
- Explicit risk-calibration examples per jurisdiction
- Section pre-pass: extract all headings first, mandate coverage of every one
- Gap-fill pass: after main loop, detect skipped sections and run a targeted follow-up
- v2: jurisdiction parameter added to generate_risk_report and answer_question
"""

from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_groq import ChatGroq

GROQ_MODEL = "llama-3.3-70b-versatile"

_ANALYSIS_BASE = """You are ClauseGuard, an expert legal contract analyst. \
Your primary goal is COMPLETE coverage — you must analyze EVERY section listed.

━━ RISK SCORING CALIBRATION ━━

Critical (85-100) — Deal-breaker. Immediate legal exposure. Do NOT sign without changes.
  • Non-compete: void/unenforceable under applicable law (e.g. Section 27 ICA in India),
    OR duration >2 years, OR worldwide scope, OR liquidated damages >$100k
  • IP assignment: no carve-out for inventions made on personal time unrelated to business
  • Confidentiality: permanent, one-sided (employee only), no exclusions for public knowledge
  • Arbitration: employee bears ALL costs + class action waiver + company retains court access
  • Indemnification: uncapped, one-directional (employee only, no reciprocal obligation)
  • Liability cap: company capped at nominal amount with no equivalent cap on employee

High (60-84) — Significant. Must negotiate before signing.
  • Non-compete: enforceable jurisdiction but broad scope/geography
  • Termination: no notice period AND no severance regardless of tenure
  • One-sided indemnification with some cap
  • Liability exclusions overwhelmingly favouring one party

Medium (35-59) — Common but worth negotiating if possible.
  • At-will employment without severance provision
  • Non-solicitation covering all customers (not just those employee worked with)
  • Mandatory arbitration with cost-sharing
  • Governing law in an unfavourable jurisdiction

Low (10-34) — Minor deviation from standard.
None (0-9) — Acceptable, market-standard language.

━━ PROCESS ━━
For EACH section in the provided list:
  1. Call extract_clause (verbatim text + section reference)
  2. Call flag_risk (apply calibration + jurisdiction law above carefully)
  3. Call compare_to_standard for: Non-Compete, Confidentiality, IP Assignment,
     Limitation of Liability, Indemnification, Termination, Arbitration

Do NOT stop until every listed section is covered.
After all tool calls, write a 2-3 sentence executive summary."""


def _build_analysis_system(jurisdiction: str) -> str:
    from templates import get_jurisdiction_context
    return _ANALYSIS_BASE + "\n\n" + get_jurisdiction_context(jurisdiction)


def _build_qa_system(jurisdiction: str) -> str:
    law = "Indian law (Indian Contract Act 1872 and related statutes)" if jurisdiction == "India" \
          else "US law (federal and state commercial law)"
    return (
        f"You are ClauseGuard, a legal contract analyst specialising in {law}. "
        "Answer questions about contracts concisely and precisely. "
        "Reference applicable statutes and case law from the jurisdiction when relevant. "
        "Cite specific sections when possible. Note any risks relevant to the question."
    )


# ── LangChain tools ────────────────────────────────────────────────────────────

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
    """Assess and record the risk level of a clause. Apply the calibration table exactly.
    risk_score: 85-100=Critical, 60-84=High, 35-59=Medium, 10-34=Low, 0-9=None."""
    return "Recorded."


@tool
def compare_to_standard(
    clause_type: str,
    deviation: Literal["Favorable", "Market Standard", "Unfavorable", "Highly Unfavorable", "Missing"],
    what_is_standard: str,
    how_it_differs: str,
) -> str:
    """Compare a clause against market-standard language."""
    return "Recorded."


TOOLS = [extract_clause, flag_risk, compare_to_standard]


# ── Analyzer ──────────────────────────────────────────────────────────────────

class ClauseAnalyzer:
    def __init__(self, groq_api_key: str) -> None:
        self._llm = ChatGroq(model=GROQ_MODEL, api_key=groq_api_key, temperature=0)

    @property
    def llm(self) -> ChatGroq:
        return self._llm

    # ── Q&A ───────────────────────────────────────────────────────────────────

    def answer_question(
        self,
        question: str,
        context_chunks: list[str],
        history: list[dict],
        jurisdiction: str = "India",
    ) -> str:
        context = "\n\n---\n\n".join(context_chunks) if context_chunks else "No relevant sections found."

        history_messages = []
        for msg in history[-8:]:
            content = msg["content"]
            if isinstance(content, list):
                content = " ".join(
                    b.get("text", "") for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            if msg["role"] == "user":
                history_messages.append(HumanMessage(content=str(content)))
            else:
                history_messages.append(AIMessage(content=str(content)))

        prompt = ChatPromptTemplate.from_messages([
            ("system", _build_qa_system(jurisdiction)),
            MessagesPlaceholder("history"),
            ("human", "Relevant contract sections:\n\n{context}\n\nQuestion: {question}"),
        ])

        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"context": context, "question": question, "history": history_messages})

    # ── Risk report ───────────────────────────────────────────────────────────

    def generate_risk_report(self, contract_text: str, jurisdiction: str = "India") -> dict:
        truncated = contract_text[:50000]

        # ── Step 1: extract section headings so we can mandate complete coverage ──
        section_list = self._extract_section_list(truncated)
        sections_directive = (
            f"You MUST analyze ALL {len(section_list)} of these sections — do not skip any:\n"
            + "\n".join(f"  • {s}" for s in section_list)
        ) if section_list else "Analyze every section in the contract thoroughly."

        # ── Step 2: main tool-use loop ────────────────────────────────────────
        main_prompt = (
            f"{sections_directive}\n\n"
            "For each section: call extract_clause → flag_risk → compare_to_standard (key clauses).\n"
            "Apply the risk calibration and jurisdiction law in the system prompt exactly.\n"
            "After ALL sections are done, write a 2-3 sentence executive summary.\n\n"
            f"CONTRACT TEXT:\n\n{truncated}"
        )

        extracted, risks, comparisons, summary = self._run_tool_loop(main_prompt, jurisdiction=jurisdiction)

        # ── Step 3: gap-fill — find sections the model skipped ────────────────
        skipped = self._find_skipped_sections(section_list, extracted)

        if skipped:
            gap_prompt = (
                "The following sections were NOT analyzed in the previous pass. "
                "Analyze each one now — extract_clause + flag_risk + compare_to_standard:\n"
                + "\n".join(f"  • {s}" for s in skipped)
                + f"\n\nCONTRACT TEXT:\n\n{truncated}"
            )
            ext2, risk2, comp2, summary2 = self._run_tool_loop(gap_prompt, jurisdiction=jurisdiction)
            # Merge gap-fill results (don't overwrite existing good data)
            for k, v in ext2.items():
                extracted.setdefault(k, v)
            for k, v in risk2.items():
                risks.setdefault(k, v)
            for k, v in comp2.items():
                comparisons.setdefault(k, v)
            if summary2 and not summary:
                summary = summary2

        return self._build_report(extracted, risks, comparisons, summary, jurisdiction)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_section_list(self, contract_text: str) -> list[str]:
        """Quick single call (no tools) to get all section headings from the contract."""
        response = self.llm.invoke([
            SystemMessage(content="You are a document parser."),
            HumanMessage(
                content=(
                    "List every section and article heading in this contract, one per line. "
                    "Include the section number and title, e.g. 'Section 5. Non-Competition'. "
                    "Output ONLY the headings — no explanations, no bullets, no extra text.\n\n"
                    + contract_text[:20000]
                )
            ),
        ])
        lines = response.content.strip().split("\n")
        return [ln.strip() for ln in lines if ln.strip()]

    def _run_tool_loop(
        self,
        user_prompt: str,
        jurisdiction: str = "India",
        max_iterations: int = 35,
    ) -> tuple[dict, dict, dict, str]:
        """Run the agentic tool-use loop and return (extracted, risks, comparisons, summary)."""
        llm_with_tools = self.llm.bind_tools(TOOLS)
        messages: list = [
            SystemMessage(content=_build_analysis_system(jurisdiction)),
            HumanMessage(content=user_prompt),
        ]
        summary = ""

        for _ in range(max_iterations):
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            # Capture any text output as the running summary
            if isinstance(response.content, str) and response.content.strip():
                summary = response.content
            elif isinstance(response.content, list):
                for part in response.content:
                    if isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
                        summary = part["text"]

            if response.tool_calls:
                for tc in response.tool_calls:
                    messages.append(ToolMessage(content="Recorded.", tool_call_id=tc["id"]))
            else:
                break

        # Harvest structured data from AIMessages
        extracted: dict = {}
        risks: dict = {}
        comparisons: dict = {}

        for msg in messages:
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for tc in msg.tool_calls:
                    key = tc["args"].get("clause_type", "")
                    if tc["name"] == "extract_clause":
                        extracted[key] = tc["args"]
                    elif tc["name"] == "flag_risk":
                        risks[key] = tc["args"]
                    elif tc["name"] == "compare_to_standard":
                        comparisons[key] = tc["args"]

        return extracted, risks, comparisons, summary

    def _find_skipped_sections(
        self,
        section_list: list[str],
        extracted: dict,
    ) -> list[str]:
        """Return sections from section_list that don't appear in extracted."""
        if not section_list:
            return []

        covered_lower = {k.lower() for k in extracted}
        skipped = []

        for section in section_list:
            # Split the heading into meaningful words (>3 chars) for fuzzy matching
            words = [w.lower() for w in section.replace(".", " ").split() if len(w) > 3]
            if not words:
                continue
            # A section is "covered" if any extracted key shares at least one keyword with it
            covered = any(
                any(word in covered_key or covered_key in word for covered_key in covered_lower)
                for word in words
            )
            if not covered:
                skipped.append(section)

        return skipped

    # ── Report builder ────────────────────────────────────────────────────────

    def _build_report(
        self,
        extracted: dict,
        risks: dict,
        comparisons: dict,
        summary: str,
        jurisdiction: str = "India",
    ) -> dict:
        findings: list[dict] = []

        for clause_type, risk in risks.items():
            findings.append({
                "clause_type": clause_type,
                "risk_level": risk.get("risk_level", "None"),
                "risk_score": risk.get("risk_score", 0),
                "issue_summary": risk.get("issue_summary", ""),
                "detailed_analysis": risk.get("detailed_analysis", ""),
                "recommendation": risk.get("recommendation", ""),
                "clause_excerpt": extracted.get(clause_type, {}).get("clause_text", "")[:500],
                "section": extracted.get(clause_type, {}).get("section_reference", "—"),
                "comparison": comparisons.get(clause_type),
            })

        for clause_type, clause in extracted.items():
            if clause_type not in risks:
                findings.append({
                    "clause_type": clause_type,
                    "risk_level": "None",
                    "risk_score": 0,
                    "issue_summary": "Standard clause — no significant risk identified.",
                    "detailed_analysis": "",
                    "recommendation": "No changes needed.",
                    "clause_excerpt": clause.get("clause_text", "")[:500],
                    "section": clause.get("section_reference", "—"),
                    "comparison": comparisons.get(clause_type),
                })

        findings.sort(key=lambda x: x["risk_score"], reverse=True)

        scores = sorted(
            [f["risk_score"] for f in findings if f["risk_score"] > 0], reverse=True
        )
        if scores:
            if len(scores) >= 3:
                overall = int(
                    scores[0] * 0.45
                    + scores[1] * 0.30
                    + (sum(scores[2:]) / (len(scores) - 2)) * 0.25
                )
            elif len(scores) == 2:
                overall = int(scores[0] * 0.6 + scores[1] * 0.4)
            else:
                overall = scores[0]

            # If any clause is Critical, the overall should reflect that
            if any(f["risk_score"] >= 85 for f in findings):
                overall = max(overall, 82)

            overall = min(overall, 100)
        else:
            overall = 0

        return {
            "overall_score": overall,
            "findings": findings,
            "summary": summary,
            "total_clauses": len(extracted),
            "high_risk_count": len([f for f in findings if f["risk_score"] >= 60]),
            "jurisdiction": jurisdiction,
        }
