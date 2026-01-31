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
    version="1.0.0"
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
    down_payment_pct: Optional[float] = Field(
        default=None,
        description="Down payment percentage (0-1). If None, uses default for loan type."
    )
    interest_rate: float = Field(
        default=0.065,
        description="Annual interest rate (e.g., 0.065 for 6.5%)"
    )
    loan_term_years: int = Field(
        default=30,
        description="Loan term in years"
    )
    purchase_price: Optional[float] = Field(
        default=None,
        description="Purchase price (if not provided, will be estimated from RentCast)"
    )
    estimated_rent: Optional[float] = Field(
        default=None,
        description="Estimated monthly rent (if not provided, will be estimated from RentCast)"
    )
    property_tax_annual: Optional[float] = Field(
        default=None,
        description="Annual property tax (if not provided, will be estimated)"
    )
    insurance_annual: Optional[float] = Field(
        default=None,
        description="Annual insurance (if not provided, will be estimated)"
    )
    hoa_monthly: float = Field(
        default=0.0,
        description="Monthly HOA fees"
    )
    maintenance_pct: float = Field(
        default=0.01,
        description="Annual maintenance as percentage of property value (e.g., 0.01 for 1%)"
    )
    vacancy_rate: float = Field(
        default=0.05,
        description="Vacancy rate (e.g., 0.05 for 5%)"
    )
    management_fee_pct: float = Field(
        default=0.10,
        description="Property management fee as percentage of rent (e.g., 0.10 for 10%)"
    )


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Property Investment Analyzer</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .header p {
                font-size: 1.1em;
                opacity: 0.9;
            }
            .content {
                padding: 40px;
            }
            .form-group {
                margin-bottom: 25px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #333;
            }
            input, select {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input:focus, select:focus {
                outline: none;
                border-color: #667eea;
            }
            .form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 40px;
                font-size: 18px;
                font-weight: 600;
                border-radius: 8px;
                cursor: pointer;
                width: 100%;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            button:active {
                transform: translateY(0);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            .results {
                margin-top: 40px;
                display: none;
            }
            .results.show {
                display: block;
            }
            .card {
                background: #f8f9fa;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .card h3 {
                color: #667eea;
                margin-bottom: 15px;
            }
            .metric {
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #e0e0e0;
            }
            .metric:last-child {
                border-bottom: none;
            }
            .metric-label {
                font-weight: 500;
                color: #666;
            }
            .metric-value {
                font-weight: 600;
                color: #333;
            }
            .positive {
                color: #10b981;
            }
            .negative {
                color: #ef4444;
            }
            .loading {
                text-align: center;
                padding: 40px;
                display: none;
            }
            .loading.show {
                display: block;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .recommendations {
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
            }
            .recommendations ul {
                list-style: none;
                padding-left: 0;
            }
            .recommendations li {
                padding: 8px 0;
            }
            .error {
                background: #f8d7da;
                border-left: 4px solid #dc3545;
                padding: 15px;
                border-radius: 8px;
                color: #721c24;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏠 Property Investment Analyzer</h1>
                <p>Analyze Zillow and Realtor.com properties for investment potential</p>
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
                                <option value="rental">Rental (Buy & Hold)</option>
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
                    
                    <button type="submit" id="analyzeBtn">Analyze Property</button>
                </form>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Analyzing property... This may take a moment.</p>
                </div>
                
                <div class="results" id="results"></div>
            </div>
        </div>
        
        <script>
            document.getElementById('analysisForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const form = e.target;
                const resultsDiv = document.getElementById('results');
                const loadingDiv = document.getElementById('loading');
                const analyzeBtn = document.getElementById('analyzeBtn');
                
                // Show loading, hide results
                loadingDiv.classList.add('show');
                resultsDiv.classList.remove('show');
                analyzeBtn.disabled = true;
                
                // Collect form data
                const formData = new FormData(form);
                const data = {};
                
                for (const [key, value] of formData.entries()) {
                    if (value) {
                        if (key === 'interest_rate') {
                            data[key] = parseFloat(value) / 100;
                        } else if (['down_payment_pct', 'maintenance_pct', 'vacancy_rate', 'management_fee_pct'].includes(key)) {
                            data[key] = parseFloat(value) / 100;
                        } else if (['loan_term_years'].includes(key)) {
                            data[key] = parseInt(value);
                        } else if (['purchase_price', 'estimated_rent', 'hoa_monthly'].includes(key)) {
                            data[key] = parseFloat(value) || null;
                        } else {
                            data[key] = value;
                        }
                    }
                }
                
                try {
                    const response = await fetch('/api/analyze', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        displayResults(result);
                    } else {
                        displayError(result.detail || 'An error occurred');
                    }
                } catch (error) {
                    displayError('Network error: ' + error.message);
                } finally {
                    loadingDiv.classList.remove('show');
                    analyzeBtn.disabled = false;
                }
            });
            
            function displayResults(data) {
                const resultsDiv = document.getElementById('results');
                let html = '';
                
                if (data.error) {
                    html = `<div class="error"><strong>Error:</strong> ${data.error}</div>`;
                    if (data.suggestions) {
                        html += '<ul>';
                        data.suggestions.forEach(s => html += `<li>${s}</li>`);
                        html += '</ul>';
                    }
                } else {
                    // Property Info
                    html += '<div class="card"><h3>Property Information</h3>';
                    html += `<div class="metric"><span class="metric-label">Address:</span><span class="metric-value">${data.property_info?.address || 'N/A'}</span></div>`;
                    html += `<div class="metric"><span class="metric-label">Source:</span><span class="metric-value">${data.property_info?.source || 'N/A'}</span></div>`;
                    html += '</div>';
                    
                    // Loan Details
                    if (data.loan_details) {
                        html += '<div class="card"><h3>Loan Details</h3>';
                        const ld = data.loan_details;
                        html += `<div class="metric"><span class="metric-label">Purchase Price:</span><span class="metric-value">$${ld.purchase_price?.toLocaleString() || 'N/A'}</span></div>`;
                        html += `<div class="metric"><span class="metric-label">Down Payment:</span><span class="metric-value">$${ld.down_payment?.toLocaleString() || 'N/A'} (${ld.down_payment_pct}%)</span></div>`;
                        html += `<div class="metric"><span class="metric-label">Loan Amount:</span><span class="metric-value">$${ld.loan_amount?.toLocaleString() || 'N/A'}</span></div>`;
                        html += `<div class="metric"><span class="metric-label">Interest Rate:</span><span class="metric-value">${ld.interest_rate}%</span></div>`;
                        html += `<div class="metric"><span class="metric-label">Monthly Payment (PITI):</span><span class="metric-value">$${ld.total_monthly_payment?.toLocaleString() || 'N/A'}</span></div>`;
                        html += '</div>';
                    }
                    
                    // Investment Analysis
                    if (data.investment_analysis) {
                        html += '<div class="card"><h3>Investment Analysis</h3>';
                        const ia = data.investment_analysis;
                        html += `<div class="metric"><span class="metric-label">Monthly Cash Flow:</span><span class="metric-value ${ia.monthly_cash_flow >= 0 ? 'positive' : 'negative'}">$${ia.monthly_cash_flow?.toLocaleString() || 'N/A'}</span></div>`;
                        html += `<div class="metric"><span class="metric-label">Annual Cash Flow:</span><span class="metric-value ${ia.annual_cash_flow >= 0 ? 'positive' : 'negative'}">$${ia.annual_cash_flow?.toLocaleString() || 'N/A'}</span></div>`;
                        html += `<div class="metric"><span class="metric-label">Cash-on-Cash Return:</span><span class="metric-value">${ia.cash_on_cash_return}%</span></div>`;
                        html += `<div class="metric"><span class="metric-label">Cap Rate:</span><span class="metric-value">${ia.cap_rate}%</span></div>`;
                        html += `<div class="metric"><span class="metric-label">Rental Yield:</span><span class="metric-value">${ia.rental_yield}%</span></div>`;
                        html += `<div class="metric"><span class="metric-label">DSCR:</span><span class="metric-value">${ia.dscr}</span></div>`;
                        html += '</div>';
                    }
                    
                    // Scores
                    if (data.scores) {
                        html += '<div class="card"><h3>Investment Scores</h3>';
                        const scores = data.scores;
                        html += `<div class="metric"><span class="metric-label">Overall Score:</span><span class="metric-value">${scores.overall_score || 'N/A'}/100</span></div>`;
                        if (scores.cash_on_cash_score) {
                            html += `<div class="metric"><span class="metric-label">Cash-on-Cash Score:</span><span class="metric-value">${scores.cash_on_cash_score}/100</span></div>`;
                        }
                        html += '</div>';
                    }
                    
                    // Recommendations
                    if (data.recommendations && data.recommendations.length > 0) {
                        html += '<div class="recommendations"><h3>Recommendations</h3><ul>';
                        data.recommendations.forEach(rec => {
                            html += `<li>${rec}</li>`;
                        });
                        html += '</ul></div>';
                    }
                }
                
                resultsDiv.innerHTML = html;
                resultsDiv.classList.add('show');
            }
            
            function displayError(message) {
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = `<div class="error"><strong>Error:</strong> ${message}</div>`;
                resultsDiv.classList.add('show');
            }
        </script>
    </body>
    </html>
    """


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
