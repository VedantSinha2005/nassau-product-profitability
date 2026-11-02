"""Product Line Profitability & Margin Performance Analysis | Streamlit dashboard.

Run: streamlit run app.py
Data is an educational assignment case study, NOT official Nassau Candy accounts.
"""
from __future__ import annotations
import io
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics import (clean_data, summary, product_metrics, division_metrics,
                       risk_flags, profit_pareto, products_to_80_pct, monthly_metrics)

DATA_FILE = Path(__file__).parent / 'data' / 'Nassau_Candy_Distributor.csv'
COLORS = {'Chocolate':'#9b5a38', 'Sugar':'#dfad48', 'Other':'#47636f'}
PLOT_CONFIG = {'displaylogo': False, 'modeBarButtonsToRemove': ['lasso2d','select2d']}

st.set_page_config(page_title='Nassau Candy | Product Profitability', page_icon='🍬', layout='wide', initial_sidebar_state='expanded')
st.markdown("""<style>
.block-container {padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1400px;}
h1,h2,h3{letter-spacing:-.025em} .stMetric {border:1px solid #edddd0; border-radius:14px; padding:14px; background:#fffaf5}
.hero {padding:1.4rem 1.6rem; border-radius:19px; background:linear-gradient(120deg,#3d2a2a 0%,#734b36 70%,#b37542 100%); color:white; margin-bottom:1.25rem}
.hero h1 {margin:.1rem 0 .3rem; color:white; font-size:2.05rem}
.hero p {margin:0; color:#f9e7d6; font-size:1.02rem}
.pill {display:inline-block; background:#f4dbb3; color:#422f27; padding:3px 11px; border-radius:99px; font-weight:650; font-size:.78rem}
.smallnote{background:#fff2dd; border-left:4px solid #b45a2a; padding:.7rem 1rem; border-radius:8px}
</style>""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_default():
    return clean_data(DATA_FILE)

@st.cache_data(show_spinner=False)
def load_uploaded(file_bytes):
    return clean_data(pd.read_csv(io.BytesIO(file_bytes)))

with st.sidebar:
    st.title('🍬 Analysis controls')
    st.caption('Interactive case-study dashboard')
    uploaded = st.file_uploader('Optional replacement CSV', type=['csv'], help='Use the same 18-column schema. Uploaded files stay in this session.')
try:
    data, audit = load_uploaded(uploaded.getvalue()) if uploaded is not None else load_default()
except (ValueError, UnicodeError, pd.errors.ParserError) as exc:
    st.error(f'Unable to process dataset: {exc}')
    st.stop()
if data.empty:
    st.error('No valid transaction records remain after cleaning.')
    st.stop()

with st.sidebar:
    first, last = data['Order Date'].min().date(), data['Order Date'].max().date()
    period = st.date_input('Order date range', (first,last), min_value=first, max_value=last, format='DD/MM/YYYY')
    divisions = st.multiselect('Product divisions', sorted(data.Division.unique()), default=sorted(data.Division.unique()))
    query = st.text_input('Product search', placeholder='e.g. Kazookles')
    cutoff = st.slider('Low-margin threshold (%)', min_value=0, max_value=100, value=50, step=1,
                       help='Products below this weighted gross-margin percentage are flagged.')
    min_revenue = st.number_input('Minimum revenue for priority risk flag', min_value=0.0, value=1000.0, step=250.0)
    st.divider()
    st.caption('Data source: uploaded assignment CSV. Figures are not verified Nassau Candy financial results. Currency shown as USD by assumption.')
    st.link_button('Nassau Candy — official website', 'https://www.nassaucandy.com/', use_container_width=True)

if not isinstance(period, (tuple,list)) or len(period) != 2:
    st.info('Select both a start and end date to continue.')
    st.stop()
filtered = data.loc[(data['Order Date'].dt.date>=period[0]) & (data['Order Date'].dt.date<=period[1]) & (data['Division'].isin(divisions))].copy()
if query.strip():
    filtered = filtered[filtered['Product Name'].str.contains(query.strip(),case=False,regex=False,na=False)]
if filtered.empty:
    st.warning('No records match the current filters. Broaden the date range or product/division selections.')
    st.stop()

k = summary(filtered); products = product_metrics(filtered); div = division_metrics(filtered)
products = risk_flags(products, margin_threshold=cutoff, min_revenue=min_revenue)
months = monthly_metrics(filtered)

st.markdown("""<div class='hero'><span class='pill'>PRODUCT FINANCE · CASE STUDY</span>
<h1>Product Line Profitability & Margin Performance</h1>
<p>Nassau Candy Distributor · Sales, costs, gross margins, profit concentration & portfolio risk</p></div>""", unsafe_allow_html=True)
st.caption(f"Analysis window: {period[0]:%d %b %Y} – {period[1]:%d %b %Y}  |  {k['rows']:,} source rows in current selection  |  {k['products']} products")
st.info('**Important:** Educational dataset with Wonka-themed product names; not verified Nassau Candy sales or financial disclosures. Gross profit excludes unprovided overhead, freight, marketing and tax costs.')

m1,m2,m3,m4,m5=st.columns(5)
m1.metric('Revenue (assumed USD)', f"${k['revenue']:,.2f}")
m2.metric('Gross profit',f"${k['profit']:,.2f}")
m3.metric('Weighted gross margin',f"{k['gross_margin_pct']:.2f}%")
m4.metric('Profit per unit', f"${k['profit_per_unit']:,.2f}" if np.isfinite(k['profit_per_unit']) else 'N/A')
m5.metric('Products below threshold', f"{int(products['Low Margin'].sum())} / {len(products)}")

t1,t2,t3,t4,t5,t6=st.tabs(['📊 Overview','🏆 Product profitability','🏭 Division performance','🔎 Cost & risk','📈 Pareto & concentration','📋 Data quality & exports'])

def style(fig, height=390):
    fig.update_layout(template='plotly_white', height=height, margin=dict(l=15,r=15,t=50,b=35), font=dict(family='Arial',size=12),
                      paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',hovermode='closest')
    return fig

with t1:
    st.subheader('Financial performance at a glance')
    left,right=st.columns([1.2,1])
    with left:
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=months.Month,y=months.Revenue, mode='lines+markers',name='Revenue',line_color='#b45a2a'))
        fig.add_trace(go.Scatter(x=months.Month,y=months.Profit, mode='lines+markers',name='Gross profit',line_color='#47636f'))
        fig.update_layout(title='Monthly revenue and gross profit',yaxis_title='Assumed USD',xaxis_title='Order month',legend=dict(orientation='h',y=1.12))
        st.plotly_chart(style(fig),use_container_width=True,config=PLOT_CONFIG)
    with right:
        fig=px.bar(div,x='Division',y=['Revenue','Profit'],barmode='group',title='Revenue vs. profit by division',color_discrete_sequence=['#dfad48','#47636f'],labels={'value':'Assumed USD','variable':'Measure'})
        st.plotly_chart(style(fig),use_container_width=True,config=PLOT_CONFIG)
    st.markdown('**How to interpret this dashboard:** all margins use `sum(Gross Profit) / sum(Sales)`; they are not unweighted averages of row or product margins. Use the filters to compare periods, divisions, or individual product names.')

with t2:
    st.subheader('Product profit leaderboard')
    l,r=st.columns([1.35,1])
    with l:
        top=products.sort_values('Profit',ascending=True)
        fig=px.bar(top,x='Profit',y='Product Name',orientation='h',color='Division',color_discrete_map=COLORS,title='Gross profit contribution by product',hover_data=['Gross Margin (%)','Revenue','Units'])
        fig.update_layout(yaxis_title='',xaxis_title='Gross profit (assumed USD)')
        st.plotly_chart(style(fig, max(440, 28*len(top)+135)),use_container_width=True,config=PLOT_CONFIG)
    with r:
        fig=px.scatter(products,x='Revenue',y='Gross Margin (%)',size='Transactions',color='Division',color_discrete_map=COLORS,
                       hover_name='Product Name',hover_data=['Profit','Profit/Unit','Margin Volatility (pp)'],title='Revenue vs. gross margin')
        fig.add_hline(y=cutoff,line_dash='dot',annotation_text=f'{cutoff}% threshold',line_color='#b45a2a')
        st.plotly_chart(style(fig,460),use_container_width=True,config=PLOT_CONFIG)
    st.markdown('**Product-level metrics**')
    table_cols=['Product Name','Division','Revenue','Cost','Profit','Gross Margin (%)','Profit/Unit','Revenue Contribution (%)','Profit Contribution (%)','Margin Volatility (pp)','Transactions']
    st.dataframe(products[table_cols].style.format({c:'{:,.2f}' for c in ['Revenue','Cost','Profit','Gross Margin (%)','Profit/Unit','Revenue Contribution (%)','Profit Contribution (%)','Margin Volatility (pp)']}),use_container_width=True,hide_index=True)
    selected=st.selectbox('Inspect product',products['Product Name'].to_list())
    prod=products.loc[products['Product Name']==selected].iloc[0]
    c1,c2,c3=st.columns(3)
    c1.metric('Product revenue',f"${prod['Revenue']:,.2f}")
    c2.metric('Product margin',f"{prod['Gross Margin (%)']:.2f}%")
    c3.metric('Profit share',f"{prod['Profit Contribution (%)']:.2f}%")

with t3:
    st.subheader('Division performance & margin structure')
    a,b=st.columns(2)
    with a:
        fig=px.bar(div,x='Division',y='Gross Margin (%)',color='Division',color_discrete_map=COLORS,title='Weighted gross margin by division',text_auto='.1f')
        fig.update_layout(showlegend=False,yaxis_title='Gross margin (%)')
        st.plotly_chart(style(fig),use_container_width=True,config=PLOT_CONFIG)
    with b:
        fig=px.bar(div,x='Division',y=['Revenue Contribution (%)','Profit Contribution (%)'],barmode='group',title='Revenue share vs profit share',labels={'value':'Share (%)','variable':'Measure'},color_discrete_sequence=['#dfad48','#47636f'])
        st.plotly_chart(style(fig),use_container_width=True,config=PLOT_CONFIG)
    st.dataframe(div.style.format({c:'{:,.2f}' for c in ['Revenue','Cost','Profit','Gross Margin (%)','Revenue Contribution (%)','Profit Contribution (%)']}),use_container_width=True,hide_index=True)
    st.caption('Small divisions may have very few records. Compare sample sizes before drawing structural conclusions; the data is dominated by Chocolate transactions.')

with t4:
    st.subheader('Cost-to-sales diagnostics & actionable margin flags')
    col1,col2=st.columns([1.2,1])
    with col1:
        fig=px.scatter(products,x='Revenue',y='Cost',size='Transactions',color='Gross Margin (%)',color_continuous_scale='RdYlGn',
                       hover_name='Product Name',hover_data=['Division','Profit','Units','Profit/Unit'],title='Product-level cost vs revenue')
        upper=max(products.Revenue.max(),products.Cost.max())*1.04
        fig.add_trace(go.Scatter(x=[0,upper],y=[0,upper],name='Break-even cost',line=dict(color='#a54444',dash='dash')))
        fig.add_trace(go.Scatter(x=[0,upper],y=[0,upper*(1-cutoff/100)],name=f'{cutoff}% margin line',line=dict(color='#b58437',dash='dot')))
        fig.update_layout(xaxis_title='Revenue (assumed USD)',yaxis_title='Direct cost (assumed USD)')
        st.plotly_chart(style(fig,470),use_container_width=True,config=PLOT_CONFIG)
    with col2:
        st.markdown(f'### Margin threshold: {cutoff}%')
        st.caption('Below the dotted line for a given revenue corresponds to a margin above the threshold. Low-margin products lie above the threshold line.')
        priority=products.loc[products['Risk Classification']!='Monitor'].sort_values(['Gross Margin (%)','Revenue'],ascending=[True,False])
        st.metric('Flagged products',len(priority))
        if priority.empty:
            st.success('No products fall below the chosen margin threshold.')
        else:
            st.dataframe(priority[['Product Name','Revenue','Gross Margin (%)','Risk Classification']].style.format({'Revenue':'{:,.2f}','Gross Margin (%)':'{:.2f}'}),hide_index=True,use_container_width=True)
        st.markdown('**Decision guidance:** inspect sourcing and pricing first; a low gross margin alone does not establish that a product should be discontinued. Validate demand elasticity, distribution expenses, and strategic importance.')
    st.markdown('**Risk categories:** below-threshold products with revenue above the user-selected minimum are priority reviews; high-sales/low-margin products are tagged when they also fall in the top revenue quartile. Thresholds are decision aids, not estimated corporate policy.')

with t5:
    st.subheader('Profit concentration / Pareto analysis')
    measure=st.radio('Rank by', ['Profit','Revenue'],horizontal=True)
    pareto=profit_pareto(products,metric=measure)
    count80=products_to_80_pct(products,metric=measure)
    st.metric(f'Products required to reach ≥80% of {measure.lower()}', f'{count80} of {len(products)}' if count80 is not None else 'N/A')
    if count80 is not None:
        st.caption(f'{count80/len(products)*100:.1f}% of listed products generate at least 80% of {measure.lower()} in the current selection.')
    fig=go.Figure()
    fig.add_trace(go.Bar(x=pareto['Product Name'],y=pareto[measure],name=measure,marker_color='#b45a2a',yaxis='y'))
    fig.add_trace(go.Scatter(x=pareto['Product Name'],y=pareto['Cumulative Share (%)'],name='Cumulative share (%)',line=dict(color='#47636f',width=3),mode='lines+markers',yaxis='y2'))
    fig.add_hline(y=0,line_color='#e3d4c5')
    fig.update_layout(title='Pareto distribution',yaxis=dict(title=measure+' (assumed USD)'),yaxis2=dict(title='Cumulative share (%)',overlaying='y',side='right',range=[0,105]),
                      xaxis=dict(title='Product (ranked)',tickangle=-40),legend=dict(orientation='h',y=1.16))
    st.plotly_chart(style(fig,550),use_container_width=True,config=PLOT_CONFIG)
    st.dataframe(pareto[['Product Rank','Product Name',measure,'Cumulative Share (%)']].style.format({measure:'{:,.2f}','Cumulative Share (%)':'{:.2f}'}),use_container_width=True,hide_index=True)
    st.caption('Pareto is computed across all selected products. Net totals and negative values can make cumulative shares nonmonotonic if valid losses are present; interpret carefully.')

with t6:
    st.subheader('Validation, provenance & downloadable results')
    q1,q2,q3,q4=st.columns(4)
    q1.metric('Original rows',f"{audit['source_rows']:,}")
    q2.metric('Retained after validation',f"{audit['retained_rows']:,}")
    q3.metric('Excluded invalid rows',f"{audit['excluded_rows']:,}")
    q4.metric('Missing / nonpositive units',f"{audit['missing_or_nonpositive_units_retained']:,}")
    st.dataframe(pd.DataFrame([{'Check':key.replace('_',' ').title(),'Count':value} for key,value in audit.items() if value is not None]),use_container_width=True,hide_index=True)
    st.markdown('''**Cleaning and definitions**
- Dates parsed as `DD-MM-YYYY` (day-first). Invalid dates and invalid/nonpositive sales or negative cost are excluded.
- `Gross Profit` is validated against `Sales - Cost` with a 0.011 tolerance. Negative *valid* gross profits are retained for loss detection.
- Rows with missing/nonpositive units are retained but excluded from unit denominators. Product/division labels are whitespace-normalized.
- Gross margin = `SUM(Gross Profit) / SUM(Sales) × 100`; profit/unit = `SUM(Gross Profit) / SUM(valid Units)`.
- Margin volatility = sample standard deviation, in percentage points, of **monthly product-level weighted gross margins** (requires at least two active months). A near-zero value can simply reflect fixed product-level pricing/cost in this illustrative dataset.
- Metrics change with filters; export the current filtered data and aggregations below.''')
    st.download_button('Download filtered transactions (CSV)',filtered.drop(columns=['Month','Year','Row Margin (%)'],errors='ignore').to_csv(index=False).encode('utf-8'),file_name='profitability_filtered_transactions.csv',mime='text/csv')
    st.download_button('Download product metrics (CSV)',products.to_csv(index=False).encode('utf-8'),file_name='profitability_product_metrics.csv',mime='text/csv')
    st.download_button('Download division metrics (CSV)',div.to_csv(index=False).encode('utf-8'),file_name='profitability_division_metrics.csv',mime='text/csv')
    with st.expander('Preview source rows'):
        st.dataframe(filtered.head(100),hide_index=True,use_container_width=True)
    st.markdown('**External reference:** [Nassau Candy official website](https://www.nassaucandy.com/) provides general business context only. The synthetic/illustrative Wonka-labelled transaction dataset was supplied with the project brief and has not been authenticated against the company.')

st.divider()
st.caption('Academic project · Product profitability analysis · No live ERP connection · Data range reflects the selected CSV, not company-reported financials.')
