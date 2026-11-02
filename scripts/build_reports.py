"""Rebuild research paper, executive summary, and supporting figures from source data.
Requires: pandas numpy matplotlib python-docx; run from project root with:
    python scripts/build_reports.py
Generated reports are analysis of an academic case study, not company accounts.
"""
from __future__ import annotations
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analytics import clean_data, summary, product_metrics, division_metrics, monthly_metrics, products_to_80_pct
OUT=ROOT/'reports'; CHARTS=ROOT/'charts'; OUT.mkdir(exist_ok=True);CHARTS.mkdir(exist_ok=True)
d,a=clean_data(ROOT/'data'/'Nassau_Candy_Distributor.csv'); s=summary(d); p=product_metrics(d); dv=division_metrics(d); mo=monthly_metrics(d)
BROWN='#9b5a38'; BLUE='#47636f'; GOLD='#dfad48'; TEXT='#28241f'; MUTED='#69594d'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.right':False,'axes.spines.top':False,'axes.labelcolor':TEXT,'text.color':TEXT,'xtick.color':MUTED,'ytick.color':MUTED, 'axes.titleweight':'bold','figure.facecolor':'white','axes.facecolor':'white'})

def savefig(name):
    plt.tight_layout(pad=2)
    plt.savefig(CHARTS/name,dpi=175,bbox_inches='tight',facecolor='white');plt.close()

# Figure 1: division comparison
fig,ax=plt.subplots(figsize=(8.6,3.45))
x=np.arange(len(dv));w=.37
ax.bar(x-w/2,dv['Revenue']/1000,width=w,label='Revenue',color=GOLD)
ax.bar(x+w/2,dv['Profit']/1000,width=w,label='Gross profit',color=BLUE)
ax.set_xticks(x,dv.Division);ax.set_ylabel('Assumed USD, thousands');ax.set_title('Revenue and gross profit by product division',loc='left');ax.legend(frameon=False)
for i,(r,pr) in enumerate(zip(dv.Revenue,dv.Profit)):
    ax.text(i-w/2,r/1000+1,f'{r/1000:.1f}',ha='center',fontsize=9)
    ax.text(i+w/2,pr/1000+1,f'{pr/1000:.1f}',ha='center',fontsize=9)
ax.set_ylim(0,145)
savefig('01_division_financials.png')

# Figure 2: top products; shrink labels
fig,ax=plt.subplots(figsize=(9,4.6))
t=p.sort_values('Profit').tail(8)
ax.barh(t['Product Name'],t['Profit']/1000,color=[BROWN if di=='Chocolate' else BLUE for di in t.Division]);ax.set_xlabel('Gross profit (assumed USD, thousands)')
ax.set_title('Highest gross-profit contributing products',loc='left');
for i,v in enumerate(t['Profit']/1000):ax.text(v+.15,i,f'{v:.1f}',va='center',fontsize=9)
ax.set_xlim(0,23)
savefig('02_product_leaderboard.png')

# Figure 3: pareto
fig,ax=plt.subplots(figsize=(9.2,3.7));ranked=p.sort_values('Profit',ascending=False).reset_index(drop=True)
x=np.arange(1,len(ranked)+1); cum=ranked.Profit.cumsum()/ranked.Profit.sum()*100
ax.bar(x,ranked.Profit/1000,color=BROWN,alpha=.85);ax.set_ylabel('Gross profit (assumed USD, thousands)');ax.set_xlabel('Product rank (1 = most profit)');ax.set_xticks(x);ax.set_title('Product concentration: gross profit Pareto',loc='left')
ay=ax.twinx();ay.plot(x,cum,color=BLUE,linewidth=2.5,marker='o',markersize=4);ay.axhline(80,color='#b45a2a',linestyle='--',linewidth=1.4);ay.set_ylim(0,105);ay.set_ylabel('Cumulative gross profit (%)');ax.axvspan(0.5,5.5,alpha=.05,color=GOLD)
savefig('03_pareto.png')

# Figure 4: margin vs revenue
fig,ax=plt.subplots(figsize=(9.0,3.8))
for divn,color in [('Chocolate',BROWN),('Other',BLUE),('Sugar',GOLD)]:
    z=p[p.Division==divn];ax.scatter(z['Revenue'],z['Gross Margin (%)'],s=np.sqrt(z['Transactions'])*19+50,c=color,label=divn,alpha=.84,edgecolor='white',linewidth=.8)
ax.axhline(50,color='#ac4f32',ls='--',lw=1.3); ax.annotate('Illustrative 50% risk threshold',(16000,52),fontsize=9,color='#ac4f32');
kk=p[p['Product Name']=='Kazookles'].iloc[0]
ax.annotate('Kazookles: 7.69% margin',(kk.Revenue,kk['Gross Margin (%)']),xytext=(4000,18),arrowprops={'arrowstyle':'->','color':BLUE},fontsize=9)
ax.set_xlabel('Product revenue (assumed USD)');ax.set_ylabel('Weighted gross margin (%)');ax.set_ylim(0,90);ax.set_title('Margin risk differs from sales volume',loc='left');ax.legend(frameon=False,ncol=3)
savefig('04_margin_diagnostics.png')

# Figure 5: temporal
fig,ax=plt.subplots(figsize=(9.2,3.65))
ax.plot(mo.Month,mo.Revenue/1000,color=BROWN,linewidth=2,marker='o',markersize=3,label='Revenue')
ax.plot(mo.Month,mo.Profit/1000,color=BLUE,linewidth=2,marker='o',markersize=3,label='Gross profit')
ax.set_title('Monthly performance, Jan 2024 – Dec 2025',loc='left');ax.set_ylabel('Assumed USD, thousands');ax.grid(axis='y',alpha=.16);ax.legend(frameon=False,ncol=2)
fig.autofmt_xdate()
savefig('05_monthly_performance.png')


def set_cell_shading(cell, fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd');shd.set(qn('w:fill'),fill);tcPr.append(shd)

def make_doc(title,subtitle,filename,short=False):
    doc=Document();sec=doc.sections[0];sec.top_margin=Inches(.72);sec.bottom_margin=Inches(.7);sec.left_margin=Inches(.82);sec.right_margin=Inches(.82)
    styles=doc.styles; normal=styles['Normal'];normal.font.name='Aptos';normal.font.size=Pt(10.2);normal.font.color.rgb=RGBColor(49,43,39)
    normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.line_spacing=1.13
    for name,size in [('Title',25),('Heading 1',16),('Heading 2',12)]:
        st=styles[name];st.font.name='Aptos Display' if name!='Heading 2' else 'Aptos';st.font.size=Pt(size);st.font.color.rgb=RGBColor(93,57,41);st.font.bold=True
        st.paragraph_format.space_before=Pt(12 if name!='Title' else 4);st.paragraph_format.space_after=Pt(7)
    h=sec.header.paragraphs[0];h.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    r=h.add_run('NASSAU CANDY  /  ACADEMIC CASE STUDY');r.font.size=Pt(8);r.font.color.rgb=RGBColor(133,114,101)
    f=sec.footer.paragraphs[0];f.alignment=WD_ALIGN_PARAGRAPH.CENTER
    run=f.add_run('Profitability & margin analysis  •  Illustrative dataset  |  Page ');run.font.size=Pt(8);run.font.color.rgb=RGBColor(133,114,101)
    fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');f._p.append(fld)
    return doc

def add_p(d,text='',bold_head=None):
    pa=d.add_paragraph()
    if bold_head and text.startswith(bold_head):pa.add_run(bold_head).bold=True;pa.add_run(text[len(bold_head):])
    else:pa.add_run(text)
    return pa

def bullets(d,items):
    for item in items:
        p0=d.add_paragraph(style='List Bullet');p0.add_run(item)

def add_table(d,head,rows,widths=None):
    tab=d.add_table(rows=1,cols=len(head));tab.style='Light Shading Accent 1';tab.alignment=WD_TABLE_ALIGNMENT.CENTER
    for j,val in enumerate(head):
        c=tab.rows[0].cells[j];c.text=str(val);set_cell_shading(c,'5D3929');
        for rr in c.paragraphs[0].runs:rr.font.bold=True;rr.font.color.rgb=RGBColor(255,255,255);rr.font.size=Pt(9)
    for i,row in enumerate(rows):
        rc=tab.add_row().cells
        for j,val in enumerate(row):
            rc[j].text=str(val)
            if i%2==1:set_cell_shading(rc[j],'FFF6EC')
            for para in rc[j].paragraphs:
                para.paragraph_format.space_after=Pt(2)
                for rr in para.runs:rr.font.size=Pt(8.7)
    d.add_paragraph().paragraph_format.space_after=Pt(0)
    return tab

def figure(d,name,caption,width=6.35):
    pa=d.add_paragraph();pa.alignment=WD_ALIGN_PARAGRAPH.CENTER
    pa.add_run().add_picture(str(CHARTS/name),width=Inches(width))
    ca=d.add_paragraph(caption);ca.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for r in ca.runs:r.font.italic=True;r.font.size=Pt(8.5);r.font.color.rgb=RGBColor(110,97,88)

def page(d):d.add_page_break()

def money(x):return f'${x:,.2f}'

def pct(x):return f'{x:.2f}%'

# Research paper
paper=make_doc('Product Line Profitability & Margin Performance Analysis','',OUT/'research_paper.docx')
paper.add_heading('Product Line Profitability &\nMargin Performance Analysis',0)
sub=paper.add_paragraph('Nassau Candy Distributor  |  Exploratory data analysis and decision recommendations');sub.style='Subtitle'
paper.add_paragraph('Prepared 30 October 2026  •  Dataset period: 02 January 2024 – 31 December 2025')
paper.add_paragraph('Research report · Version 1.0 · Academic case study')
paper.add_heading('Abstract',1)
add_p(paper,f"This study evaluates the profitability of {s['products']} product lines across {s['divisions']} divisions using {s['rows']:,} supplied transaction-line records. The dataset totals {money(s['revenue'])} in sales and {money(s['profit'])} in gross profit, yielding a weighted gross margin of {pct(s['gross_margin_pct'])}. Chocolate contributes {pct(dv.loc[dv.Division=='Chocolate','Profit Contribution (%)'].iloc[0])} of observed gross profit. The analysis identifies extreme product concentration, division-level revenue–profit imbalances, and a low-margin product warranting commercial review. An interactive Streamlit dashboard accompanies this report.")
paper.add_heading('Research questions',1)
bullets(paper,['Which products lead gross-profit contribution, margin, and unit economics?','How do division revenue, gross profit, and weighted margin compare?','What share of products drives 80% of revenue and 80% of profit?','Which products merit pricing or sourcing review, and how reliable are the trends?'])
paper.add_heading('Scope and provenance',1)
add_p(paper,'This is an analysis of a user-supplied assignment CSV, not independently verified financial records of Nassau Candy Distributors, Inc. The file contains Wonka-themed product names and should be regarded as illustrative. The official Nassau Candy website is used solely to contextualize the broad wholesale-confectionery business; the website does not authenticate these transactions. The source file contains no currency code; USD is used as a reporting assumption.')
page(paper)

paper.add_heading('1. Data and methodology',1)
add_p(paper,'The unit of observation is a transaction/product line. There are 10,194 lines across 8,549 distinct order identifiers. Order Date is parsed as day-first (DD-MM-YYYY); observations span 24 calendar months in 2024–2025. The 15 product IDs are grouped under Chocolate, Other, and Sugar.')
paper.add_heading('1.1 Data cleaning & validation',2)
bullets(paper,[f"Checked the original {a['source_rows']:,} rows for invalid dates, missing financial fields, sales ≤ 0, costs < 0, and Gross Profit ≠ Sales − Cost (tolerance $0.011).",f"Excluded {a['excluded_rows']:,} invalid rows; retained {a['retained_rows']:,}. No invalid or inconsistent records were detected.",'Normalized whitespace in product names and standardized division case; retained 15 distinct products.','Rows with zero/missing units would remain in financial aggregates but not in per-unit denominators; none were detected in this file.','Retained valid negative gross profits when present, because loss-making products are substantive risk signals; none appear in this file.'])
paper.add_heading('1.2 KPI definitions',2)
add_table(paper,['Indicator','Definition / interpretation'],[
('Gross margin (%)','Σ gross profit ÷ Σ sales × 100, revenue-weighted'),('Profit per unit','Σ gross profit ÷ Σ valid units'),('Revenue contribution','Product revenue ÷ portfolio revenue × 100'),('Profit contribution','Product gross profit ÷ portfolio gross profit × 100'),('Margin volatility','Sample SD (percentage points) of monthly weighted product margins'),('80% concentration','Smallest count of ranked products whose cumulative contribution reaches ≥80%')])
add_p(paper,'Gross Profit is supplied by the CSV and reconciled to Sales − Cost. The cost column is described as manufacturing cost, so all profitability conclusions concern gross profit only. They exclude transport, selling, administrative, marketing, financing and tax expenses.')
paper.add_heading('1.3 Filtering and risk rules',2)
add_p(paper,'The dashboard supports date range, division selection, product-name search, gross-margin threshold, and minimum-revenue risk exposure. The default 50% low-margin threshold and $1,000 material-revenue cutoff are demonstration settings, not benchmark policies validated for Nassau Candy. “High sales / low margin” requires both margin below threshold and revenue in the top quartile of the current product selection.')
page(paper)

paper.add_heading('2. Portfolio financial baseline',1)
add_table(paper,['Portfolio KPI','Dataset result'],[
('Transaction lines',f"{s['rows']:,}"),('Unique orders',f"{a['unique_order_ids']:,}"),('Products / divisions',f"{s['products']} / {s['divisions']}"),('Sales (assumed USD)',money(s['revenue'])),('Manufacturing/direct cost',money(s['cost'])),('Gross profit',money(s['profit'])),('Weighted gross margin',pct(s['gross_margin_pct'])),('Gross profit per unit',money(s['profit_per_unit']))])
paper.add_heading('2.1 Financial performance by division',2)
add_table(paper,['Division','Sales','Gross profit','Margin','Profit share'],[[r.Division,money(r.Revenue),money(r.Profit),pct(r['Gross Margin (%)']),pct(r['Profit Contribution (%)'])] for _,r in dv.iterrows()])
figure(paper,'01_division_financials.png','Figure 1. Revenue versus gross profit by division. Values derive exclusively from the supplied CSV.',width=6.25)
add_p(paper,'Chocolate accounts for 9,844 of 10,194 lines (96.57%) and 95.06% of gross profit. Other earns a 44.84% weighted gross margin versus 67.45% for Chocolate; Sugar has only 40 rows, making its apparent 66.61% gross margin an especially weak basis for broad inference.')
page(paper)

paper.add_heading('3. Product-level profitability',1)
add_p(paper,'The five chocolate-bar products dominate absolute profits. Their profit ranking is not identical to a gross-margin ranking; absolute contribution depends jointly on volume, selling price and unit economics.')
add_table(paper,['Product','Gross profit','Gross margin','Profit/unit'],[[r['Product Name'],money(r.Profit),pct(r['Gross Margin (%)']),money(r['Profit/Unit'])] for _,r in p.head(5).iterrows()])
figure(paper,'02_product_leaderboard.png','Figure 2. Eight highest contributors to portfolio gross profit.',width=6.15)
add_p(paper,'Highest individual contribution: Wonka Bar - Scrumdiddlyumptious with $19,357.50 profit (20.72% of the portfolio). Highest margin overall: Everlasting Gobstopper at 80%, but this figure is based on only three transaction rows and $130 in revenue. This is not equivalent to being the best-performing commercial product.')
page(paper)

paper.add_heading('4. Profit concentration and dependency risk',1)
add_p(paper,f"The five largest gross-profit products contribute {pct(p.head(5).Profit.sum()/s['profit']*100)} of all gross profit. They also account for {pct(p.head(5).Revenue.sum()/s['revenue']*100)} of sales. For both revenue and gross profit, {products_to_80_pct(p,'Profit')} of the {len(p)} products are sufficient to pass the 80% concentration threshold. That is 33.3% of products—not an exact 80/20 pattern, but marked concentration nonetheless.")
figure(paper,'03_pareto.png','Figure 3. Product-level profit ranking and cumulative concentration.',width=6.25)
paper.add_heading('Interpretation',2)
bullets(paper,['Dependence on a narrow Chocolate portfolio makes total profit sensitive to changes in those products’ demand, pricing or cost.','Evaluate inventory availability, supply continuity and promotional discount effects on the five leaders.','Do not discontinue lower-revenue products purely because they fall outside the top 80%; they may serve assortment, market-access or cross-selling roles.'])
page(paper)

paper.add_heading('5. Cost structure and margin risk',1)
add_p(paper,'Product-level sales and manufacturing/direct costs are compared to identify cases where costs absorb an unusually large fraction of revenue. The default 50% margin threshold is illustrative and can be changed in the Streamlit app.')
figure(paper,'04_margin_diagnostics.png','Figure 4. Weighted gross margin versus revenue by product (bubble size reflects row count).',width=6.3)
lo=p.sort_values('Gross Margin (%)').head(5)
add_table(paper,['Product','Sales','Gross margin','Rows'],[[r['Product Name'],money(r.Revenue),pct(r['Gross Margin (%)']),f"{int(r.Transactions):,}"] for _,r in lo.iterrows()])
add_p(paper,'Kazookles has $1,205.75 of revenue, $1,113.00 of cost and only $92.75 of gross profit: a 7.69% margin over 96 rows. This is the clearest material-margin review candidate. Fun Dip (40.00% margin), Nerds (46.67%) and SweeTARTS (46.67%) are also below the 50% illustrative threshold but have very low observed revenue and sample sizes.')
add_p(paper,'Recommendation: review Kazookles input costs, selling price and discounting first; validate competitive constraints, demand elasticity and fuller cost allocation before considering repricing or delisting.')
page(paper)

paper.add_heading('6. Time trend and volatility',1)
figure(paper,'05_monthly_performance.png','Figure 5. Monthly revenue and gross profit based on order dates; no seasonality attribution is inferred.',width=6.35)
y=d.groupby('Year',as_index=False).agg(Sales=('Sales','sum'),Profit=('Gross Profit','sum'))
add_table(paper,['Year','Sales','Gross profit','Weighted margin'],[[int(r.Year),money(r.Sales),money(r.Profit),pct(r.Profit/r.Sales*100)] for _,r in y.iterrows()])
add_p(paper,'Revenue is higher in 2025 than in 2024, but the dataset alone does not explain the increase. Monthly totals reflect order volume and any sampling process; external macroeconomic or commercial causes must not be inferred.')
paper.add_heading('6.1 Why margin volatility rounds to zero',2)
add_p(paper,'All 15 products exhibit approximately zero standard deviation in monthly weighted gross margins (floating-point deviations below 0.0000000001 percentage points). This follows from near-fixed unit pricing and costs embedded in the case dataset. It does not demonstrate stable real-world procurement or selling economics. Monthly metrics are computed only in months with observed sales for each product.')
paper.add_heading('6.2 Data limitations',2)
bullets(paper,['The product names and case-study structure are not authenticated as Nassau Candy’s actual commercial product portfolio.','The source does not report discounts, tax, freight, overhead, customer acquisition cost, or realized net profit; observed gross margin must not be interpreted as net margin.','Severely uneven division counts (Chocolate 9,844; Other 310; Sugar 40) weaken cross-division generalization.','No source currency metadata or independent audit trail is provided; USD is an explicit presentation assumption.','Product-specific margin constancy constrains volatility and pricing-sensitivity inference.'])
page(paper)

paper.add_heading('7. Recommendations and staged implementation',1)
add_table(paper,['Priority','Suggested action','Success indicator'],[
('Immediate','Review Kazookles pricing, direct material cost and transactional terms; confirm data integrity.','Unit contribution and gross-margin uplift'),
('Near-term','Protect supply and monitor prices for the five Chocolate gross-profit leaders.','Leader availability, share and margin'),
('Near-term','Investigate Other division cost mix and contribution by SKU.','Weighted division margin, not simple mean'),
('Ongoing','Use dashboard filters to watch monthly sales/profit, and test scenarios after adding real costs.','Monthly margin and profit by SKU'),
('Governance','Confirm whether data is representative before presenting any finding as a company fact.','Documented source provenance')])
paper.add_heading('8. Conclusion',1)
add_p(paper,f"The supplied case dataset indicates substantial gross-profit concentration in five Chocolate products, alongside an overall weighted gross margin of {pct(s['gross_margin_pct'])}. Kazookles is the most material low-margin review opportunity. A repeatable Streamlit dashboard and validated KPI definitions support exploratory product and division decisions, but further verified accounting, fulfillment and pricing data are essential before implementing changes or claiming this represents actual Nassau Candy performance.")
paper.add_heading('References / source notes',1)
bullets(paper,['Nassau Candy Distributors, Inc. Official website, https://www.nassaucandy.com/ (accessed 30 October 2026): business context only.','Nassau Candy. Confections catalog, https://www.nassaucandy.com/confections.html (accessed 30 October 2026): product-category context only.','User-supplied academic data file: Nassau Candy Distributor (2).csv; 10,194 records; not a verified corporate financial statement.','Project brief supplied by the user: “Product Line Profitability & Margin Performance Analysis for Nassau Candy Distributor.”'])
paper.add_paragraph('Research-status disclosure: this document is an original analytical project report, not a peer-reviewed or approved/published research article.')
paper.save(OUT/'Nassau_Product_Profitability_Research_Paper.docx')

# Executive summary for stakeholders
ex=make_doc('Executive Summary','',OUT/'executive_summary.docx',short=True)
ex.add_heading('Executive Summary',0)
sub=ex.add_paragraph('Product Line Profitability & Margin Performance');sub.style='Subtitle'
ex.add_paragraph('Nassau Candy Distributor | Academic demonstration | 30 October 2026')
ex.add_heading('Decision brief',1)
add_p(ex,'Purpose: provide an audit-friendly view of product and division gross profitability to inform pricing, sourcing, assortment and portfolio concentration discussions. This summary uses a supplied illustrative dataset rather than verified corporate accounts. Values are presented in assumed USD.')
add_table(ex,['Measure','Result'],[
('Source transaction lines',f"{s['rows']:,} (2024–2025)"),('Products / divisions',f"{s['products']} / {s['divisions']}"),('Total sales',money(s['revenue'])),('Total gross profit',money(s['profit'])),('Weighted gross margin',pct(s['gross_margin_pct'])),('Profit from five Chocolate leaders',pct(p.head(5).Profit.sum()/s['profit']*100))])
ex.add_heading('Three findings that matter',1)
bullets(ex,['Profit depends heavily on Chocolate: five Chocolate products generate 95.06% of gross profit. Concentration risk is more significant than the simple count of available products suggests.','The Other division has a weaker 44.84% weighted gross margin compared with Chocolate at 67.45%; this is descriptive, not proof of operational underperformance.','Kazookles has a 7.69% gross margin on $1,205.75 in sales, making it the clearest product-level direct-cost or pricing review candidate.'])
ex.add_heading('Immediate actions',1)
add_table(ex,['Timeframe','Recommendation'],[
('0–30 days','Validate source/contract prices and direct costs for Kazookles; consider repricing, renegotiating sourcing or targeted promotion changes.'),
('0–60 days','Monitor supply and discounts for the five highest-profit Chocolate products; protect contribution without creating excess portfolio dependency.'),
('30–90 days','Review Other division mix and identify opportunities to improve gross margin while safeguarding demand.'),
('Ongoing','Use the dashboard to monitor product-level gross margin and profit concentration on each data refresh.')])
page(ex)
ex.add_heading('Delivery for oversight and decision-making',1)
add_p(ex,'The accompanying Streamlit dashboard includes a product leaderboard, division performance, sales-versus-cost diagnostics, low-margin flags, an 80% concentration/Pareto view and filters for date, division, product name and margin threshold. CSV exports make all product- and division-level calculations reproducible.')
figure(ex,'01_division_financials.png','Division-level financial profile from the supplied dataset.',width=6.15)
ex.add_heading('Governance and key caveats',1)
bullets(ex,['The source product labels are Wonka-themed. They must not be described as the current commercial products sold by Nassau Candy without independent verification.','The dataset’s gross profit excludes unprovided logistics, marketing, overhead and tax; the figures are not net profitability estimates.','Sugar is represented by only 40 transaction rows, and month-to-month margin volatility is near zero due to fixed dataset unit economics.','Official Nassau Candy website information supplies corporate context only, not evidence supporting the dataset numbers.','This is a course-project executive summary for public-sector/governance-style stakeholders; it is not an official statement by Nassau Candy or a government agency.'])
ex.add_heading('Recommended decision',1)
add_p(ex,'Approve this dashboard as a reproducible *exploratory case study*, and commission verification of company-specific sales, cost, allocation and product-master data before acting on pricing, procurement or discontinuation recommendations.')
ex.add_paragraph('Sources: user-provided assignment CSV and brief; Nassau Candy (https://www.nassaucandy.com/, accessed 30 October 2026) for general company context only.')
ex.save(OUT/'Nassau_Product_Profitability_Executive_Summary.docx')
print('Created charts and DOCX reports in',ROOT)
