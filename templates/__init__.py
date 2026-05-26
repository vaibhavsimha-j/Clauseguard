def get_jurisdiction_context(jurisdiction: str) -> str:
    if jurisdiction == "India":
        from templates.standard_clauses_india import JURISDICTION_CONTEXT
    else:
        from templates.standard_clauses_us import JURISDICTION_CONTEXT
    return JURISDICTION_CONTEXT
