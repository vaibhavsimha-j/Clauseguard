"""
United States jurisdiction legal standards.
Sources: Federal Arbitration Act, Defend Trade Secrets Act 2016, Copyright Act 1976,
WARN Act, state employment laws (CA, NY, DE referenced specifically),
Uniform Trade Secrets Act, and established case law.
Note: US employment law varies significantly by state. Where state law diverges
materially, the most common commercial standard is noted.
"""

JURISDICTION_CONTEXT = """
━━ JURISDICTION: UNITED STATES ━━
Apply US law when assessing all clauses. Note that employment law varies by state —
California and Minnesota are most employee-protective; Delaware is standard for
corporate contracts.

1. NON-COMPETE
   Law: State law (no federal standard). FTC Rule (2024) attempted ban — check status.
   California: Business & Professions Code 16600 — non-competes are VOID (same as India).
   Most other states: enforceable if reasonable in duration, geography, and scope.
   Standard: ≤12 months, geography limited to where employee worked, direct competitors only.
   Adequate consideration required (new hire or material benefit for existing employee).
   Red flag: >2 years duration, worldwide or overly broad geography, covers entire industry,
   no adequate consideration, liquidated damages exceeding actual likely harm.
   → CRITICAL (score 88-100): Score CRITICAL if ANY ONE of these is present — do not
     downgrade to High even if other factors seem reasonable:
     • Employee location is California (or MN, ND, OK, ND) — clause is VOID under CA B&P
       Code 16600. Flag as Critical regardless of duration, scope, or other terms.
     • Contract explicitly says "notwithstanding [state] law" or "enforceable in all
       jurisdictions including California" — this signals the employer knows the clause
       is void and is attempting to override statute. Automatically Critical.
     • Nationwide or worldwide geographic scope.
     • Duration strictly greater than 2 years.
     • Liquidated damages amount exceeds $100,000.
   → HIGH (score 65-84): Enforceable jurisdiction, scope limited to region/industry,
     1-2 years duration, no oversize liquidated damages.
   → MEDIUM (score 40-60): Enforceable jurisdiction, reasonable geography, 6-12 months.

2. NON-SOLICITATION
   Standard: 12-24 months. Customers: limited to those employee directly worked with.
   Passive receipt of unsolicited inbound inquiries should be excluded.
   Employee non-solicitation: 12-18 months is market standard.

3. CONFIDENTIALITY
   Law: Defend Trade Secrets Act 2016 (federal), Uniform Trade Secrets Act (adopted by
   most states), state common law.
   Standard: Trade secrets: indefinite post-employment protection. General confidential
   information: 2-5 years post-employment. Mutual obligations preferred. Clear exclusions
   required: publicly available info, independently developed, rightfully received from
   third parties.
   Red flag: One-sided (only employee bound), no exclusions, perpetual obligation for all
   confidential information (not just trade secrets).

4. IP ASSIGNMENT
   Law: Copyright Act 1976 (work-made-for-hire), state statutes (CA Labor Code 2870,
   similar in DE, IL, MN, NC, WA).
   Standard: Must include carve-out for inventions made on personal time with no company
   resources and unrelated to company business. Work-made-for-hire covers copyrightable
   works created within the scope of employment.
   Red flag: No personal-time carve-out, assignment extends to pre-existing inventions
   without an exhibit listing them, assignment of future inventions with no temporal limit.
   → CRITICAL (score 85-95): No personal-time carve-out AND employee is in California
   (or CA, DE, IL, MN, NC, WA) where statutory carve-out protections exist. Contract
   explicitly waiving CA Labor Code Section 2870 or similar state statute is CRITICAL —
   statutory employee protections cannot be contractually waived.
   → HIGH (score 65-84): No personal-time carve-out in a state without a specific statute,
   or assignment extends beyond termination with no reasonable time limit.
   → MEDIUM (score 40-60): Carve-out present but poorly drafted or missing pre-existing
   invention exhibit.

5. TERMINATION AND NOTICE
   Law: At-will doctrine (most states), WARN Act (60 days for mass layoffs ≥100 employees).
   Standard: At-will employment is the legal default. No federally mandated individual notice
   period. Market standard: 2-4 weeks notice for junior/mid roles; 1-3 months for senior roles.
   Severance: not legally required but market standard for professional roles (typically
   1-2 weeks per year of service up to a cap).
   Red flag: No notice period at all, no severance regardless of tenure or role level,
   overly broad definition of "cause" that gives employer unchecked termination power.

6. ARBITRATION
   Law: Federal Arbitration Act (FAA), Epic Systems Corp v Lewis (SC 2018) upheld
   class action waivers.
   Standard: AAA or JAMS administered, employer pays arbitration fees beyond initial
   filing fee, individual arbitration, right to legal representation.
   Red flag: Employee bears all arbitration costs, class action waiver combined with
   company retaining unrestricted court access, no specified rules or arbitrator selection,
   non-appealable award clause.
   → CRITICAL (score 85-95): All three conditions together = CRITICAL: (1) employee bears
   ALL arbitration costs, AND (2) class action waiver, AND (3) company retains unrestricted
   court access while employee is bound to arbitrate. This combination strips the employee
   of all practical dispute resolution options.
   → CRITICAL (score 85-90): Even two of the above combined with a non-appealable award
   clause or no arbitrator selection process.
   → HIGH (score 65-84): One-sided cost allocation or class action waiver alone without
   the other aggravating factors.
   → MEDIUM (score 40-60): Mandatory arbitration with fair cost-sharing and no class waiver.

7. LIMITATION OF LIABILITY
   Standard: Mutual cap equal to fees paid in the preceding 12 months. Mutual exclusion
   of consequential, indirect, and punitive damages. Carve-outs for IP indemnification,
   confidentiality breaches, and willful misconduct are market standard.
   Red flag: One-sided cap (company capped, employee not), nominal cap amount ($100),
   carve-outs that effectively nullify the cap for routine commercial disputes.
   → CRITICAL (score 85-95): Company liability is capped at a nominal or token amount
   (e.g. $100, $500, $1,000) with NO equivalent cap on the employee's liability. Any cap
   under $10,000 for a professional employment contract should be treated as nominal/token
   and scored Critical. This is a fundamental asymmetry.
   → HIGH (score 65-84): Company cap is low but not nominal (e.g. 1 month of salary),
   or cap is mutual but with carve-outs that heavily favour one side.
   → MEDIUM (score 40-60): Mutual cap but set lower than market standard (below 12 months
   of fees/salary), or consequential damages excluded only on one side.

8. INDEMNIFICATION
   Standard: Mutual indemnification for breach of representations and third-party IP claims.
   Employee/vendor indemnifies company for gross negligence or willful misconduct only.
   Cap typically tied to fees paid or insurance limits.
   Red flag: One-sided (employee only), uncapped, covers ordinary negligence rather than
   gross negligence, no insurance requirement to support the indemnification obligation.

9. GOVERNING LAW AND JURISDICTION
   Standard: State law of incorporation (Delaware) or principal place of business.
   New York and California common for employment. Exclusive jurisdiction clauses are
   enforceable. Consider: courts in the governing state must apply that state's employee
   protection laws, which may override some contract terms.
   Red flag: Inconvenient forum requiring employee to litigate far from where they work,
   one-sided jury trial waiver.
"""
