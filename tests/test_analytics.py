from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from analytics import (clean_data, summary, product_metrics, division_metrics,
                       profit_pareto, products_to_80_pct, risk_flags, monthly_metrics)
DATA = Path(__file__).resolve().parents[1] / 'data' / 'Nassau_Candy_Distributor.csv'

def test_dataset_audit_and_accounting():
    d, a = clean_data(DATA)
    assert a['source_rows'] == 10194
    assert a['excluded_rows'] == 0
    assert a['unique_order_ids'] == 8549
    assert np.allclose(d['Sales']-d['Cost'],d['Gross Profit'], atol=0.011)

def test_summary_reconciles_with_row_sums():
    d, _ = clean_data(DATA); s = summary(d)
    assert round(s['revenue'],2) == 141783.63
    assert round(s['profit'],2) == 93442.80
    assert s['products']==15
    assert s['divisions']==3

def test_product_division_reconciliation():
    d,_=clean_data(DATA); p=product_metrics(d); g=division_metrics(d); s=summary(d)
    assert len(p)==15 and len(g)==3
    for k in ['Revenue','Profit','Cost']:
        assert np.isclose(p[k].sum(),s[k.lower()])
        assert np.isclose(g[k].sum(),s[k.lower()])

def test_weighted_margin_not_simple_mean():
    d,_=clean_data(DATA); p=product_metrics(d)
    assert np.isclose(summary(d)['gross_margin_pct'], 100*p.Profit.sum()/p.Revenue.sum())

def test_pareto_and_concentration():
    d,_=clean_data(DATA); p=product_metrics(d)
    assert products_to_80_pct(p, 'Profit')==5
    assert products_to_80_pct(p, 'Revenue')==5
    assert np.isclose(profit_pareto(p)['Cumulative Share (%)'].iloc[-1], 100)

def test_months_and_volatile_margin():
    d,_=clean_data(DATA); m=monthly_metrics(d); p=product_metrics(d)
    assert len(m)==24
    assert m.Month.min().year==2024 and m.Month.max().year==2025
    assert p['Margin Volatility (pp)'].notna().all()

def test_risk_flags():
    d,_=clean_data(DATA); p=risk_flags(product_metrics(d), margin_threshold=50)
    row=p.loc[p['Product Name']=='Kazookles'].iloc[0]
    assert bool(row['Low Margin'])
    assert row['Risk Classification']=='Priority margin review'

def test_invalid_data_exclusion_and_bad_units():
    d,_=clean_data(DATA); tmp=d.head(2).drop(columns=['Month','Year','Row Margin (%)']).copy()
    tmp.loc[tmp.index[0], 'Sales']=-1
    tmp.loc[tmp.index[1], 'Units']=0
    clean,a=clean_data(tmp)
    assert a['excluded_rows']==1
    assert a['missing_or_nonpositive_units_retained']==1
