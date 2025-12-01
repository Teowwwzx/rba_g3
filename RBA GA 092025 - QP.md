

AQ098-3-3-RBA       Group Assignment                                   Page 1 of 6
APU Level 3                               Asia Pacific University of Technology & Innovation                                20251117
Group Assignment: Balancing Risk and Return for Equity Fund

## Objective
To design and analyze a robo advisor portfolio optimization model using 50 ACE market stocks
from  Bursa  Malaysia.  Students  will  apply  quantitative  methods  to  construct  both  a  minimum-
volatility  portfolio  and  an  optimal  return  portfolio  under  a  risk  cap,  evaluate  performance  using
return,  volatility,  Sharpe  ratio,  and  Value-at-Risk,  and  interpret  the  financial  implications  of
algorithmic asset allocation within the Malaysian equity context.

## Mandate
An institutional client has sent a query regarding the proposed development of an equity portfolio
composed of the potential stocks listed in the ACE market. Nonetheless, they have outlined a few
requirements to be observed by your team:
i. The selected stock must record at least 0.25% average daily return for the past five (5)
years.
ii. The FBMKLCI is used as the benchmark index.
iii. Malaysia 10-Year Government Bond yield.
iv. Sharpe ratio must be not less than 2.0.
v. Daily Value-at-Risk (VaR) must be capped at -1.5% maximum.
vi. A scenario analysis of the performance summary based on the annual volatility capped
at 5%, 10% and 20%
vii. A  scenario  analysis  of  the  performance  summary  based  on  the  maximum component
weights of 10%, 20% and 30%.
viii. A final recommendation of the best equity portfolio.

Your  team  must  present  a  comprehensive  portfolio  analysis  that  complies  with  the
mandate, compares scenario outcomes, and concludes with a justified recommendation
of the optimal equity portfolio configuration. The final deliverable must include a written
report with a data summary, methodology, results, and interpretation.

AQ098-3-3-RBA       Group Assignment                                   Page 2 of 6
APU Level 3                               Asia Pacific University of Technology & Innovation                                20251117
## Required:
Using the constrained Mean-Variance Optimization (MVO), your group must:
- Identify 50 ACE Market stocks from Bursa Malaysia.
- Prepare a clean price dataset of:
o the daily closing prices for the 50 selected ACE Market stocks,
o the FBMKLCI as the benchmark,
o and the Malaysia 10-Year Government Bond yield.
The dataset must cover at least six (6) years of historical daily data.
- Arrange  and  organise  the  data  chronologically  to  ensure a consistent  time  series  for  all
assets.
- Integrate the provided Python script into your analysis environment and explain the purpose
of each function in financial terms.
- Formulate the portfolio scenarios by altering parameters such as the volatility cap and per-
asset cap.
- Compare and balance the outcomes for return, volatility, Sharpe ratio, and Value-at-Risk
across the three scenarios.
- Combine  findings  to  synthesise  insights  on  diversification,  portfolio  efficiency,  and  the
effect of constraints.
- Relate the optimised portfolios to market conditions and generalise their implications for
Robo-Advisory investment strategies.
- Defend  your  interpretations  with  sound  financial  reasoning  supported  by  quantitative
evidence.
- Organise all outputs, tables, and figures clearly within a structured group report.
- Complete the submission by ensuring that the report adheres to academic formatting and
referencing standards.

AQ098-3-3-RBA       Group Assignment                                   Page 3 of 6
APU Level 3                               Asia Pacific University of Technology & Innovation                                20251117
Submission requirements
- Report Structure and Formatting
a) Organise the final report with a professional layout and consistent formatting.
b) Use clearly labelled tables, figures, and sections.
c) Apply APA 7th edition citation style for all references.
d) The report must include:
o Python code (clean and clearly labelled for each section)
o Raw and cleaned datasets used in the analysis
o Graphs  and  charts,  where  relevant  (e.g.,  Sharpe  ratio  comparison,  risk–return
plots, allocation visuals)
o Summary reflections interpreting each model output
## 2. Final Group Report
a) Length: approximately 2,000 words (±10%)
b) Limit: Maximum  10  pages,  excluding  the  table  of  contents,  abstract,  list  of  figures,
references, and appendices
c) Format: PDF (.pdf)
## 3. Python Code Files
a) Submit the full .ipynb notebook(s) used in the analysis.
b) Ensure that code sections are labelled consistently with the corresponding report sections.
## 4. Datasets
a) Submit both the raw dataset and the cleaned dataset in .csv or .xlsx format.
b) Datasets must include the 40 ACE Market stocks, FBMKLCI benchmark, and Malaysia
10-Year Government Bond Yield covering at least six years of daily data.
## 5. Referencing
- Cite  a minimum  of  five  credible  academic  or  professional  sources using APA  7th
edition formatting.
## 6. Cover Page Details
- Include student names, ID numbers, group ID, module code, and title on the cover page.


AQ098-3-3-RBA       Group Assignment                                   Page 4 of 6
APU Level 3                               Asia Pacific University of Technology & Innovation                                20251117
## Important Notes
- All portfolio analysis and interpretation must be based on your own selected dataset and
simulation  outputs.  Using  or  copying  interpretations  from  reference  examples  or  any
external content without proper citation will result in mark deductions.
- Your written discussion must be clear, well-reasoned, and supported by your group’s
actual results. Avoid generic commentary that does not align with your outputs.
- Your submission must include all calculations, portfolio weights, performance metrics,
and relevant evidence to support your analysis.
- Maintain a professional yet readable tone. Write as if you are explaining your findings to
an informed investor or decision-maker.
- A similarity  index  above  20% (as  flagged  by  Turnitin  or  any  institutional  plagiarism
detection  system)  will  result  in  a minimum  penalty  of  10%  deduction from  the  total
marks, subject to further review.
- Submissions  with AI  content  scores  exceeding 20% will  also  be  flagged.  If  content
appears  to  lack  genuine  student  analysis  or  critical  thinking,  additional  marks  may  be
deducted at the discretion of the module lecturer.

[Grand Total: 100 marks]

AQ098-3-3-RBA       Group Assignment                                   Page 5 of 6
APU Level 3                               Asia Pacific University of Technology & Innovation                                20251117
## RUBRIC
## Section Marks
## Band 5
## Excellent
## Band 4
## Strong
## Band 3
## Competent
## Band 2
## Limited
## Band 1
## Deficient
## A. Introduction
## & Mandate
## Interpretation
## 10
Demonstrates full
comprehension of
client brief and
portfolio objective;
clearly contextualises
ACE Market
selection, benchmark,
and risk-free rate; sets
a coherent analytical
direction.
## Interprets
mandate
accurately with
some lack of
depth or
conciseness.
## Describes
mandate but
lacks
precision or
connection to
portfolio
goals.
## Limited
awareness of
client objectives
or weak linkage
to methodology.
## Misinterpret
s mandate or
omits key
parameters.
## B. Data
## Integrity &
## Coding
## Implementation
## 20
Six-year dataset
complete (40 ACE
stocks, FBMKLCI,
10-year MGS); data
cleaning fully
transparent; Python
code modular,
annotated,
reproducible; outputs
consistent with
financial logic.
Minor data or
code
inconsistencies
; good
structure and
reproducibility.
## Adequate
dataset; basic
code without
full labeling
or
traceability.
## Incomplete
dataset or
inconsistent
output; weak
annotation.
Data invalid
or code non-
functional.
## C. Analytical
## Modelling &
## Quantitative
## Rigor
## 30
Executes full scenario
analysis across
volatility (5%, 10%,
20%) and weight
## (10%, 20%, 30%)
caps; computes
returns, volatilities,
Sharpe ratios, and
VaR precisely;
interprets results
through risk–return
optimization logic;
identifies feasible
frontier portfolios.
All scenarios
attempted;
correct
calculations
with partial
financial
interpretation.
## Some
scenarios
missing or
superficial
interpretation
; metrics
mostly
correct.
Limited or
inconsistent
analysis; errors
in calculations
or logic.
No valid
computation
or
conceptual
error
throughout.
## D. Financial
## Insight &
## Theoretical
## Application
## 30
Demonstrates deep
understanding of
portfolio theory,
diversification, and
constraint effects;
synthesises
quantitative findings
into robust financial
arguments; provides a
justified, risk-aware
final recommendation.
## Sound
understanding;
good reasoning
though lacking
synthesis or
nuance.
## Basic
theoretical
grounding;
interpretation
somewhat
mechanical.
## Weak
conceptual
application;
unclear
reasoning or
unsupported
recommendation
## .
## No
theoretical
linkage;
analysis
disconnected
from finance
principles.
## E. Report
## Structure,
## Visualisation &
## Referencing
## 10
## Professional
presentation; coherent
flow; visuals enhance
analysis (Sharpe,
VaR, allocation);
precise APA 7
citations with ≥ 5
credible sources;
language clear and
academic.
## Well-formatted
with minor
citation or
structural
issues.
## Adequate
layout;
limited
visuals or
inconsistent
referencing.
## Disorganised,
poor clarity, few
sources.
## Non-
compliant
formatting
or missing
references.
## Total 100

AQ098-3-3-RBA       Group Assignment                                   Page 6 of 6
APU Level 3                               Asia Pacific University of Technology & Innovation                                20251117


## END OF QUESTION PAPER
