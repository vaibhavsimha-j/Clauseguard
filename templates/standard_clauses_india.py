"""
Indian jurisdiction legal standards.
Sources: Indian Contract Act 1872, Patents Act 1970, Copyright Act 1957,
Industrial Disputes Act 1947, Payment of Gratuity Act 1972,
Arbitration and Conciliation Act 1996 (as amended 2015/2019/2021),
Information Technology Act 2000, and established case law.
"""

JURISDICTION_CONTEXT = """
━━ JURISDICTION: INDIA ━━
Apply Indian law when assessing all clauses. The standards below are legally binding
frameworks — not just market norms.

1. NON-COMPETE
   Law: Section 27, Indian Contract Act 1872.
   Standard: Post-employment non-competes are VOID AND UNENFORCEABLE in India.
   Section 27 states "every agreement by which any one is restrained from exercising a
   lawful profession, trade or business of any kind, is to that extent void."
   Leading cases: Niranjan Shankar Golikari v Century Spinning (SC 1967),
   Percept D'Mark v Zaheer Khan (Bombay HC 2006).
   During-employment restrictions are valid.
   → CRITICAL finding for any post-employment non-compete regardless of duration or scope.
   Note to employee: clause is legally void — employer cannot enforce it in Indian courts,
   though they may still initiate litigation (harassment risk).

2. NON-SOLICITATION
   Law: Section 27 ICA 1872 (interpreted broadly by courts).
   Standard: Post-employment all-customer and all-employee non-solicitation is questionable.
   Narrow non-solicitation (only customers employee directly served, only active deals) may
   survive if it protects genuine trade secrets rather than restraining trade.
   During-employment restriction: fully valid.
   → MEDIUM (score 40-55): Broad post-employment non-solicitation covering ALL customers
   (including those the employee never worked with) and/or global scope. Questionable under
   Section 27 ICA but courts have sometimes upheld narrow versions — uncertainty makes this
   Medium, not High. Do NOT score broad non-solicitation as High.
   → LOW (score 15-35): Narrow non-solicitation limited to customers the employee personally
   served, active deals only, reasonable duration (≤12 months), limited geography.

3. CONFIDENTIALITY
   Law: Indian Contract Act 1872 (equitable principles), IT Act 2000 Section 72A,
   no standalone Trade Secrets Act (draft legislation pending as of 2024).
   Standard: Enforceable for genuine trade secrets without time limit. General confidential
   information: 2-3 years post-employment is reasonable. Must be mutual or have clear
   justification. One-sided, perpetual obligations for non-trade-secret information are
   unfavorable and may be challenged.
   → India scoring override: Do NOT score confidentiality as Critical. Indian courts apply
   equitable principles and would NOT enforce a perpetual obligation for general confidential
   information — they would limit it to a reasonable period (2-3 years). Immediate legal
   exposure is lower than in countries with strong trade secrets legislation.
   → HIGH (score 65-78): Perpetual, one-sided confidentiality with no exclusions for publicly
   known information or independently developed information.
   → MEDIUM (score 40-60): One-sided but with a defined (if long) post-employment period,
   or mutual but with missing exclusion carve-outs.

4. IP ASSIGNMENT
   Law: Copyright Act 1957 Section 17, Patents Act 1970.
   Standard: Copyright Act Section 17 — works created in the course of employment belong
   to the employer automatically (no separate assignment needed for copyrightable work).
   Patents Act — employee specifically hired to invent: employer owns the patent. General
   employee whose invention is incidental: employee may retain rights.
   Patent assignment must be in writing; recordal at the Indian Patent Office is advisable.
   → HIGH risk (score 65-75): Assignment covers inventions made outside working hours using
   personal resources, with no carve-out for personal-time work unrelated to company business.
   Even if partially unenforceable under Patents Act 1970, the employee still faces litigation
   risk and practical harassment. The clause creates a chilling effect on personal projects.
   → HIGH/CRITICAL risk (score 75-85): Same as above PLUS a post-employment assignment tail
   (e.g. any invention conceived within 1-2 years after termination). This extends beyond
   any reasonable employment scope and is a significant overreach.

5. TERMINATION AND NOTICE
   Law: Industrial Disputes Act 1947, Payment of Gratuity Act 1972,
   State Shops and Establishments Acts (state-specific).
   Standard: No US-style at-will employment — statutory protections apply.
   Gratuity mandatory after 5 years continuous service (15 days salary per year of service)
   under Payment of Gratuity Act 1972.
   Notice periods: State Shops Acts typically require 1 month (junior) to 3 months (senior).
   Industrial Disputes Act 1947 Section 25F: workmen cannot be retrenched without
   1 month notice + retrenchment compensation (15 days per year of service).
   Red flag: No notice period, no severance, no gratuity mention, immediate termination
   without cause for senior/long-tenured employees.

6. ARBITRATION
   Law: Arbitration and Conciliation Act 1996 (amended 2015, 2019, 2021).
   Standard: Seat of arbitration must be specified (typically an Indian city).
   Both parties share arbitration costs — market standard in India.
   Institutional arbitration preferred: Delhi International Arbitration Centre (DIAC),
   Mumbai Centre for International Arbitration (MCIA), or ICADR.
   Indian courts retain supervisory jurisdiction under Sections 34 and 37 of the Act.
   Class action arbitration is not standard in India.
   Red flag: Employee bears all costs; no seat specified; one party retains court access
   while the other is bound to arbitrate; foreign seat clause forcing Indian employee
   to arbitrate abroad.

7. LIMITATION OF LIABILITY
   Law: Section 73 and Section 74, Indian Contract Act 1872.
   Standard: Section 73 — damages must be direct and not remote. Section 74 — courts award
   only "reasonable compensation" regardless of what the contract stipulates; penalty clauses
   are not enforced as written. A nominal liability cap (e.g., Rs. 100) may be disregarded
   by courts in favour of actual loss. Mutual caps are market standard.
   Red flag: Nominal cap on company liability with no equivalent cap on employee; highly
   asymmetric caps that courts may override anyway under Section 74.

8. INDEMNIFICATION
   Law: Sections 124-125, Indian Contract Act 1872 (Contract of Indemnity).
   Standard: Indemnity contracts are valid. Section 74 limits recovery to "reasonable
   compensation" — punitive or liquidated penalty amounts are not enforced as written.
   One-sided, uncapped indemnification is unfavorable; courts will limit recovery to
   proven actual loss regardless.
   Red flag: Unlimited indemnification by employee with no reciprocal obligation on company.

9. GOVERNING LAW AND JURISDICTION
   Standard: Specify Indian law and courts in the relevant city (Mumbai, Bengaluru, Delhi,
   Hyderabad, Chennai, Pune). Exclusive jurisdiction clauses are enforceable. Foreign
   governing law clauses are generally valid between commercial parties but Indian courts
   will still apply mandatory Indian statutes (labour laws, consumer protection, etc.).
   Red flag: Clause requiring employee to litigate exclusively in a foreign country or
   distant Indian city with no connection to where work is performed.
   → India scoring: Do NOT score foreign governing law as Critical. Indian mandatory statutes
   (Industrial Disputes Act, Payment of Gratuity Act, Shops & Establishments Acts, labour laws)
   continue to apply regardless of the governing law clause — they cannot be stripped by contract.
   → HIGH (score 60-72): Foreign governing law (e.g. English law) AND exclusive foreign court
   jurisdiction. Creates a real practical barrier to justice but does not void statutory protections.
   → MEDIUM (score 40-58): Foreign governing law only, with Indian courts still having jurisdiction,
   or a distant Indian city with weak connection to where the employee works.

10. COMPENSATION AND BENEFITS (GENERAL)
   Standard in India: It is market-standard for Indian employment contracts to state that
   salary revisions are at the company's discretion. This means upward revisions are not
   guaranteed — it does NOT mean the company can unilaterally cut base salary (which would
   require employee consent under employment law principles).
   → STANDARD / NO RISK (score 0-15): Clause stating compensation may be revised at
   company's discretion, or that bonus/ESOP/variable pay is not guaranteed. This is normal
   boilerplate. Do NOT score this as Medium or High.
   → LOW (score 15-30): Only if the clause explicitly allows the company to REDUCE base
   salary unilaterally without employee consent, or removes all statutory deductions protections.
"""
