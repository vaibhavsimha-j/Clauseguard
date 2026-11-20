import io
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="ClauseGuard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    [data-testid="stSidebar"] { background-color: #0f172a; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stButton button { background: #1e40af; color: white !important; border: none; }
    [data-testid="stSidebar"] .stButton button:hover { background: #1d4ed8; }
    [data-testid="stSidebar"] input { color: #ffffff !important; }
    div[data-testid="stExpander"] { border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 6px; }
    .risk-score-box { text-align: center; padding: 24px; border-radius: 12px; border: 2px solid; margin-bottom: 16px; }
    .score-number { font-size: 3rem; font-weight: 800; line-height: 1; }
    .score-label { font-size: 1rem; font-weight: 600; margin-top: 4px; }
</style>
""",
    unsafe_allow_html=True,
)


# ── cached component factories (keyed by api credentials) ─────────────────────

@st.cache_resource
def get_processor():
    from backend.document_processor import DocumentProcessor
    return DocumentProcessor()


@st.cache_resource
def get_vector_store(pinecone_api_key: str, index_name: str):
    from backend.vector_store import VectorStore
    return VectorStore(pinecone_api_key=pinecone_api_key, index_name=index_name)


@st.cache_resource
def get_analyzer(gemini_api_key: str):
    from backend.clause_analyzer import ClauseAnalyzer
    return ClauseAnalyzer(gemini_api_key=gemini_api_key)


# ── helpers ────────────────────────────────────────────────────────────────────

RISK_COLORS = {
    "Critical": "#dc2626",
    "High": "#ea580c",
    "Medium": "#ca8a04",
    "Low": "#16a34a",
    "None": "#15803d",
}

RISK_ICONS = {
    "Critical": "🔴",
    "High": "🟠",
    "Medium": "🟡",
    "Low": "🟢",
    "None": "✅",
}

DEVIATION_DISPLAY = {
    "Favorable": "✅ Favorable",
    "Market Standard": "📋 Market Standard",
    "Unfavorable": "⚠️ Unfavorable",
    "Highly Unfavorable": "🚨 Highly Unfavorable",
    "Missing": "❌ Missing",
}


def score_label(score: int) -> tuple[str, str]:
    if score >= 80:
        return "Critical Risk", "#dc2626"
    if score >= 60:
        return "High Risk", "#ea580c"
    if score >= 35:
        return "Moderate Risk", "#ca8a04"
    return "Low Risk", "#16a34a"


# ── demo mode ──────────────────────────────────────────────────────────────────
# Lets visitors try ClauseGuard on the owner's API keys, which are read from
# Streamlit Secrets (never from the repo). Usage is capped per visitor session
# AND across the whole app per UTC day, so the keys can't be drained.

def _secret(name: str, default=None):
    try:
        value = st.secrets.get(name)
    except Exception:  # no secrets.toml configured
        value = None
    if value in (None, ""):
        value = os.getenv(name, default)
    return value


def _int_secret(name: str, default: int) -> int:
    try:
        return int(_secret(name, default))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


DEMO_GEMINI_KEY = _secret("DEMO_GEMINI_API_KEY")
DEMO_PINECONE_KEY = _secret("DEMO_PINECONE_API_KEY")
DEMO_AVAILABLE = bool(DEMO_GEMINI_KEY and DEMO_PINECONE_KEY)

DEMO_LIMITS = {
    # kind: (per visitor session, whole app per UTC day)
    "report": (_int_secret("DEMO_SESSION_REPORTS", 2), _int_secret("DEMO_DAILY_REPORTS", 15)),
    "question": (_int_secret("DEMO_SESSION_QUESTIONS", 10), _int_secret("DEMO_DAILY_QUESTIONS", 100)),
}
DEMO_MAX_CHARS = 20_000      # each report re-sends the contract on every LLM call
DEMO_REPORT_TIMEOUT = 600    # seconds before a stuck "report running" slot is freed

MODE_DEMO = "🎯 Try Demo (no keys needed)"
MODE_OWN = "🔑 Use my own API keys"

_SAMPLES_DIR = Path(__file__).parent / "samples"
# jurisdiction -> (file, display name, flag, button tooltip)
SAMPLE_CONTRACTS = {
    "India": (
        _SAMPLES_DIR / "sample_employment_agreement_india.txt",
        "Sample - Employment Agreement (India).txt",
        "🇮🇳",
        "A fictional Bengaluru employment agreement with several clauses that are risky under Indian law",
    ),
    "United States": (
        _SAMPLES_DIR / "sample_employment_agreement_us.txt",
        "Sample - Employment Agreement (US - California).txt",
        "🇺🇸",
        "A fictional California employment agreement with several clauses that are risky under US law",
    ),
}


class DemoUsage:
    """App-wide demo counters shared by every session (thread-safe)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._day = None
        self._counts = {"report": 0, "question": 0}
        self._report_started_at = None

    def _roll_day(self) -> None:
        today = datetime.now(timezone.utc).date()
        if today != self._day:
            self._day = today
            self._counts = {"report": 0, "question": 0}

    def remaining(self, kind: str, limit: int) -> int:
        with self._lock:
            self._roll_day()
            return max(0, limit - self._counts[kind])

    def try_use(self, kind: str, limit: int) -> bool:
        with self._lock:
            self._roll_day()
            if self._counts[kind] >= limit:
                return False
            self._counts[kind] += 1
            return True

    def refund(self, kind: str) -> None:
        with self._lock:
            self._counts[kind] = max(0, self._counts[kind] - 1)

    def try_start_report(self) -> bool:
        """Only one demo report at a time, so concurrent visitors can't trip Gemini's per-minute limit."""
        with self._lock:
            now = time.time()
            if self._report_started_at and now - self._report_started_at < DEMO_REPORT_TIMEOUT:
                return False
            self._report_started_at = now
            return True

    def finish_report(self) -> None:
        with self._lock:
            self._report_started_at = None


@st.cache_resource
def get_demo_usage() -> DemoUsage:
    return DemoUsage()


def demo_remaining(kind: str) -> int:
    session_limit, daily_limit = DEMO_LIMITS[kind]
    session_left = session_limit - st.session_state[f"demo_{kind}s_used"]
    return max(0, min(session_left, get_demo_usage().remaining(kind, daily_limit)))


def _limit_message(kind: str, scope: str) -> str:
    noun = "risk report" if kind == "report" else "question"
    if scope == "session":
        return (
            f"You've used all {DEMO_LIMITS[kind][0]} demo {noun}s for this session. "
            "To keep exploring, switch to **Use my own API keys** — Google AI Studio and Pinecone both have free tiers."
        )
    return (
        f"The demo has reached today's {noun} limit (it resets at midnight UTC). "
        "You can still try ClauseGuard right now with your own free API keys."
    )


def demo_exhausted_message(kind: str) -> str:
    """Explain why no demo uses are left (doesn't consume anything)."""
    if st.session_state[f"demo_{kind}s_used"] >= DEMO_LIMITS[kind][0]:
        return _limit_message(kind, "session")
    return _limit_message(kind, "daily")


def reserve_demo(kind: str) -> str | None:
    """Consume one demo use. Returns a message to show the visitor if they're out of uses."""
    session_limit, daily_limit = DEMO_LIMITS[kind]
    if st.session_state[f"demo_{kind}s_used"] >= session_limit:
        return _limit_message(kind, "session")
    if not get_demo_usage().try_use(kind, daily_limit):
        return _limit_message(kind, "daily")
    st.session_state[f"demo_{kind}s_used"] += 1
    return None


def release_demo(kind: str) -> None:
    """Give a demo use back when the call failed, so visitors aren't charged for errors."""
    st.session_state[f"demo_{kind}s_used"] = max(0, st.session_state[f"demo_{kind}s_used"] - 1)
    get_demo_usage().refund(kind)


def demo_error_message(exc: Exception) -> str:
    logging.exception("Demo mode request failed", exc_info=exc)
    text = str(exc).lower()
    if any(s in text for s in ("429", "resource_exhausted", "resourceexhausted", "quota", "rate limit")):
        return "The demo is busy right now (rate limit reached). Please wait a minute and try again."
    return "Something went wrong while running the demo. Please try again in a minute."


class _NamedBytes(io.BytesIO):
    """In-memory file with a .name, so the sample contract looks like an upload."""

    def __init__(self, data: bytes, name: str) -> None:
        super().__init__(data)
        self.name = name


# ── session state defaults ─────────────────────────────────────────────────────

CONTRACT_KEYS = ("contract_id", "contract_name", "contract_text", "messages", "risk_report", "analysis_error", "analysis_notice")


def reset_contract() -> None:
    for k in CONTRACT_KEYS:
        st.session_state[k] = [] if k == "messages" else None
    st.session_state.uploader_nonce += 1  # also empties the file uploader widget


for _key, _default in [
    ("contract_id", None),
    ("contract_name", None),
    ("contract_text", None),
    ("messages", []),
    ("risk_report", None),
    ("analysis_error", None),
    ("analysis_notice", None),
    ("demo_reports_used", 0),
    ("demo_questions_used", 0),
    ("uploader_nonce", 0),
    ("active_mode", None),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default


# ── sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    if DEMO_AVAILABLE:
        st.markdown("## 🚀 Get Started")
        mode = st.radio("Mode", [MODE_DEMO, MODE_OWN], key="mode", label_visibility="collapsed")
    else:
        mode = MODE_OWN
    demo_mode = mode == MODE_DEMO

    # Contracts are indexed in the active mode's Pinecone account, so switching modes starts fresh
    if st.session_state.active_mode not in (None, mode):
        reset_contract()
    st.session_state.active_mode = mode

    if demo_mode:
        st.success("Demo mode is on — no API keys needed.")
        st.caption(
            f"🎯 Demo uses left: **{demo_remaining('report')}** risk reports · "
            f"**{demo_remaining('question')}** questions"
        )
        st.caption("Please don't upload confidential documents in demo mode.")
        gemini_key, pinecone_key = str(DEMO_GEMINI_KEY), str(DEMO_PINECONE_KEY)
    else:
        st.markdown("## 🔑 API Configuration")
        st.markdown("Enter your API keys to start ClauseGuard.")
        st.info("🔒 Your API Keys are SAFE with us!")
        st.divider()

        gemini_key = st.text_input(
            "Google AI API Key",
            type="password",
            placeholder="AIza...",
            help="Get yours free at aistudio.google.com",
            key="gemini_api_key",
        )
        pinecone_key = st.text_input(
            "Pinecone API Key",
            type="password",
            placeholder="pcsk_...",
            help="Get yours at app.pinecone.io",
            key="pinecone_api_key",
        )

    index_name = "clauseguard"  # fixed — users don't need to configure this
    keys_ready = bool(gemini_key and pinecone_key)

    if not demo_mode:
        if keys_ready:
            st.success("Connected")
        else:
            missing = [k for k, v in [("Google AI API Key", gemini_key), ("Pinecone API Key", pinecone_key)] if not v]
            st.warning(f"Enter: {', '.join(missing)}")

    # Stop here if keys aren't ready — nothing below works without them
    if not keys_ready:
        if DEMO_AVAILABLE:
            st.caption("No keys? Pick **Try Demo** above.")
        st.stop()

    st.divider()

    # ── jurisdiction selector ──
    st.markdown("**Jurisdiction**")
    jurisdiction = st.selectbox(
        "Jurisdiction",
        ["India", "United States"],
        label_visibility="collapsed",
        key="jurisdiction",
        help="Risk assessment and clause comparisons will follow this jurisdiction's laws",
    )

    # Warn if report was generated under a different jurisdiction
    if (
        st.session_state.risk_report is not None
        and st.session_state.risk_report.get("jurisdiction") != jurisdiction
    ):
        st.warning(
            f"Report was generated under **{st.session_state.risk_report.get('jurisdiction')}** law. "
            "Click **Re-analyze** to regenerate under the new jurisdiction."
        )

    st.divider()

    # ── file upload ──
    st.markdown("**Upload Contract**")
    uploaded = st.file_uploader(
        "upload",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
        help="Supports PDF, Word (.docx), and plain text",
        key=f"uploader_{st.session_state.uploader_nonce}",
    )

    sample_path, sample_name, sample_flag, sample_help = SAMPLE_CONTRACTS[jurisdiction]
    load_sample = st.button(
        f"📄 Load sample contract {sample_flag}",
        use_container_width=True,
        help=sample_help,
    )

    to_process = None
    if load_sample:
        to_process = _NamedBytes(sample_path.read_bytes(), sample_name)
    elif uploaded and uploaded.name != st.session_state.contract_name:
        to_process = uploaded

    if to_process is not None:
        try:
            processor = get_processor()
            cid, chunks, text = processor.process(to_process)
            if demo_mode and len(text) > DEMO_MAX_CHARS:
                st.warning(
                    f"Demo mode supports contracts up to {DEMO_MAX_CHARS:,} characters "
                    f"(this one has {len(text):,}). Try the sample contract, or use your own API keys for longer documents."
                )
            else:
                vector_store = get_vector_store(pinecone_key, index_name)
                with st.spinner("Parsing & indexing…"):
                    vector_store.add_document(cid, chunks, to_process.name)
                if load_sample:
                    reset_contract()  # empties the uploader so it can't override the sample
                st.session_state.contract_id = cid
                st.session_state.contract_name = to_process.name
                st.session_state.contract_text = text
                st.session_state.messages = []
                st.session_state.risk_report = None
                st.session_state.analysis_error = None
                st.session_state.analysis_notice = None
                if load_sample:
                    st.rerun()
                st.success("Contract uploaded successfully")
        except Exception as exc:
            if demo_mode:
                st.error(demo_error_message(exc))
            else:
                st.error(f"Failed to process file: {exc}")

    if st.session_state.contract_id:
        st.divider()
        st.markdown(f"**📄 {st.session_state.contract_name}**")
        st.caption(f"{len(st.session_state.contract_text):,} characters")

        if st.session_state.risk_report is None:
            if st.button("🔍 Generate Risk Report", type="primary", use_container_width=True):
                st.session_state.analysis_error = None
                st.session_state.analysis_notice = None
                if demo_mode:
                    st.session_state.analysis_notice = reserve_demo("report")
                    if not st.session_state.analysis_notice and not get_demo_usage().try_start_report():
                        release_demo("report")
                        st.session_state.analysis_notice = (
                            "Another visitor is generating a demo report right now. "
                            "Please try again in a minute or two."
                        )
                if not st.session_state.analysis_notice:
                    analyzer = get_analyzer(gemini_key)
                    with st.spinner("Analyzing clauses… (30–90 sec)"):
                        try:
                            st.session_state.risk_report = analyzer.generate_risk_report(
                                st.session_state.contract_text,
                                jurisdiction=jurisdiction,
                            )
                        except Exception as exc:
                            if demo_mode:
                                release_demo("report")
                                st.session_state.analysis_notice = demo_error_message(exc)
                            else:
                                import traceback
                                st.session_state.analysis_error = f"{exc}\n\n{traceback.format_exc()}"
                        finally:
                            if demo_mode:
                                get_demo_usage().finish_report()
                st.rerun()

            if st.session_state.analysis_notice:
                st.warning(st.session_state.analysis_notice)
            if st.session_state.analysis_error:
                st.error(f"Analysis failed: {st.session_state.analysis_error}")
        else:
            st.success("Report ready")
            if st.button("↺ Re-analyze", use_container_width=True):
                st.session_state.risk_report = None
                st.rerun()

        if st.button("Clear contract", use_container_width=True):
            reset_contract()
            st.rerun()


# ── persistent header ─────────────────────────────────────────────────────────

st.markdown("# ⚖️ ClauseGuard")
st.markdown("#### Legal Contract Intelligence Platform")
st.markdown(
    "Upload any contract — NDA, employment agreement, service agreement — "
    "and get structured risk analysis powered by Gemini Flash."
)
if not st.session_state.contract_id:
    if demo_mode:
        st.info(
            "👈 **New here?** Pick a jurisdiction, click **📄 Load sample contract** in the sidebar "
            "(it loads a sample written for that jurisdiction), then **🔍 Generate Risk Report** — "
            "or upload your own contract. No API keys needed."
        )
    st.stop()

st.divider()

# ── main tabs ──────────────────────────────────────────────────────────────────

tab_qa, tab_risk, tab_clauses = st.tabs(["💬 Ask Questions", "🚨 Risk Analysis", "📋 Clauses"])


# ── Q&A tab ────────────────────────────────────────────────────────────────────

with tab_qa:
    st.markdown("Ask anything about the contract in plain English.")

    if not st.session_state.messages:
        st.markdown("**Suggested questions:**")
        col_a, col_b = st.columns(2)
        suggestions = [
            "What are the termination conditions?",
            "Is there a non-compete clause, and how long does it last?",
            "Who owns intellectual property created during this engagement?",
            "What happens to confidential information after the contract ends?",
        ]
        for i, s in enumerate(suggestions):
            (col_a if i % 2 == 0 else col_b).markdown(f"- _{s}_")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    questions_left = demo_remaining("question") if demo_mode else None
    if demo_mode and questions_left == 0:
        st.info(demo_exhausted_message("question"))

    if prompt := st.chat_input("Ask about your contract…", disabled=questions_left == 0):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            blocked = reserve_demo("question") if demo_mode else None
            if blocked:
                reply = f"⚠️ {blocked}"
            else:
                vector_store = get_vector_store(pinecone_key, index_name)
                analyzer = get_analyzer(gemini_key)
                with st.spinner("Searching contract…"):
                    try:
                        chunks = vector_store.search(prompt, st.session_state.contract_id, k=5)
                        reply = analyzer.answer_question(
                            prompt, chunks, st.session_state.messages[:-1],
                            jurisdiction=jurisdiction,
                        )
                    except Exception as exc:
                        if demo_mode:
                            release_demo("question")
                            reply = f"⚠️ {demo_error_message(exc)}"
                        else:
                            reply = f"⚠️ Error: {exc}"
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()


# ── Risk Analysis tab ──────────────────────────────────────────────────────────

with tab_risk:
    if not st.session_state.risk_report:
        st.info("Click **Generate Risk Report** in the sidebar to analyze this contract.")
    else:
        report = st.session_state.risk_report
        overall = report["overall_score"]
        label, color = score_label(overall)

        report_jurisdiction = report.get("jurisdiction", "India")
        flag = "🇮🇳" if report_jurisdiction == "India" else "🇺🇸"
        st.caption(f"{flag} Analysed under **{report_jurisdiction}** law")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Risk Score", f"{overall} / 100")
        m2.metric("Risk Level", label)
        m3.metric("Clauses Found", report["total_clauses"])
        m4.metric("High+ Risk Clauses", report["high_risk_count"])

        st.progress(overall / 100)

        if report.get("summary"):
            st.markdown(f"> {report['summary']}")

        st.divider()
        st.markdown("### Clause-by-Clause Findings")

        for finding in report["findings"]:
            level = finding["risk_level"]
            icon = RISK_ICONS.get(level, "")
            score_f = finding["risk_score"]
            section = finding["section"]

            header = f"{icon} **{finding['clause_type']}** — {level} ({score_f}/100)  ·  {section}"

            with st.expander(header, expanded=(level in ("Critical", "High"))):
                if finding["clause_excerpt"]:
                    st.markdown("**Contract language:**")
                    st.markdown(
                        f"<blockquote style='border-left:4px solid {RISK_COLORS.get(level,'#64748b')};padding-left:12px;color:#475569'>"
                        f"{finding['clause_excerpt']}</blockquote>",
                        unsafe_allow_html=True,
                    )

                if finding["issue_summary"]:
                    st.markdown(f"**Issue:** {finding['issue_summary']}")

                if finding["detailed_analysis"]:
                    st.markdown(f"**Analysis:** {finding['detailed_analysis']}")

                if finding["recommendation"] and finding["recommendation"] not in ("No changes needed.", ""):
                    st.success(f"💡 **Recommendation:** {finding['recommendation']}")

                comp = finding.get("comparison")
                if comp:
                    st.divider()
                    dev_display = DEVIATION_DISPLAY.get(comp["deviation"], comp["deviation"])
                    st.markdown(f"**vs. Market Standard:** {dev_display}")
                    st.markdown(f"*Standard:* {comp['what_is_standard']}")
                    if comp["how_it_differs"]:
                        st.markdown(f"*Difference:* {comp['how_it_differs']}")


# ── Clauses tab ────────────────────────────────────────────────────────────────

with tab_clauses:
    if not st.session_state.risk_report:
        st.info("Generate a Risk Report first to browse extracted clauses.")
    else:
        report = st.session_state.risk_report
        findings = report["findings"]

        st.markdown(f"**{report['total_clauses']} clause types** identified in this contract.")
        st.divider()

        for level_key, group_label in [
            ("Critical", "🔴 Critical Risk"),
            ("High", "🟠 High Risk"),
            ("Medium", "🟡 Medium Risk"),
            ("Low", "🟢 Low Risk"),
            ("None", "✅ Standard / No Risk"),
        ]:
            group = [f for f in findings if f["risk_level"] == level_key]
            if not group:
                continue

            st.markdown(f"#### {group_label}")
            for finding in group:
                with st.expander(f"{finding['clause_type']}  ·  {finding['section']}"):
                    excerpt = finding["clause_excerpt"]
                    st.markdown(excerpt if excerpt else "_No text extracted._")
                    comp = finding.get("comparison")
                    if comp:
                        dev_display = DEVIATION_DISPLAY.get(comp["deviation"], comp["deviation"])
                        st.caption(f"Market comparison: {dev_display}")