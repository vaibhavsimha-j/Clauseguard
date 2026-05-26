"""
Reference descriptions for market-standard clause language.
Used as context in the system prompt for comparisons.
"""

STANDARD_CLAUSES = {
    "Non-Compete": {
        "market_standard": (
            "12-month post-termination restriction, limited to direct competitors in the same market segment. "
            "Geographic scope tied to where the employee actually worked. Reasonable carve-outs for passive investments."
        ),
        "red_flags": [
            "Duration exceeding 2 years",
            "Worldwide or overly broad geographic scope",
            "Covers entire industry, not just direct competitors",
            "No geographic limitation",
            "Applies without adequate consideration",
        ],
    },
    "Non-Solicitation": {
        "market_standard": (
            "12-24 month restriction on soliciting company employees and customers. "
            "Customers typically limited to those the employee actually dealt with."
        ),
        "red_flags": [
            "Covers all company customers, not just those the employee worked with",
            "Duration exceeding 24 months",
            "Prohibits passive acceptance of inbound inquiries",
        ],
    },
    "Confidentiality": {
        "market_standard": (
            "Mutual obligations during employment. Post-termination obligations for trade secrets are indefinite; "
            "for general confidential information, 2-5 years is standard. "
            "Clear exclusions: publicly available info, independently developed, rightfully received from third parties."
        ),
        "red_flags": [
            "One-sided (only employee obligated)",
            "No exclusions for public knowledge or prior knowledge",
            "Overly broad definition of 'confidential information'",
            "Perpetual obligation for all confidential information (not just trade secrets)",
        ],
    },
    "IP Assignment": {
        "market_standard": (
            "Assigns inventions created using company resources or related to company business. "
            "Should exclude inventions made entirely on personal time with no company resources and unrelated to business. "
            "Many states (CA, DE, IL, MN, NC, WA) require statutory carve-outs."
        ),
        "red_flags": [
            "Assigns all inventions regardless of when or how created",
            "No carve-out for personal-time inventions unrelated to company business",
            "Includes a 'prior inventions' schedule but doesn't actually allow for it",
            "Covers future inventions without temporal limitation",
        ],
    },
    "Indemnification": {
        "market_standard": (
            "Mutual indemnification for breach of representations and third-party IP infringement. "
            "Employee/vendor indemnifies company for gross negligence or willful misconduct. "
            "Caps typically tied to fees paid or insurance limits."
        ),
        "red_flags": [
            "One-sided indemnification favoring company",
            "Uncapped indemnification obligation",
            "Covers ordinary negligence, not just gross negligence or willful misconduct",
            "No insurance requirement to back the indemnification",
        ],
    },
    "Limitation of Liability": {
        "market_standard": (
            "Mutual cap on direct damages equal to fees paid in the preceding 12 months. "
            "Exclusion of consequential, indirect, and punitive damages. "
            "Carve-outs for IP indemnification, confidentiality breaches, and willful misconduct."
        ),
        "red_flags": [
            "One-sided cap (only limits one party's liability)",
            "No cap on liability at all",
            "Carve-outs that effectively eliminate the cap for routine commercial disputes",
            "Employee bears unlimited liability for any breach",
        ],
    },
    "Termination": {
        "market_standard": (
            "At-will for employees (US). Notice periods of 2-4 weeks for standard roles, longer for senior positions. "
            "Termination for cause requires material breach with opportunity to cure. "
            "Severance provisions for termination without cause."
        ),
        "red_flags": [
            "No notice period for termination",
            "Extremely broad definition of 'cause'",
            "No opportunity to cure alleged breach",
            "No severance for termination without cause",
            "Company can terminate for any reason with no obligations",
        ],
    },
    "Governing Law": {
        "market_standard": (
            "Governing law clause is standard. Should match the state where the employee works or the company is headquartered. "
            "Exclusive jurisdiction clauses should specify a convenient forum."
        ),
        "red_flags": [
            "Governing law in a jurisdiction that severely limits employee rights (e.g., non-compete enforceability varies dramatically by state)",
            "Requires disputes to be litigated in an inconvenient forum",
            "Waiver of jury trial in a one-sided manner",
        ],
    },
    "Arbitration": {
        "market_standard": (
            "Mandatory arbitration is common but contested. If present: should be AAA/JAMS administered, "
            "company pays arbitration fees beyond filing fee, individual (not class) arbitration, "
            "right to representation by counsel."
        ),
        "red_flags": [
            "Class action waiver combined with mandatory arbitration",
            "Employee bears all arbitration costs",
            "Arbitration clause is one-sided (company retains right to go to court)",
            "No specified rules or arbitrator selection process",
        ],
    },
    "At-Will Employment": {
        "market_standard": (
            "Standard at-will employment language in US contexts. "
            "No implied contract of continued employment. "
            "Should be balanced with any representations made during hiring."
        ),
        "red_flags": [
            "Contradicted by offer letter language suggesting job security",
            "Missing entirely from agreements in at-will states (ambiguity risk for employer)",
        ],
    },
}
