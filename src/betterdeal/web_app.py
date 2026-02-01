"""
Web Application for Property Investment Analysis

FastAPI web app that accepts property URLs and performs investment analysis.
"""

import os
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .analysis_engine import PropertyAnalyzer, InvestmentStrategy
from .loan_calculator import LoanCalculator

load_dotenv()

app = FastAPI(
    title="RentCast Property Analyzer",
    description="Analyze property investments from Zillow and Realtor.com links",
    version="2.0.0"
)


class AnalysisRequest(BaseModel):
    """Request model for property analysis."""
    property_url: str = Field(..., description="Zillow or Realtor.com property URL")
    strategy: str = Field(
        default=InvestmentStrategy.RENTAL,
        description="Investment strategy: rental, flip, brrrr, house_hack, long_term_appreciation"
    )
    loan_type: str = Field(
        default=LoanCalculator.CONVENTIONAL,
        description="Loan type: conventional, fha, va, usda"
    )
    down_payment_pct: Optional[float] = Field(default=None)
    interest_rate: float = Field(default=0.065)
    loan_term_years: int = Field(default=30)
    purchase_price: Optional[float] = Field(default=None)
    estimated_rent: Optional[float] = Field(default=None)
    property_tax_annual: Optional[float] = Field(default=None)
    insurance_annual: Optional[float] = Field(default=None)
    hoa_monthly: float = Field(default=0.0)
    maintenance_pct: float = Field(default=0.01)
    vacancy_rate: float = Field(default=0.05)
    management_fee_pct: float = Field(default=0.10)
    # New advanced fields
    appreciation_rate: float = Field(default=0.04)
    rent_growth_rate: float = Field(default=0.03)
    expense_growth_rate: float = Field(default=0.02)
    marginal_tax_rate: float = Field(default=0.22)
    hold_years: int = Field(default=10)
    capex_reserve_pct: float = Field(default=0.03)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    return HTML_PAGE


@app.post("/api/analyze")
async def analyze_property(request: AnalysisRequest):
    """Analyze a property from a URL."""
    try:
        analyzer = PropertyAnalyzer()

        result = await analyzer.analyze_property(
            property_url=request.property_url,
            strategy_type=request.strategy,
            loan_type=request.loan_type,
            down_payment_pct=request.down_payment_pct,
            interest_rate=request.interest_rate,
            loan_term_years=request.loan_term_years,
            purchase_price=request.purchase_price,
            estimated_rent=request.estimated_rent,
            property_tax_annual=request.property_tax_annual,
            insurance_annual=request.insurance_annual,
            hoa_monthly=request.hoa_monthly,
            maintenance_pct=request.maintenance_pct,
            vacancy_rate=request.vacancy_rate,
            management_fee_pct=request.management_fee_pct,
            appreciation_rate=request.appreciation_rate,
            rent_growth_rate=request.rent_growth_rate,
            expense_growth_rate=request.expense_growth_rate,
            marginal_tax_rate=request.marginal_tax_rate,
            hold_years=request.hold_years,
            capex_reserve_pct=request.capex_reserve_pct,
        )

        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Main entry point for the web application."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Full HTML page with tabbed interface
# ---------------------------------------------------------------------------

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Property Investment Analyzer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,Ubuntu,Cantarell,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px}
.container{max-width:1200px;margin:0 auto;background:#fff;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,.3);overflow:hidden}
.header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:30px 40px;text-align:center}
.header h1{font-size:2.2em;margin-bottom:6px}
.header p{font-size:1em;opacity:.9}
.content{padding:30px 40px}

/* Form */
.form-group{margin-bottom:20px}
label{display:block;margin-bottom:6px;font-weight:600;color:#333;font-size:.9em}
input,select{width:100%;padding:10px 12px;border:2px solid #e0e0e0;border-radius:8px;font-size:15px;transition:border-color .3s}
input:focus,select:focus{outline:none;border-color:#667eea}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:600px){.form-row{grid-template-columns:1fr}}

/* Advanced settings collapsible */
.advanced-toggle{background:none;border:2px solid #667eea;color:#667eea;padding:10px 20px;font-size:14px;font-weight:600;border-radius:8px;cursor:pointer;width:100%;margin-bottom:16px;transition:all .2s}
.advanced-toggle:hover{background:#667eea;color:#fff}
.advanced-panel{display:none;border:1px solid #e0e0e0;border-radius:12px;padding:20px;margin-bottom:20px;background:#fafafa}
.advanced-panel.show{display:block}

/* Submit button */
.submit-btn{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;border:none;padding:14px 40px;font-size:17px;font-weight:600;border-radius:8px;cursor:pointer;width:100%;transition:transform .2s,box-shadow .2s}
.submit-btn:hover{transform:translateY(-2px);box-shadow:0 10px 20px rgba(102,126,234,.3)}
.submit-btn:disabled{opacity:.6;cursor:not-allowed;transform:none}

/* Loading */
.loading{text-align:center;padding:40px;display:none}
.loading.show{display:block}
.spinner{border:4px solid #f3f3f3;border-top:4px solid #667eea;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:0 auto 16px}
@keyframes spin{0%{transform:rotate(0)}100%{transform:rotate(360deg)}}

/* Results area */
.results{margin-top:30px;display:none}
.results.show{display:block}

/* Tabs */
.tab-bar{display:flex;flex-wrap:wrap;gap:4px;border-bottom:2px solid #e0e0e0;margin-bottom:20px}
.tab-btn{padding:10px 16px;border:none;background:none;font-size:14px;font-weight:600;color:#888;cursor:pointer;border-bottom:3px solid transparent;transition:all .2s;white-space:nowrap}
.tab-btn:hover{color:#667eea}
.tab-btn.active{color:#667eea;border-bottom-color:#667eea}
.tab-panel{display:none}
.tab-panel.active{display:block}

/* Cards */
.card{background:#f8f9fa;border-radius:12px;padding:20px;margin-bottom:20px}
.card h3{color:#667eea;margin-bottom:12px;font-size:1.1em}
.metric{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #e8e8e8}
.metric:last-child{border-bottom:none}
.metric-label{font-weight:500;color:#666;font-size:.9em}
.metric-value{font-weight:600;color:#333;font-size:.9em}
.positive{color:#10b981}
.negative{color:#ef4444}
.warning{color:#f59e0b}

/* Grade badge */
.grade-badge{display:inline-flex;align-items:center;justify-content:center;width:56px;height:56px;border-radius:50%;font-size:1.4em;font-weight:700;color:#fff;margin-right:12px;flex-shrink:0}
.grade-a{background:linear-gradient(135deg,#10b981,#059669)}
.grade-b{background:linear-gradient(135deg,#3b82f6,#2563eb)}
.grade-c{background:linear-gradient(135deg,#f59e0b,#d97706)}
.grade-d{background:linear-gradient(135deg,#ef4444,#dc2626)}
.grade-f{background:linear-gradient(135deg,#6b7280,#4b5563)}

/* Summary box */
.summary-box{display:flex;align-items:flex-start;background:linear-gradient(135deg,#f0f4ff,#e8ecff);border-radius:12px;padding:20px;margin-bottom:20px}
.summary-text{flex:1}
.summary-text ul{list-style:none;padding:0}
.summary-text li{padding:6px 0;font-size:.95em;color:#333}
.summary-text li::before{content:"\\2022";color:#667eea;font-weight:700;display:inline-block;width:1em;margin-left:0}

/* Projection table */
.proj-table{width:100%;border-collapse:collapse;font-size:.85em}
.proj-table th{background:#667eea;color:#fff;padding:8px 10px;text-align:right;position:sticky;top:0}
.proj-table th:first-child{text-align:center}
.proj-table td{padding:6px 10px;text-align:right;border-bottom:1px solid #eee}
.proj-table td:first-child{text-align:center;font-weight:600}
.proj-table tr:hover{background:#f0f4ff}
.proj-scroll{max-height:500px;overflow-y:auto;border-radius:8px;border:1px solid #e0e0e0}

/* Stress test */
.stress-pass{color:#10b981;font-weight:600}
.stress-fail{color:#ef4444;font-weight:600}
.stress-table{width:100%;border-collapse:collapse;font-size:.9em}
.stress-table th{background:#f1f5f9;padding:10px;text-align:left}
.stress-table td{padding:8px 10px;border-bottom:1px solid #eee}

/* Bar chart (CSS only) */
.bar-chart{margin:12px 0}
.bar-row{display:flex;align-items:center;margin-bottom:8px}
.bar-label{width:140px;font-size:.85em;font-weight:500;color:#555;flex-shrink:0}
.bar-track{flex:1;background:#e5e7eb;border-radius:6px;height:22px;overflow:hidden;position:relative}
.bar-fill{height:100%;border-radius:6px;transition:width .5s ease;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;font-size:.75em;font-weight:600;color:#fff;min-width:30px}
.bar-fill.high{background:linear-gradient(90deg,#10b981,#059669)}
.bar-fill.mid{background:linear-gradient(90deg,#3b82f6,#2563eb)}
.bar-fill.low{background:linear-gradient(90deg,#f59e0b,#d97706)}
.bar-fill.vlow{background:linear-gradient(90deg,#ef4444,#dc2626)}

/* Strategy cards */
.strategy-card{border:2px solid #e0e0e0;border-radius:12px;padding:16px;margin-bottom:16px;transition:border-color .2s}
.strategy-card.best{border-color:#10b981;background:#f0fdf4}
.strategy-header{display:flex;align-items:center;margin-bottom:10px}
.strategy-name{font-size:1.1em;font-weight:700;color:#333}
.strategy-score{margin-left:auto;font-size:.9em;color:#666}
.pros-cons{display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:.85em}
.pros li{color:#059669}
.cons li{color:#dc2626}
.pros,.cons{list-style:none;padding:0}
.pros li::before{content:"+ ";font-weight:700}
.cons li::before{content:"- ";font-weight:700}

/* Comp table */
.comp-table{width:100%;border-collapse:collapse;font-size:.88em}
.comp-table th{background:#f1f5f9;padding:8px 10px;text-align:left;font-size:.85em}
.comp-table td{padding:6px 10px;border-bottom:1px solid #eee}

/* Error */
.error{background:#fef2f2;border-left:4px solid #ef4444;padding:16px;border-radius:8px;color:#991b1b;margin-top:20px}

/* View toggle */
.view-toggle{margin-bottom:12px;display:flex;gap:8px}
.view-toggle button{padding:6px 14px;border:1px solid #667eea;background:#fff;color:#667eea;border-radius:6px;cursor:pointer;font-size:.85em;font-weight:500}
.view-toggle button.active{background:#667eea;color:#fff}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>Property Investment Analyzer</h1>
        <p>Institutional-grade analysis for Zillow and Realtor.com properties</p>
    </div>
    <div class="content">
        <form id="analysisForm">
            <div class="form-group">
                <label for="property_url">Property URL (Zillow or Realtor.com)</label>
                <input type="url" id="property_url" name="property_url" required
                       placeholder="https://www.zillow.com/homedetails/...">
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="strategy">Investment Strategy</label>
                    <select id="strategy" name="strategy">
                        <option value="rental">Rental (Buy &amp; Hold)</option>
                        <option value="flip">Flip</option>
                        <option value="brrrr">BRRRR</option>
                        <option value="house_hack">House Hack</option>
                        <option value="long_term_appreciation">Long-term Appreciation</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="loan_type">Loan Type</label>
                    <select id="loan_type" name="loan_type">
                        <option value="conventional">Conventional</option>
                        <option value="fha">FHA</option>
                        <option value="va">VA</option>
                        <option value="usda">USDA</option>
                    </select>
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="interest_rate">Interest Rate (%)</label>
                    <input type="number" id="interest_rate" name="interest_rate"
                           step="0.001" value="6.5" min="0" max="20">
                </div>
                <div class="form-group">
                    <label for="loan_term_years">Loan Term (Years)</label>
                    <input type="number" id="loan_term_years" name="loan_term_years"
                           value="30" min="15" max="30">
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="down_payment_pct">Down Payment (%)</label>
                    <input type="number" id="down_payment_pct" name="down_payment_pct"
                           step="0.1" min="0" max="100" placeholder="Auto (based on loan type)">
                </div>
                <div class="form-group">
                    <label for="purchase_price">Purchase Price ($)</label>
                    <input type="number" id="purchase_price" name="purchase_price"
                           step="1000" min="0" placeholder="Auto (from RentCast)">
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="estimated_rent">Estimated Monthly Rent ($)</label>
                    <input type="number" id="estimated_rent" name="estimated_rent"
                           step="100" min="0" placeholder="Auto (from RentCast)">
                </div>
                <div class="form-group">
                    <label for="hoa_monthly">Monthly HOA ($)</label>
                    <input type="number" id="hoa_monthly" name="hoa_monthly"
                           step="10" value="0" min="0">
                </div>
            </div>

            <button type="button" class="advanced-toggle" onclick="toggleAdvanced()">
                Advanced Settings
            </button>

            <div class="advanced-panel" id="advancedPanel">
                <div class="form-row">
                    <div class="form-group">
                        <label for="appreciation_rate">Annual Appreciation (%)</label>
                        <input type="number" id="appreciation_rate" name="appreciation_rate"
                               step="0.1" value="4.0" min="0" max="20">
                    </div>
                    <div class="form-group">
                        <label for="rent_growth_rate">Annual Rent Growth (%)</label>
                        <input type="number" id="rent_growth_rate" name="rent_growth_rate"
                               step="0.1" value="3.0" min="0" max="20">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="expense_growth_rate">Annual Expense Growth (%)</label>
                        <input type="number" id="expense_growth_rate" name="expense_growth_rate"
                               step="0.1" value="2.0" min="0" max="20">
                    </div>
                    <div class="form-group">
                        <label for="marginal_tax_rate">Marginal Tax Rate (%)</label>
                        <input type="number" id="marginal_tax_rate" name="marginal_tax_rate"
                               step="1" value="22" min="0" max="50">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="hold_years">Hold Period (Years)</label>
                        <input type="number" id="hold_years" name="hold_years"
                               value="10" min="1" max="30">
                    </div>
                    <div class="form-group">
                        <label for="capex_reserve_pct">CapEx Reserve (%)</label>
                        <input type="number" id="capex_reserve_pct" name="capex_reserve_pct"
                               step="0.1" value="3.0" min="0" max="10">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="vacancy_rate">Vacancy Rate (%)</label>
                        <input type="number" id="vacancy_rate" name="vacancy_rate"
                               step="0.5" value="5" min="0" max="50">
                    </div>
                    <div class="form-group">
                        <label for="management_fee_pct">Management Fee (%)</label>
                        <input type="number" id="management_fee_pct" name="management_fee_pct"
                               step="0.5" value="10" min="0" max="20">
                    </div>
                </div>
            </div>

            <button type="submit" class="submit-btn" id="analyzeBtn">Analyze Property</button>
        </form>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Analyzing property... This may take a moment.</p>
        </div>

        <div class="results" id="results"></div>
    </div>
</div>

<script>
function toggleAdvanced() {
    document.getElementById('advancedPanel').classList.toggle('show');
}

document.getElementById('analysisForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const resultsDiv = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    const analyzeBtn = document.getElementById('analyzeBtn');

    loadingDiv.classList.add('show');
    resultsDiv.classList.remove('show');
    analyzeBtn.disabled = true;

    const formData = new FormData(form);
    const data = {};

    const pctFields = ['interest_rate','down_payment_pct','appreciation_rate','rent_growth_rate',
                       'expense_growth_rate','marginal_tax_rate','capex_reserve_pct',
                       'vacancy_rate','management_fee_pct','maintenance_pct'];
    const intFields = ['loan_term_years','hold_years'];
    const floatNullFields = ['purchase_price','estimated_rent','property_tax_annual','insurance_annual'];

    for (const [key, value] of formData.entries()) {
        if (!value && value !== '0') continue;
        if (pctFields.includes(key)) {
            data[key] = parseFloat(value) / 100;
        } else if (intFields.includes(key)) {
            data[key] = parseInt(value);
        } else if (floatNullFields.includes(key)) {
            const v = parseFloat(value);
            if (!isNaN(v) && v > 0) data[key] = v;
        } else if (key === 'hoa_monthly') {
            data[key] = parseFloat(value) || 0;
        } else {
            data[key] = value;
        }
    }

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (response.ok && !result.error) {
            displayResults(result);
        } else {
            let msg = result.error || result.detail || 'An error occurred';
            if (Array.isArray(msg)) msg = msg.map(e => e.msg || JSON.stringify(e)).join(', ');
            else if (typeof msg === 'object') msg = JSON.stringify(msg);
            displayError(msg);
        }
    } catch (error) {
        displayError('Network error: ' + error.message);
    } finally {
        loadingDiv.classList.remove('show');
        analyzeBtn.disabled = false;
    }
});

function $(v) { return typeof v === 'number' ? v.toLocaleString(undefined, {minimumFractionDigits:0, maximumFractionDigits:2}) : (v ?? 'N/A'); }
function $$(v) { return typeof v === 'number' ? '$' + v.toLocaleString(undefined, {minimumFractionDigits:0, maximumFractionDigits:0}) : 'N/A'; }
function pct(v) { return typeof v === 'number' ? v.toFixed(2) + '%' : 'N/A'; }
function cfClass(v) { return v >= 0 ? 'positive' : 'negative'; }
function gradeClass(g) {
    if (!g) return 'grade-f';
    if (g.startsWith('A')) return 'grade-a';
    if (g.startsWith('B')) return 'grade-b';
    if (g.startsWith('C')) return 'grade-c';
    if (g.startsWith('D')) return 'grade-d';
    return 'grade-f';
}
function barClass(v) { return v >= 75 ? 'high' : v >= 50 ? 'mid' : v >= 25 ? 'low' : 'vlow'; }

function displayResults(d) {
    const resultsDiv = document.getElementById('results');
    const best = d.best_strategy;
    const cm = d.core_metrics;
    const proj = d.projection;
    const tax = d.tax_analysis;
    const risk = d.risk_analysis;
    const comps = d.comparables;
    const strats = d.strategy_scores || [];
    const summary = d.executive_summary || [];
    const ld = d.loan_details;

    let html = '';

    // --- Tab bar ---
    html += '<div class="tab-bar">';
    const tabs = ['Summary','Core Metrics','Projections','Tax Analysis','Risk Analysis','Comparables','Strategies'];
    tabs.forEach((t, i) => {
        html += '<button class="tab-btn' + (i===0?' active':'') + '" onclick="switchTab(event,' + i + ')">' + t + '</button>';
    });
    html += '</div>';

    // === TAB 0: Executive Summary ===
    html += '<div class="tab-panel active" data-tab="0">';
    if (best) {
        html += '<div class="summary-box">';
        html += '<div class="grade-badge ' + gradeClass(best.grade) + '">' + best.grade + '</div>';
        html += '<div class="summary-text">';
        html += '<div style="font-size:1.2em;font-weight:700;margin-bottom:4px">' + best.strategy.replace(/_/g,' ').replace(/\\b\\w/g,l=>l.toUpperCase()) + ' Strategy</div>';
        html += '<div style="color:#666;margin-bottom:10px">Score: ' + best.score + '/100</div>';
        html += '<ul>';
        summary.forEach(s => { html += '<li>' + s + '</li>'; });
        html += '</ul></div></div>';
    }
    // Key metrics overview
    html += '<div class="card"><h3>Key Metrics at a Glance</h3>';
    html += '<div class="form-row">';
    html += '<div>';
    html += metric('Monthly Cash Flow', $$(cm.cash_flow_before_tax/12), cfClass(cm.cash_flow_before_tax));
    html += metric('Annual NOI', $$(cm.noi));
    html += metric('Cash-on-Cash Return', pct(cm.cash_on_cash_return), cfClass(cm.cash_on_cash_return));
    html += '</div><div>';
    html += metric('Cap Rate', pct(cm.cap_rate));
    html += metric('DSCR', cm.dscr?.toFixed(2), cm.dscr >= 1.25 ? 'positive' : cm.dscr >= 1.0 ? 'warning' : 'negative');
    if (proj.irr != null) html += metric('Projected IRR', pct(proj.irr));
    html += '</div></div></div>';

    // Property & Loan info
    html += '<div class="card"><h3>Property & Loan</h3>';
    html += metric('Address', d.property_info?.address || 'N/A');
    html += metric('Purchase Price', $$(ld?.purchase_price));
    html += metric('Loan Amount', $$(ld?.loan_amount));
    html += metric('Down Payment', $$(ld?.down_payment) + ' (' + (ld?.down_payment_pct||0) + '%)');
    html += metric('Monthly Payment (PITI)', $$(ld?.total_monthly_payment));
    html += metric('Estimated Monthly Rent', $$(cm.gross_rental_income/12));
    html += '</div>';
    html += '</div>';

    // === TAB 1: Core Metrics ===
    html += '<div class="tab-panel" data-tab="1">';
    html += '<div class="card"><h3>Income</h3>';
    html += metric('Gross Rental Income', $$(cm.gross_rental_income) + '/yr');
    html += metric('Vacancy Loss (' + (d.selected_strategy ? '' : '') + ')', '-' + $$(cm.vacancy_loss));
    html += metric('Effective Gross Income', $$(cm.effective_gross_income));
    html += '</div>';
    html += '<div class="card"><h3>Expenses (Operating - excludes debt service)</h3>';
    html += metric('Total Operating Expenses', $$(cm.operating_expenses));
    html += metric('OpEx Ratio', pct(cm.opex_ratio));
    html += metric('CapEx Reserve', $$(cm.capex_reserve_annual) + '/yr');
    html += '</div>';
    html += '<div class="card"><h3>Returns</h3>';
    html += metric('Net Operating Income (NOI)', $$(cm.noi));
    html += metric('Annual Debt Service', $$(cm.annual_debt_service));
    html += metric('Cash Flow (Before Tax)', $$(cm.cash_flow_before_tax), cfClass(cm.cash_flow_before_tax));
    html += metric('Cash-on-Cash Return', pct(cm.cash_on_cash_return));
    html += metric('Cap Rate', pct(cm.cap_rate));
    html += metric('Gross Rental Yield', pct(cm.gross_rental_yield));
    html += metric('Rent-to-Value', pct(cm.rent_to_value));
    html += metric('DSCR', cm.dscr?.toFixed(2));
    html += metric('Break-Even Occupancy', pct(cm.break_even_occupancy));
    html += metric('Total Cash Invested', $$(cm.total_cash_invested));
    html += '</div>';
    html += '</div>';

    // === TAB 2: Projections ===
    html += '<div class="tab-panel" data-tab="2">';
    if (proj.irr != null || proj.npv != null) {
        html += '<div class="card"><h3>Terminal Metrics</h3>';
        html += metric('IRR', proj.irr != null ? pct(proj.irr) : 'N/A');
        html += metric('NPV (8% discount)', proj.npv != null ? $$(proj.npv) : 'N/A');
        html += metric('Equity Multiple', proj.equity_multiple != null ? proj.equity_multiple.toFixed(2) + 'x' : 'N/A');
        html += metric('Terminal Sale Price', $$(proj.terminal_sale_price));
        html += metric('Selling Costs (6%)', $$(proj.selling_costs));
        html += metric('Depreciation Recapture Tax', $$(proj.depreciation_recapture_tax));
        html += metric('Net Sale Proceeds', $$(proj.net_sale_proceeds));
        html += '</div>';
    }
    html += '<div class="view-toggle"><button class="active" onclick="toggleProjView(event,false)">10-Year</button><button onclick="toggleProjView(event,true)">Full 30-Year</button></div>';
    html += buildProjectionTable(proj.years, false);
    html += '</div>';

    // === TAB 3: Tax Analysis ===
    html += '<div class="tab-panel" data-tab="3">';
    html += '<div class="card"><h3>Year 1 Tax Analysis</h3>';
    html += metric('Depreciable Basis', $$(tax.depreciable_basis));
    html += metric('Depreciation Schedule', tax.depreciation_years + ' years');
    html += metric('Annual Depreciation', $$(tax.annual_depreciation));
    html += metric('Mortgage Interest (Yr 1)', $$(tax.mortgage_interest_year1));
    html += metric('NOI', $$(tax.noi));
    html += metric('Taxable Income', $$(tax.taxable_income), cfClass(-tax.taxable_income));
    if (tax.paper_loss < 0) {
        html += metric('Paper Loss', $$(Math.abs(tax.paper_loss)), 'positive');
        html += metric('Tax Savings', $$(tax.tax_savings), 'positive');
    }
    html += metric('Marginal Tax Rate', pct(tax.marginal_tax_rate * 100));
    html += metric('After-Tax Cash Flow', $$(tax.effective_cash_flow_after_tax), cfClass(tax.effective_cash_flow_after_tax));
    html += '</div>';
    html += '</div>';

    // === TAB 4: Risk Analysis ===
    html += '<div class="tab-panel" data-tab="4">';
    html += '<div class="card"><h3>Stress Test Scenarios</h3>';
    html += '<table class="stress-table"><thead><tr><th>Scenario</th><th>Cash Flow/mo</th><th>DSCR</th><th>CoC Return</th><th>Result</th></tr></thead><tbody>';
    (risk.scenarios || []).forEach(s => {
        const cls = s.passes ? 'stress-pass' : 'stress-fail';
        html += '<tr><td><strong>' + s.name + '</strong><br><small style="color:#888">' + s.description + '</small></td>';
        html += '<td class="' + cfClass(s.cash_flow_monthly) + '">' + $$(s.cash_flow_monthly) + '</td>';
        html += '<td>' + s.dscr?.toFixed(2) + '</td>';
        html += '<td>' + pct(s.cash_on_cash) + '</td>';
        html += '<td class="' + cls + '">' + (s.passes ? 'PASS' : 'FAIL') + '</td></tr>';
    });
    html += '</tbody></table></div>';

    if (risk.break_even) {
        html += '<div class="card"><h3>Break-Even Metrics</h3>';
        html += metric('Min Monthly Rent', $$(risk.break_even.min_monthly_rent));
        html += metric('Max Purchase Price (8% CoC)', $$(risk.break_even.max_purchase_price));
        html += metric('Max Interest Rate', pct(risk.break_even.max_interest_rate));
        html += metric('Max Vacancy Rate', pct(risk.break_even.max_vacancy_rate));
        html += '</div>';
    }
    html += '</div>';

    // === TAB 5: Comparables ===
    html += '<div class="tab-panel" data-tab="5">';
    const sc = comps.sale_comps || [];
    const rc = comps.rental_comps || [];
    if (sc.length === 0 && rc.length === 0) {
        html += '<div class="card"><p style="color:#888;text-align:center;padding:20px">No comparable properties found in this area. This may be due to limited listings data.</p></div>';
    } else {
        if (comps.subject_price_sqft || comps.subject_rent_sqft) {
            html += '<div class="card"><h3>Subject vs Market</h3>';
            if (comps.subject_price_sqft) html += metric('Subject Price/sqft', '$' + comps.subject_price_sqft.toFixed(2));
            if (comps.median_sale_price_sqft) html += metric('Market Median Price/sqft', '$' + comps.median_sale_price_sqft.toFixed(2));
            if (comps.price_vs_market) html += metric('Price vs Market', comps.price_vs_market.toUpperCase());
            if (comps.subject_rent_sqft) html += metric('Subject Rent/sqft', '$' + comps.subject_rent_sqft.toFixed(2));
            if (comps.median_rent_sqft) html += metric('Market Median Rent/sqft', '$' + comps.median_rent_sqft.toFixed(2));
            if (comps.rent_vs_market) html += metric('Rent vs Market', comps.rent_vs_market.toUpperCase());
            html += '</div>';
        }
        if (sc.length > 0) {
            html += '<div class="card"><h3>Sale Comparables (' + sc.length + ')</h3>';
            html += '<table class="comp-table"><thead><tr><th>Address</th><th>Price</th><th>Sqft</th><th>$/Sqft</th><th>Bed/Bath</th></tr></thead><tbody>';
            sc.forEach(c => {
                html += '<tr><td>' + c.address + '</td><td>' + $$(c.price) + '</td><td>' + $(c.sqft) + '</td><td>$' + c.price_per_sqft.toFixed(2) + '</td><td>' + (c.bedrooms||'-') + '/' + (c.bathrooms||'-') + '</td></tr>';
            });
            html += '</tbody></table></div>';
        }
        if (rc.length > 0) {
            html += '<div class="card"><h3>Rental Comparables (' + rc.length + ')</h3>';
            html += '<table class="comp-table"><thead><tr><th>Address</th><th>Rent</th><th>Sqft</th><th>$/Sqft</th><th>Bed/Bath</th></tr></thead><tbody>';
            rc.forEach(c => {
                html += '<tr><td>' + c.address + '</td><td>' + $$(c.price) + '/mo</td><td>' + $(c.sqft) + '</td><td>$' + c.price_per_sqft.toFixed(2) + '</td><td>' + (c.bedrooms||'-') + '/' + (c.bathrooms||'-') + '</td></tr>';
            });
            html += '</tbody></table></div>';
        }
    }
    html += '</div>';

    // === TAB 6: Strategy Scores ===
    html += '<div class="tab-panel" data-tab="6">';
    strats.sort((a,b) => b.score - a.score);
    strats.forEach(s => {
        const isBest = best && s.strategy === best.strategy;
        const name = s.strategy.replace(/_/g,' ').replace(/\\b\\w/g,l=>l.toUpperCase());
        html += '<div class="strategy-card' + (isBest?' best':'') + '">';
        html += '<div class="strategy-header">';
        html += '<div class="grade-badge ' + gradeClass(s.grade) + '" style="width:40px;height:40px;font-size:1em">' + s.grade + '</div>';
        html += '<div class="strategy-name">' + name + (isBest ? ' <span style="color:#059669;font-size:.8em">(Recommended)</span>':'') + '</div>';
        html += '<div class="strategy-score">' + s.score.toFixed(1) + '/100</div>';
        html += '</div>';

        // Component bar chart
        if (s.component_scores) {
            html += '<div class="bar-chart">';
            for (const [label, val] of Object.entries(s.component_scores)) {
                html += '<div class="bar-row">';
                html += '<div class="bar-label">' + label + '</div>';
                html += '<div class="bar-track"><div class="bar-fill ' + barClass(val) + '" style="width:' + Math.min(val,100) + '%">' + val.toFixed(0) + '</div></div>';
                html += '</div>';
            }
            html += '</div>';
        }

        // Pros / Cons
        if ((s.pros && s.pros.length) || (s.cons && s.cons.length)) {
            html += '<div class="pros-cons">';
            html += '<ul class="pros">';
            (s.pros||[]).forEach(p => { html += '<li>' + p + '</li>'; });
            html += '</ul><ul class="cons">';
            (s.cons||[]).forEach(c => { html += '<li>' + c + '</li>'; });
            html += '</ul></div>';
        }
        html += '</div>';
    });
    html += '</div>';

    resultsDiv.innerHTML = html;
    resultsDiv.classList.add('show');
}

function metric(label, value, cls) {
    return '<div class="metric"><span class="metric-label">' + label + '</span><span class="metric-value' + (cls ? ' '+cls : '') + '">' + value + '</span></div>';
}

function switchTab(e, idx) {
    document.querySelectorAll('.tab-btn').forEach((b,i) => b.classList.toggle('active', i===idx));
    document.querySelectorAll('.tab-panel').forEach((p,i) => p.classList.toggle('active', i===idx));
}

function buildProjectionTable(years, full) {
    if (!years || !years.length) return '<p>No projection data.</p>';
    let indices;
    if (full) {
        // Years 1-10, then 15,20,25,30
        indices = [];
        for (let i = 0; i < 10 && i < years.length; i++) indices.push(i);
        [14,19,24,29].forEach(i => { if (i < years.length && !indices.includes(i)) indices.push(i); });
    } else {
        indices = [];
        for (let i = 0; i < 10 && i < years.length; i++) indices.push(i);
    }
    let html = '<div class="proj-scroll" id="projTable"><table class="proj-table"><thead><tr>';
    html += '<th>Year</th><th>Gross Income</th><th>NOI</th><th>CF (Pre-Tax)</th><th>CF (Post-Tax)</th><th>Property Value</th><th>Equity</th><th>ROE</th>';
    html += '</tr></thead><tbody>';
    indices.forEach(i => {
        const y = years[i];
        html += '<tr><td>' + y.year + '</td><td>' + $$(y.gross_income) + '</td><td>' + $$(y.noi) + '</td>';
        html += '<td class="' + cfClass(y.cash_flow_before_tax) + '">' + $$(y.cash_flow_before_tax) + '</td>';
        html += '<td class="' + cfClass(y.cash_flow_after_tax) + '">' + $$(y.cash_flow_after_tax) + '</td>';
        html += '<td>' + $$(y.property_value) + '</td><td>' + $$(y.equity) + '</td>';
        html += '<td>' + pct(y.return_on_equity) + '</td></tr>';
    });
    html += '</tbody></table></div>';
    return html;
}

function toggleProjView(e, full) {
    const btns = e.target.parentElement.querySelectorAll('button');
    btns.forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
    // Rebuild table
    const panel = e.target.closest('.tab-panel');
    const tableDiv = panel.querySelector('#projTable');
    if (tableDiv && window._projYears) {
        tableDiv.outerHTML = buildProjectionTable(window._projYears, full).replace('<div class="proj-scroll" id="projTable">','<div class="proj-scroll" id="projTable">');
    }
}

// Store projection years globally for toggle
const origDisplay = displayResults;
displayResults = function(d) {
    window._projYears = d.projection?.years;
    origDisplay(d);
};

function displayError(message) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div class="error"><strong>Error:</strong> ' + message + '</div>';
    resultsDiv.classList.add('show');
}
</script>
</body>
</html>"""
