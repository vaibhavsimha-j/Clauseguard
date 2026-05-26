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
def get_analyzer(groq_api_key: str):
    from backend.clause_analyzer import ClauseAnalyzer
    return ClauseAnalyzer(groq_api_key=groq_api_key)


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


# ── session state defaults ─────────────────────────────────────────────────────

for _key, _default in [
    ("contract_id", None),
    ("contract_name", None),
    ("contract_text", None),
    ("messages", []),
    ("risk_report", None),
    ("analysis_error", None),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default


# ── sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚖️ ClauseGuard")
    st.caption("Legal Contract Intelligence")
    st.divider()

    # ── API key inputs ──
    st.markdown("**API Keys**")

    groq_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Get yours at console.groq.com",
        key="groq_api_key",
    )
    pinecone_key = st.text_input(
        "Pinecone API Key",
        type="password",
        placeholder="pcsk_...",
        help="Get yours at app.pinecone.io",
        key="pinecone_api_key",
    )

    index_name = "clauseguard"  # fixed — users don't need to configure this
    keys_ready = bool(groq_key and pinecone_key)

    if keys_ready:
        st.success("Connected")
    else:
        missing = [k for k, v in [("Groq API Key", groq_key), ("Pinecone API Key", pinecone_key)] if not v]
        st.warning(f"Enter: {', '.join(missing)}")

    # Stop here if keys aren't ready — nothing below works without them
    if not keys_ready:
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
    )

    if uploaded and uploaded.name != st.session_state.contract_name:
        try:
            processor = get_processor()
            vector_store = get_vector_store(pinecone_key, index_name)
            with st.spinner("Parsing & indexing…"):
                cid, chunks, text = processor.process(uploaded)
                vector_store.add_document(cid, chunks, uploaded.name)
            st.session_state.contract_id = cid
            st.session_state.contract_name = uploaded.name
            st.session_state.contract_text = text
            st.session_state.messages = []
            st.session_state.risk_report = None
            st.session_state.analysis_error = None
            st.success("Contract uploaded successfully")
        except Exception as exc:
            st.error(f"Failed to process file: {exc}")

    if st.session_state.contract_id:
        st.divider()
        st.markdown(f"**📄 {st.session_state.contract_name}**")
        st.caption(f"{len(st.session_state.contract_text):,} characters")

        if st.session_state.risk_report is None:
            if st.button("🔍 Generate Risk Report", type="primary", use_container_width=True):
                st.session_state.analysis_error = None
                analyzer = get_analyzer(groq_key)
                with st.spinner("Analyzing clauses… (30–90 sec)"):
                    try:
                        st.session_state.risk_report = analyzer.generate_risk_report(
                            st.session_state.contract_text,
                            jurisdiction=jurisdiction,
                        )
                    except Exception as exc:
                        import traceback
                        st.session_state.analysis_error = f"{exc}\n\n{traceback.format_exc()}"
                st.rerun()

            if st.session_state.analysis_error:
                st.error(f"Analysis failed: {st.session_state.analysis_error}")
        else:
            st.success("Report ready")
            if st.button("↺ Re-analyze", use_container_width=True):
                st.session_state.risk_report = None
                st.rerun()

        if st.button("Clear contract", use_container_width=True):
            for k in ("contract_id", "contract_name", "contract_text", "messages", "risk_report", "analysis_error"):
                st.session_state[k] = None if k != "messages" else []
            st.rerun()


# ── landing page ───────────────────────────────────────────────────────────────

if not st.session_state.contract_id:
    st.markdown("# ⚖️ ClauseGuard")
    st.markdown("#### Legal Contract Intelligence Platform")
    st.markdown(
        "Upload any contract — NDA, employment agreement, service agreement — "
        "and get structured risk analysis powered by Llama 3.3 70B."
    )
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.info("**📤 Upload**\nPDF, Word, or plain text contracts")
    c2.info("**💬 Ask**\nNatural-language Q&A backed by RAG")
    c3.info("**🚨 Analyze**\nStructured risk scoring with clause-by-clause breakdown")
    st.stop()


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

    if prompt := st.chat_input("Ask about your contract…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            vector_store = get_vector_store(pinecone_key, index_name)
            analyzer = get_analyzer(groq_key)
            with st.spinner("Searching contract…"):
                chunks = vector_store.search(prompt, st.session_state.contract_id, k=5)
                try:
                    reply = analyzer.answer_question(
                        prompt, chunks, st.session_state.messages[:-1],
                        jurisdiction=jurisdiction,
                    )
                except Exception as exc:
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
