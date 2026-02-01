"""
Property Investment Analysis Engine

Institutional-grade property investment analysis with multi-year projections,
IRR/NPV, tax analysis, risk stress testing, comparable market analysis,
and scoring for all 5 strategies.
"""

import math
import re
import statistics
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from .loan_calculator import LoanCalculator
from .rentcast_client import RentCastClient


# ---------------------------------------------------------------------------
# Pydantic Data Models
# ---------------------------------------------------------------------------

class CoreMetrics(BaseModel):
    """Corrected core investment metrics."""
    gross_rental_income: float = 0.0
    vacancy_loss: float = 0.0
    effective_gross_income: float = 0.0
    operating_expenses: float = 0.0  # Does NOT include debt service
    noi: float = 0.0  # EGI - opex
    annual_debt_service: float = 0.0
    cash_flow_before_tax: float = 0.0
    total_cash_invested: float = 0.0
    cash_on_cash_return: float = 0.0
    cap_rate: float = 0.0
    gross_rental_yield: float = 0.0
    rent_to_value: float = 0.0
    dscr: float = 0.0  # NOI / debt service
    opex_ratio: float = 0.0  # opex / EGI
    break_even_occupancy: float = 0.0
    capex_reserve_annual: float = 0.0


class YearProjection(BaseModel):
    """Single-year projection."""
    year: int
    gross_income: float = 0.0
    vacancy_loss: float = 0.0
    effective_income: float = 0.0
    operating_expenses: float = 0.0
    noi: float = 0.0
    debt_service: float = 0.0
    cash_flow_before_tax: float = 0.0
    depreciation: float = 0.0
    mortgage_interest: float = 0.0
    taxable_income: float = 0.0
    tax_liability: float = 0.0
    cash_flow_after_tax: float = 0.0
    property_value: float = 0.0
    loan_balance: float = 0.0
    equity: float = 0.0
    return_on_equity: float = 0.0


class MultiYearProjection(BaseModel):
    """Multi-year projection with terminal metrics."""
    years: List[YearProjection] = []
    irr: Optional[float] = None
    npv: Optional[float] = None
    equity_multiple: Optional[float] = None
    annualized_return: Optional[float] = None
    terminal_sale_price: float = 0.0
    selling_costs: float = 0.0
    depreciation_recapture_tax: float = 0.0
    net_sale_proceeds: float = 0.0


class TaxAnalysis(BaseModel):
    """Year-1 detailed tax breakdown."""
    annual_depreciation: float = 0.0
    depreciable_basis: float = 0.0
    depreciation_years: float = 27.5
    mortgage_interest_year1: float = 0.0
    noi: float = 0.0
    taxable_income: float = 0.0
    paper_loss: float = 0.0
    tax_savings: float = 0.0
    effective_cash_flow_after_tax: float = 0.0
    marginal_tax_rate: float = 0.22


class StressScenario(BaseModel):
    """Single stress test result."""
    name: str
    description: str
    cash_flow_monthly: float = 0.0
    cash_flow_annual: float = 0.0
    dscr: float = 0.0
    cash_on_cash: float = 0.0
    passes: bool = True


class BreakEvenMetrics(BaseModel):
    """Break-even calculations."""
    min_monthly_rent: float = 0.0
    max_purchase_price: float = 0.0
    max_interest_rate: float = 0.0
    max_vacancy_rate: float = 0.0


class RiskAnalysis(BaseModel):
    """Risk stress tests and break-even metrics."""
    scenarios: List[StressScenario] = []
    break_even: BreakEvenMetrics = BreakEvenMetrics()
    overall_risk_score: float = 0.0  # 0-100, higher = riskier


class CompProperty(BaseModel):
    """A single comparable property."""
    address: str = ""
    price: float = 0.0
    sqft: float = 0.0
    price_per_sqft: float = 0.0
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None


class ComparableAnalysis(BaseModel):
    """Sale and rental comp analysis."""
    sale_comps: List[CompProperty] = []
    rental_comps: List[CompProperty] = []
    median_sale_price_sqft: Optional[float] = None
    median_rent_sqft: Optional[float] = None
    subject_price_sqft: Optional[float] = None
    subject_rent_sqft: Optional[float] = None
    price_vs_market: Optional[str] = None  # "above", "below", "at"
    rent_vs_market: Optional[str] = None


class StrategyScore(BaseModel):
    """Score for a single strategy."""
    strategy: str
    score: float = 0.0  # 0-100
    grade: str = "N/A"
    pros: List[str] = []
    cons: List[str] = []
    component_scores: Dict[str, float] = {}


class FullAnalysisResult(BaseModel):
    """Complete analysis result."""
    property_info: Dict[str, Any] = {}
    property_data: Dict[str, Any] = {}
    market_statistics: Optional[Dict[str, Any]] = None
    loan_details: Dict[str, Any] = {}
    core_metrics: CoreMetrics = CoreMetrics()
    projection: MultiYearProjection = MultiYearProjection()
    tax_analysis: TaxAnalysis = TaxAnalysis()
    risk_analysis: RiskAnalysis = RiskAnalysis()
    comparables: ComparableAnalysis = ComparableAnalysis()
    strategy_scores: List[StrategyScore] = []
    best_strategy: Optional[StrategyScore] = None
    executive_summary: List[str] = []
    selected_strategy: str = "rental"


# ---------------------------------------------------------------------------
# Investment Strategy Config (kept for compatibility)
# ---------------------------------------------------------------------------

class InvestmentStrategy:
    RENTAL = "rental"
    FLIP = "flip"
    BRRRR = "brrrr"
    HOUSE_HACK = "house_hack"
    LONG_TERM_APPRECIATION = "long_term_appreciation"

    ALL_STRATEGIES = [RENTAL, FLIP, BRRRR, HOUSE_HACK, LONG_TERM_APPRECIATION]


# ---------------------------------------------------------------------------
# Calculation Engine
# ---------------------------------------------------------------------------

class InvestmentCalculator:
    """Institutional-grade investment calculations."""

    def __init__(
        self,
        purchase_price: float,
        estimated_rent: float,
        loan_details: Dict[str, Any],
        amortization: List[Dict[str, float]],
        vacancy_rate: float = 0.05,
        maintenance_pct: float = 0.01,
        management_fee_pct: float = 0.10,
        capex_reserve_pct: float = 0.03,
        appreciation_rate: float = 0.04,
        rent_growth_rate: float = 0.03,
        expense_growth_rate: float = 0.02,
        marginal_tax_rate: float = 0.22,
        hold_years: int = 10,
    ):
        self.purchase_price = purchase_price
        self.estimated_rent = estimated_rent
        self.loan_details = loan_details
        self.amortization = amortization
        self.vacancy_rate = vacancy_rate
        self.maintenance_pct = maintenance_pct
        self.management_fee_pct = management_fee_pct
        self.capex_reserve_pct = capex_reserve_pct
        self.appreciation_rate = appreciation_rate
        self.rent_growth_rate = rent_growth_rate
        self.expense_growth_rate = expense_growth_rate
        self.marginal_tax_rate = marginal_tax_rate
        self.hold_years = hold_years

        # Derived
        self.loan_amount = loan_details.get("loan_amount", 0)
        self.annual_debt_service = loan_details.get("monthly_principal_interest", 0) * 12
        self.down_payment = loan_details.get("down_payment", 0)
        self.upfront_costs = loan_details.get("upfront_costs", 0)
        self.total_cash_invested = self.down_payment + self.upfront_costs
        self.interest_rate = loan_details.get("interest_rate_decimal", 0.065)
        self.loan_term = loan_details.get("loan_term_years", 30)

        # Operating expense components (annual, year 1)
        self.property_tax_annual = loan_details.get("property_tax_annual", purchase_price * 0.015)
        self.insurance_annual = loan_details.get("insurance_annual", purchase_price * 0.005)
        self.pmi_annual = loan_details.get("pmi_monthly", 0) * 12
        self.hoa_annual = loan_details.get("hoa_monthly", 0) * 12
        self.maintenance_annual = purchase_price * maintenance_pct
        self.capex_reserve_annual = purchase_price * capex_reserve_pct

        # Depreciable basis: improvements only (land ~20%)
        self.land_value = purchase_price * 0.20
        self.depreciable_basis = purchase_price - self.land_value
        self.annual_depreciation = self.depreciable_basis / 27.5

    # ----- Core Metrics -----

    def calculate_core_metrics(self) -> CoreMetrics:
        gross_income = self.estimated_rent * 12
        vacancy_loss = gross_income * self.vacancy_rate
        egi = gross_income - vacancy_loss

        management_fee = gross_income * self.management_fee_pct
        opex = (
            self.property_tax_annual
            + self.insurance_annual
            + self.pmi_annual
            + self.hoa_annual
            + self.maintenance_annual
            + self.capex_reserve_annual
            + management_fee
        )

        noi = egi - opex
        cash_flow_bt = noi - self.annual_debt_service

        coc = (cash_flow_bt / self.total_cash_invested * 100) if self.total_cash_invested > 0 else 0
        cap_rate = (noi / self.purchase_price * 100) if self.purchase_price > 0 else 0
        gross_yield = (gross_income / self.purchase_price * 100) if self.purchase_price > 0 else 0
        rtv = (self.estimated_rent / self.purchase_price * 100) if self.purchase_price > 0 else 0
        dscr = (noi / self.annual_debt_service) if self.annual_debt_service > 0 else float('inf')
        opex_ratio = (opex / egi * 100) if egi > 0 else 0

        # Break-even occupancy: (opex + debt service) / gross income
        if gross_income > 0:
            be_occ = ((opex + self.annual_debt_service) / gross_income * 100)
        else:
            be_occ = 100.0

        return CoreMetrics(
            gross_rental_income=round(gross_income, 2),
            vacancy_loss=round(vacancy_loss, 2),
            effective_gross_income=round(egi, 2),
            operating_expenses=round(opex, 2),
            noi=round(noi, 2),
            annual_debt_service=round(self.annual_debt_service, 2),
            cash_flow_before_tax=round(cash_flow_bt, 2),
            total_cash_invested=round(self.total_cash_invested, 2),
            cash_on_cash_return=round(coc, 2),
            cap_rate=round(cap_rate, 2),
            gross_rental_yield=round(gross_yield, 2),
            rent_to_value=round(rtv, 3),
            dscr=round(dscr, 2),
            opex_ratio=round(opex_ratio, 2),
            break_even_occupancy=round(min(be_occ, 100), 2),
            capex_reserve_annual=round(self.capex_reserve_annual, 2),
        )

    # ----- Multi-Year Projection -----

    def generate_multi_year_projection(self) -> MultiYearProjection:
        years: List[YearProjection] = []
        cash_flows = [-self.total_cash_invested]  # IRR cash flow series

        cumulative_depreciation = 0.0

        for yr in range(1, 31):
            growth_factor_rent = (1 + self.rent_growth_rate) ** (yr - 1)
            growth_factor_expense = (1 + self.expense_growth_rate) ** (yr - 1)
            growth_factor_value = (1 + self.appreciation_rate) ** yr

            gross_income = self.estimated_rent * 12 * growth_factor_rent
            vac_loss = gross_income * self.vacancy_rate
            egi = gross_income - vac_loss

            management_fee = gross_income * self.management_fee_pct
            opex = (
                self.property_tax_annual * growth_factor_expense
                + self.insurance_annual * growth_factor_expense
                + self.pmi_annual  # PMI doesn't inflate
                + self.hoa_annual * growth_factor_expense
                + self.maintenance_annual * growth_factor_expense
                + self.capex_reserve_annual * growth_factor_expense
                + management_fee
            )

            noi = egi - opex
            debt_service = self.annual_debt_service
            cf_bt = noi - debt_service

            # Tax analysis
            depreciation = self.annual_depreciation
            cumulative_depreciation += depreciation

            # Get mortgage interest from amortization schedule
            if yr <= len(self.amortization):
                mortgage_interest = self.amortization[yr - 1]["interest_paid"]
                loan_balance = self.amortization[yr - 1]["remaining_balance"]
            else:
                mortgage_interest = 0.0
                loan_balance = 0.0

            taxable_income = noi - depreciation - mortgage_interest
            tax = taxable_income * self.marginal_tax_rate if taxable_income > 0 else 0
            cf_at = cf_bt - tax

            prop_value = self.purchase_price * growth_factor_value
            equity = prop_value - loan_balance
            roe = (cf_bt / equity * 100) if equity > 0 else 0

            yp = YearProjection(
                year=yr,
                gross_income=round(gross_income, 2),
                vacancy_loss=round(vac_loss, 2),
                effective_income=round(egi, 2),
                operating_expenses=round(opex, 2),
                noi=round(noi, 2),
                debt_service=round(debt_service, 2),
                cash_flow_before_tax=round(cf_bt, 2),
                depreciation=round(depreciation, 2),
                mortgage_interest=round(mortgage_interest, 2),
                taxable_income=round(taxable_income, 2),
                tax_liability=round(tax, 2),
                cash_flow_after_tax=round(cf_at, 2),
                property_value=round(prop_value, 2),
                loan_balance=round(loan_balance, 2),
                equity=round(equity, 2),
                return_on_equity=round(roe, 2),
            )
            years.append(yp)

            # For IRR: annual after-tax cash flow (add terminal sale at hold_years)
            if yr <= self.hold_years:
                cash_flows.append(cf_at)

        # Terminal sale at hold_years
        hold_yr = years[self.hold_years - 1] if self.hold_years <= len(years) else years[-1]
        terminal_sale_price = hold_yr.property_value
        selling_costs = terminal_sale_price * 0.06
        dep_recapture_tax = cumulative_depreciation * 0.25 if self.hold_years <= 27 else (self.depreciable_basis * 0.25)
        # Only recapture up to hold_years of depreciation
        dep_recapture_tax = min(self.annual_depreciation * self.hold_years, self.depreciable_basis) * 0.25
        net_sale = terminal_sale_price - selling_costs - hold_yr.loan_balance - dep_recapture_tax

        # Add net sale proceeds to final year cash flow for IRR
        if len(cash_flows) > 1:
            cash_flows[-1] += net_sale

        irr = self.calculate_irr(cash_flows)
        npv = self.calculate_npv(cash_flows, 0.08)
        total_cash_returned = sum(cf for cf in cash_flows[1:])
        equity_multiple = (total_cash_returned / self.total_cash_invested) if self.total_cash_invested > 0 else 0

        if irr is not None:
            annualized = irr * 100
        else:
            annualized = None

        return MultiYearProjection(
            years=years,
            irr=round(irr * 100, 2) if irr is not None else None,
            npv=round(npv, 2) if npv is not None else None,
            equity_multiple=round(equity_multiple, 2),
            annualized_return=round(annualized, 2) if annualized is not None else None,
            terminal_sale_price=round(terminal_sale_price, 2),
            selling_costs=round(selling_costs, 2),
            depreciation_recapture_tax=round(dep_recapture_tax, 2),
            net_sale_proceeds=round(net_sale, 2),
        )

    # ----- IRR (Newton-Raphson) -----

    @staticmethod
    def calculate_irr(cash_flows: List[float], max_iter: int = 200, tol: float = 1e-8) -> Optional[float]:
        """Calculate IRR using Newton-Raphson. Returns decimal (e.g. 0.12 = 12%)."""
        if not cash_flows or len(cash_flows) < 2:
            return None

        # Sanity check: if sum of all cash flows is negative, IRR is negative
        # (or undefined). If total returned < invested, cap the search range.
        total = sum(cash_flows)
        total_invested = abs(cash_flows[0])
        total_returned = sum(cash_flows[1:])

        # If total cash returned is negative, IRR is deeply negative / undefined
        if total_returned <= 0:
            return None

        # Initial guess based on simple return
        if total_invested > 0:
            simple_return = (total_returned - total_invested) / total_invested
            r = max(-0.5, min(simple_return / len(cash_flows), 0.5))
        else:
            r = 0.10

        lo_clamp = -0.99
        hi_clamp = 2.0  # Cap at 200% — anything higher is nonsensical

        for _ in range(max_iter):
            npv = sum(cf / (1 + r) ** t for t, cf in enumerate(cash_flows))
            dnpv = sum(-t * cf / (1 + r) ** (t + 1) for t, cf in enumerate(cash_flows))

            if abs(dnpv) < 1e-12:
                break

            r_new = r - npv / dnpv

            # Clamp to reasonable range
            r_new = max(lo_clamp, min(r_new, hi_clamp))

            # If stuck at a clamp boundary, solver can't converge — bail
            if abs(r_new - r) < tol:
                if abs(r_new - hi_clamp) < tol or abs(r_new - lo_clamp) < tol:
                    # Stuck at boundary — not a real solution
                    break
                return r_new

            r = r_new

        # Verify convergence: NPV at r should be near zero
        npv_check = sum(cf / (1 + r) ** t for t, cf in enumerate(cash_flows))
        if abs(npv_check) < max(1.0, total_invested * 0.001):
            return r
        return None

    # ----- NPV -----

    @staticmethod
    def calculate_npv(cash_flows: List[float], discount_rate: float = 0.08) -> Optional[float]:
        if not cash_flows:
            return None
        return sum(cf / (1 + discount_rate) ** t for t, cf in enumerate(cash_flows))

    # ----- Tax Analysis (Year 1) -----

    def calculate_tax_analysis(self, core: CoreMetrics) -> TaxAnalysis:
        interest_yr1 = self.amortization[0]["interest_paid"] if self.amortization else 0

        taxable_income = core.noi - self.annual_depreciation - interest_yr1
        paper_loss = min(taxable_income, 0)
        tax_savings = abs(paper_loss) * self.marginal_tax_rate if paper_loss < 0 else 0
        tax_owed = taxable_income * self.marginal_tax_rate if taxable_income > 0 else 0

        cf_after_tax = core.cash_flow_before_tax - tax_owed + tax_savings

        return TaxAnalysis(
            annual_depreciation=round(self.annual_depreciation, 2),
            depreciable_basis=round(self.depreciable_basis, 2),
            mortgage_interest_year1=round(interest_yr1, 2),
            noi=round(core.noi, 2),
            taxable_income=round(taxable_income, 2),
            paper_loss=round(paper_loss, 2),
            tax_savings=round(tax_savings, 2),
            effective_cash_flow_after_tax=round(cf_after_tax, 2),
            marginal_tax_rate=self.marginal_tax_rate,
        )

    # ----- Stress Tests -----

    def run_stress_tests(self, core: CoreMetrics) -> RiskAnalysis:
        scenarios: List[StressScenario] = []

        base_gross = self.estimated_rent * 12
        base_management = base_gross * self.management_fee_pct
        base_opex_no_mgmt = (
            self.property_tax_annual + self.insurance_annual + self.pmi_annual
            + self.hoa_annual + self.maintenance_annual + self.capex_reserve_annual
        )

        def calc_scenario(name: str, desc: str, vacancy: float, rent_mult: float,
                          expense_mult: float, rate_add: float) -> StressScenario:
            gross = base_gross * rent_mult
            vac = gross * vacancy
            egi = gross - vac
            mgmt = gross * self.management_fee_pct
            opex = base_opex_no_mgmt * expense_mult + mgmt

            noi = egi - opex

            # Recalculate debt service if rate changes
            if rate_add > 0:
                calc = LoanCalculator()
                new_pmt = calc.calculate_monthly_payment(
                    self.loan_amount, self.interest_rate + rate_add, self.loan_term
                )
                ds = new_pmt * 12
            else:
                ds = self.annual_debt_service

            cf = noi - ds
            dscr = noi / ds if ds > 0 else float('inf')
            coc = (cf / self.total_cash_invested * 100) if self.total_cash_invested > 0 else 0

            return StressScenario(
                name=name,
                description=desc,
                cash_flow_monthly=round(cf / 12, 2),
                cash_flow_annual=round(cf, 2),
                dscr=round(dscr, 2),
                cash_on_cash=round(coc, 2),
                passes=cf >= 0 and dscr >= 1.0,
            )

        scenarios.append(calc_scenario(
            "Vacancy Doubles", f"Vacancy increases from {self.vacancy_rate*100:.0f}% to {self.vacancy_rate*200:.0f}%",
            self.vacancy_rate * 2, 1.0, 1.0, 0.0))
        scenarios.append(calc_scenario(
            "Rate +2%", f"Interest rate rises from {self.interest_rate*100:.1f}% to {(self.interest_rate+0.02)*100:.1f}%",
            self.vacancy_rate, 1.0, 1.0, 0.02))
        scenarios.append(calc_scenario(
            "Rent -10%", "Rents decline 10%",
            self.vacancy_rate, 0.90, 1.0, 0.0))
        scenarios.append(calc_scenario(
            "Rent -20%", "Rents decline 20%",
            self.vacancy_rate, 0.80, 1.0, 0.0))
        scenarios.append(calc_scenario(
            "Expense Surge", "Operating expenses increase 50%",
            self.vacancy_rate, 1.0, 1.50, 0.0))
        scenarios.append(calc_scenario(
            "Combined Downturn", "Vacancy +50%, rent -10%, expenses +20%",
            self.vacancy_rate * 1.5, 0.90, 1.20, 0.0))

        # Break-even calculations
        be = self._calc_break_evens(core)

        # Overall risk score: count failing scenarios
        fail_count = sum(1 for s in scenarios if not s.passes)
        risk_score = fail_count / len(scenarios) * 100 if scenarios else 0

        return RiskAnalysis(
            scenarios=scenarios,
            break_even=be,
            overall_risk_score=round(risk_score, 1),
        )

    def _calc_break_evens(self, core: CoreMetrics) -> BreakEvenMetrics:
        # Min rent to break even (monthly)
        # Need: rent*12*(1-vac) - opex - debt_service >= 0
        # rent_annual*(1-vac) >= opex + ds
        opex = core.operating_expenses
        ds = self.annual_debt_service
        required_annual = (opex + ds) / (1 - self.vacancy_rate) if self.vacancy_rate < 1 else float('inf')
        min_rent = required_annual / 12

        # Max purchase price for 8% CoC
        # CoC = cf / cash_invested => cf = 0.08 * cash_invested
        # cash_invested = price * dp_pct + upfront
        # cf = NOI - DS
        # This is complex; approximate by scaling
        target_coc = 0.08
        if self.total_cash_invested > 0 and self.purchase_price > 0:
            current_cf = core.cash_flow_before_tax
            needed_cf = target_coc * self.total_cash_invested
            if current_cf > needed_cf:
                max_price = self.purchase_price * 1.5  # generous cap
            elif core.noi > 0:
                # Approximate: lower price reduces DS and cash invested proportionally
                ratio = core.noi / (core.noi - current_cf + needed_cf) if (core.noi - current_cf + needed_cf) > 0 else 1
                max_price = self.purchase_price * min(ratio, 2.0)
            else:
                max_price = 0
        else:
            max_price = 0

        # Max interest rate: find rate where NOI = DS
        # Binary search
        max_rate = self._find_max_rate(core.noi)

        # Max vacancy: find vac where cash flow = 0
        gross = self.estimated_rent * 12
        if gross > 0:
            # NOI at vac v: gross*(1-v) - mgmt - opex_fixed
            # CF = NOI - DS = 0
            # gross*(1-v) - mgmt_ratio*gross - opex_fixed = DS
            # gross*(1-v)*(1 - mgmt_ratio) ... simplify
            # Approximate: NOI(v) = gross*(1-v) - opex (where opex includes mgmt)
            # NOI = DS => v = 1 - (DS + opex) / gross
            max_vac = 1 - (ds + opex) / gross if gross > 0 else 0
            max_vac = max(0, min(max_vac, 1.0))
        else:
            max_vac = 0

        return BreakEvenMetrics(
            min_monthly_rent=round(max(min_rent, 0), 2),
            max_purchase_price=round(max(max_price, 0), 2),
            max_interest_rate=round(max_rate * 100, 2),
            max_vacancy_rate=round(max_vac * 100, 2),
        )

    def _find_max_rate(self, noi: float) -> float:
        """Binary search for max interest rate where NOI covers debt service."""
        if noi <= 0 or self.loan_amount <= 0:
            return 0.0

        calc = LoanCalculator()
        lo, hi = 0.001, 0.25  # ~0% to 25%

        for _ in range(50):
            mid = (lo + hi) / 2
            pmt = calc.calculate_monthly_payment(self.loan_amount, mid, self.loan_term)
            ds = pmt * 12
            if ds < noi:
                lo = mid
            else:
                hi = mid

        return lo

    # ----- Comparable Analysis -----

    async def build_comparable_analysis(
        self,
        rentcast_client: RentCastClient,
        zip_code: str,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        sqft: Optional[int] = None,
        property_type: Optional[str] = None,
    ) -> ComparableAnalysis:
        result = ComparableAnalysis()

        sqft_min = int(sqft * 0.7) if sqft else None
        sqft_max = int(sqft * 1.3) if sqft else None

        # Fetch sale comps
        try:
            sale_data = await rentcast_client.get_sale_listings(
                zip_code=zip_code, bedrooms=bedrooms, bathrooms=bathrooms,
                sqft_min=sqft_min, sqft_max=sqft_max, property_type=property_type, limit=10,
            )
            for item in sale_data:
                price = item.get("price", 0)
                sf = item.get("squareFootage", 0) or item.get("sqft", 0)
                if price and sf:
                    result.sale_comps.append(CompProperty(
                        address=item.get("formattedAddress", item.get("address", "")),
                        price=price,
                        sqft=sf,
                        price_per_sqft=round(price / sf, 2),
                        bedrooms=item.get("bedrooms"),
                        bathrooms=item.get("bathrooms"),
                    ))
        except Exception:
            pass

        # Fetch rental comps
        try:
            rental_data = await rentcast_client.get_rental_listings(
                zip_code=zip_code, bedrooms=bedrooms, bathrooms=bathrooms,
                sqft_min=sqft_min, sqft_max=sqft_max, property_type=property_type, limit=10,
            )
            for item in rental_data:
                price = item.get("price", 0) or item.get("rent", 0)
                sf = item.get("squareFootage", 0) or item.get("sqft", 0)
                if price and sf:
                    result.rental_comps.append(CompProperty(
                        address=item.get("formattedAddress", item.get("address", "")),
                        price=price,
                        sqft=sf,
                        price_per_sqft=round(price / sf, 2),
                        bedrooms=item.get("bedrooms"),
                        bathrooms=item.get("bathrooms"),
                    ))
        except Exception:
            pass

        # Compute medians
        if result.sale_comps:
            result.median_sale_price_sqft = round(
                statistics.median(c.price_per_sqft for c in result.sale_comps), 2
            )
        if result.rental_comps:
            result.median_rent_sqft = round(
                statistics.median(c.price_per_sqft for c in result.rental_comps), 2
            )

        # Subject property comparison
        if sqft and sqft > 0:
            result.subject_price_sqft = round(self.purchase_price / sqft, 2)
            result.subject_rent_sqft = round(self.estimated_rent / sqft, 2)

            if result.median_sale_price_sqft and result.subject_price_sqft:
                ratio = result.subject_price_sqft / result.median_sale_price_sqft
                if ratio > 1.05:
                    result.price_vs_market = "above"
                elif ratio < 0.95:
                    result.price_vs_market = "below"
                else:
                    result.price_vs_market = "at"

            if result.median_rent_sqft and result.subject_rent_sqft:
                ratio = result.subject_rent_sqft / result.median_rent_sqft
                if ratio > 1.05:
                    result.rent_vs_market = "above"
                elif ratio < 0.95:
                    result.rent_vs_market = "below"
                else:
                    result.rent_vs_market = "at"

        return result

    # ----- Score All Strategies -----

    def score_all_strategies(
        self,
        core: CoreMetrics,
        projection: MultiYearProjection,
        risk: RiskAnalysis,
    ) -> List[StrategyScore]:
        scores = []
        scores.append(self._score_rental(core, projection, risk))
        scores.append(self._score_flip(core))
        scores.append(self._score_brrrr(core, projection))
        scores.append(self._score_house_hack(core))
        scores.append(self._score_long_term(core, projection, risk))
        return scores

    @staticmethod
    def _to_grade(score: float) -> str:
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 55:
            return "C-"
        elif score >= 50:
            return "D+"
        elif score >= 45:
            return "D"
        elif score >= 40:
            return "D-"
        else:
            return "F"

    def _score_rental(self, core: CoreMetrics, proj: MultiYearProjection, risk: RiskAnalysis) -> StrategyScore:
        # CoC 25%, Cap Rate 20%, DSCR 20%, Cash Flow 15%, IRR 10%, Risk 10%
        coc_score = min(100, max(0, core.cash_on_cash_return / 8 * 100))  # 8% = 100
        cap_score = min(100, max(0, core.cap_rate / 6 * 100))  # 6% = 100
        dscr_score = min(100, max(0, (core.dscr - 0.5) / 1.0 * 100))  # 1.5 = 100
        cf_score = min(100, max(0, core.cash_flow_before_tax / 12 / 200 * 100))  # $200/mo = 100
        irr_score = min(100, max(0, (proj.irr or 0) / 15 * 100))  # 15% = 100
        risk_score = max(0, 100 - risk.overall_risk_score)

        components = {
            "Cash-on-Cash": round(coc_score, 1),
            "Cap Rate": round(cap_score, 1),
            "DSCR": round(dscr_score, 1),
            "Cash Flow": round(cf_score, 1),
            "IRR": round(irr_score, 1),
            "Risk": round(risk_score, 1),
        }
        total = (coc_score * 0.25 + cap_score * 0.20 + dscr_score * 0.20
                 + cf_score * 0.15 + irr_score * 0.10 + risk_score * 0.10)

        pros, cons = [], []
        if core.cash_on_cash_return >= 8:
            pros.append(f"Strong cash-on-cash return ({core.cash_on_cash_return:.1f}%)")
        else:
            cons.append(f"Low cash-on-cash return ({core.cash_on_cash_return:.1f}%)")
        if core.dscr >= 1.25:
            pros.append(f"Healthy DSCR ({core.dscr:.2f})")
        else:
            cons.append(f"Tight DSCR ({core.dscr:.2f})")
        if core.cash_flow_before_tax > 0:
            pros.append(f"Positive cash flow (${core.cash_flow_before_tax/12:.0f}/mo)")
        else:
            cons.append(f"Negative cash flow (${core.cash_flow_before_tax/12:.0f}/mo)")

        return StrategyScore(
            strategy="rental",
            score=round(min(total, 100), 1),
            grade=self._to_grade(total),
            pros=pros, cons=cons,
            component_scores=components,
        )

    def _score_flip(self, core: CoreMetrics) -> StrategyScore:
        # For flip: profit margin based on 70% rule (ARV * 0.7 - repairs = max offer)
        # Without rehab data, approximate from cap rate and appreciation
        arv_estimate = self.purchase_price * (1 + self.appreciation_rate)
        profit = arv_estimate - self.purchase_price
        margin = (profit / self.purchase_price * 100) if self.purchase_price > 0 else 0

        margin_score = min(100, max(0, margin / 20 * 100))  # 20% margin = 100
        roi_score = min(100, max(0, margin / 15 * 100))  # annualized

        components = {"Profit Margin": round(margin_score, 1), "ROI": round(roi_score, 1)}
        total = margin_score * 0.6 + roi_score * 0.4

        pros, cons = [], []
        if margin >= 15:
            pros.append(f"Estimated {margin:.1f}% appreciation margin")
        else:
            cons.append(f"Low flip margin ({margin:.1f}%) without rehab data")
        cons.append("Flip analysis requires rehab cost and ARV inputs for accuracy")

        return StrategyScore(
            strategy="flip",
            score=round(min(total, 100), 1),
            grade=self._to_grade(total),
            pros=pros, cons=cons,
            component_scores=components,
        )

    def _score_brrrr(self, core: CoreMetrics, proj: MultiYearProjection) -> StrategyScore:
        # Rental metrics + equity extraction post-refi
        # Assume refi at 75% LTV after year 1
        yr1_value = self.purchase_price * (1 + self.appreciation_rate)
        refi_loan = yr1_value * 0.75
        equity_extraction = refi_loan - self.loan_amount
        extraction_pct = (equity_extraction / self.total_cash_invested * 100) if self.total_cash_invested > 0 else 0

        rental_score = min(100, max(0, core.cash_on_cash_return / 10 * 100))  # 10% = 100
        extraction_score = min(100, max(0, extraction_pct / 100 * 100))  # 100% extraction = 100
        dscr_score = min(100, max(0, (core.dscr - 0.5) / 1.0 * 100))

        components = {
            "Rental Return": round(rental_score, 1),
            "Equity Extraction": round(extraction_score, 1),
            "DSCR": round(dscr_score, 1),
        }
        total = rental_score * 0.4 + extraction_score * 0.35 + dscr_score * 0.25

        pros, cons = [], []
        if extraction_pct >= 70:
            pros.append(f"Strong equity extraction potential ({extraction_pct:.0f}%)")
        else:
            cons.append(f"Limited equity extraction ({extraction_pct:.0f}%)")
        if core.cash_on_cash_return >= 10:
            pros.append(f"Meets BRRRR CoC target ({core.cash_on_cash_return:.1f}%)")
        else:
            cons.append(f"Below BRRRR CoC target ({core.cash_on_cash_return:.1f}% vs 10%)")
        cons.append("BRRRR analysis requires rehab cost and ARV for full accuracy")

        return StrategyScore(
            strategy="brrrr",
            score=round(min(total, 100), 1),
            grade=self._to_grade(total),
            pros=pros, cons=cons,
            component_scores=components,
        )

    def _score_house_hack(self, core: CoreMetrics) -> StrategyScore:
        # Rental coverage %, personal housing cost reduction
        total_payment = self.loan_details.get("total_monthly_payment", 0)
        rental_coverage = (self.estimated_rent / total_payment * 100) if total_payment > 0 else 0

        # Assume renting half the units: coverage / 2 covers your half
        personal_cost = total_payment - self.estimated_rent * 0.5  # if renting half
        cost_reduction = ((total_payment - personal_cost) / total_payment * 100) if total_payment > 0 else 0

        coverage_score = min(100, max(0, rental_coverage / 100 * 100))  # 100% coverage = 100
        cost_score = min(100, max(0, cost_reduction / 50 * 100))  # 50% reduction = 100

        components = {"Rental Coverage": round(coverage_score, 1), "Cost Reduction": round(cost_score, 1)}
        total = coverage_score * 0.6 + cost_score * 0.4

        pros, cons = [], []
        if rental_coverage >= 75:
            pros.append(f"Strong rental coverage ({rental_coverage:.0f}% of payment)")
        elif rental_coverage >= 50:
            pros.append(f"Moderate rental coverage ({rental_coverage:.0f}% of payment)")
        else:
            cons.append(f"Low rental coverage ({rental_coverage:.0f}% of payment)")

        if personal_cost < total_payment * 0.5:
            pros.append(f"Significant housing cost reduction")
        else:
            cons.append("Limited personal cost savings")

        return StrategyScore(
            strategy="house_hack",
            score=round(min(total, 100), 1),
            grade=self._to_grade(total),
            pros=pros, cons=cons,
            component_scores=components,
        )

    def _score_long_term(self, core: CoreMetrics, proj: MultiYearProjection, risk: RiskAnalysis) -> StrategyScore:
        # 10-year IRR, net equity (equity minus cumulative losses), appreciation, risk
        irr_10 = proj.irr or 0
        irr_score = min(100, max(0, irr_10 / 12 * 100))  # 12% = 100

        # Net equity: equity at year 10 minus cumulative cash losses
        yr10 = proj.years[9] if len(proj.years) >= 10 else (proj.years[-1] if proj.years else None)
        if yr10 and self.total_cash_invested > 0:
            cumulative_cf = sum(y.cash_flow_before_tax for y in proj.years[:10])
            net_equity = yr10.equity + cumulative_cf  # cumulative_cf is negative when losing money
            equity_mult = net_equity / self.total_cash_invested
            equity_score = min(100, max(0, equity_mult / 5 * 100))  # 5x = 100
        else:
            equity_score = 0
            cumulative_cf = 0
            net_equity = 0

        app_score = min(100, max(0, self.appreciation_rate / 0.05 * 100))  # 5% = 100
        risk_score = max(0, 100 - risk.overall_risk_score)

        # Cash flow penalty: if losing money every year, cap overall score
        cf_penalty = 1.0
        if core.cash_flow_before_tax < 0:
            # Scale penalty by how severe the loss is relative to investment
            annual_loss_ratio = abs(core.cash_flow_before_tax) / max(self.total_cash_invested, 1)
            cf_penalty = max(0.1, 1.0 - annual_loss_ratio)

        components = {
            "10Y IRR": round(irr_score, 1),
            "Net Equity": round(equity_score, 1),
            "Appreciation": round(app_score, 1),
            "Risk": round(risk_score, 1),
        }
        raw_total = irr_score * 0.35 + equity_score * 0.30 + app_score * 0.20 + risk_score * 0.15
        total = raw_total * cf_penalty

        pros, cons = [], []
        if irr_10 >= 10:
            pros.append(f"Strong projected IRR ({irr_10:.1f}%)")
        elif irr_10 > 0:
            cons.append(f"Moderate projected IRR ({irr_10:.1f}%)")
        else:
            cons.append(f"Negative or undefined IRR")
        if yr10:
            if cumulative_cf < 0:
                cons.append(f"Cumulative cash loss of ${abs(cumulative_cf):,.0f} over 10 years")
            if net_equity > 0:
                pros.append(f"Net equity of ${net_equity:,.0f} at year 10 (after cash losses)")
            else:
                cons.append(f"Negative net equity at year 10 after cash losses")
        if self.appreciation_rate >= 0.04:
            pros.append(f"Above-average appreciation assumption ({self.appreciation_rate*100:.1f}%)")
        else:
            cons.append(f"Conservative appreciation ({self.appreciation_rate*100:.1f}%)")

        return StrategyScore(
            strategy="long_term_appreciation",
            score=round(min(total, 100), 1),
            grade=self._to_grade(total),
            pros=pros, cons=cons,
            component_scores=components,
        )

    # ----- Executive Summary -----

    def generate_executive_summary(
        self,
        core: CoreMetrics,
        projection: MultiYearProjection,
        tax: TaxAnalysis,
        risk: RiskAnalysis,
        best: Optional[StrategyScore],
    ) -> List[str]:
        summary = []

        # Best strategy
        if best:
            summary.append(
                f"Best strategy: {best.strategy.replace('_', ' ').title()} "
                f"(Score: {best.score}/100, Grade: {best.grade})"
            )

        # Cash flow
        monthly_cf = core.cash_flow_before_tax / 12
        if monthly_cf >= 0:
            summary.append(f"Positive monthly cash flow of ${monthly_cf:,.0f} before tax")
        else:
            summary.append(f"Negative monthly cash flow of ${monthly_cf:,.0f} - property requires subsidy")

        # IRR
        if projection.irr is not None:
            summary.append(
                f"Projected {self.hold_years}-year IRR of {projection.irr:.1f}% "
                f"with ${projection.net_sale_proceeds:,.0f} net sale proceeds"
            )

        # Tax benefit
        if tax.paper_loss < 0:
            summary.append(f"Tax shelter: ${abs(tax.paper_loss):,.0f} paper loss generates ${tax.tax_savings:,.0f} in tax savings (Year 1)")
        else:
            summary.append(f"Taxable income of ${tax.taxable_income:,.0f} in Year 1")

        # Risk
        passing = sum(1 for s in risk.scenarios if s.passes)
        total = len(risk.scenarios)
        summary.append(f"Risk: passes {passing}/{total} stress tests")

        # Cap rate context
        if core.cap_rate >= 6:
            summary.append(f"Cap rate of {core.cap_rate:.1f}% indicates solid income relative to price")
        elif core.cap_rate >= 4:
            summary.append(f"Cap rate of {core.cap_rate:.1f}% is moderate - typical for stable markets")
        else:
            summary.append(f"Cap rate of {core.cap_rate:.1f}% is low - may be an appreciation play")

        return summary


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class PropertyAnalyzer:
    """Orchestrates full property analysis. Same interface: URL in, dict out."""

    def __init__(self):
        self.loan_calculator = LoanCalculator()
        self.rentcast_client = RentCastClient()

    async def analyze_property(
        self,
        property_url: str,
        strategy_type: str = InvestmentStrategy.RENTAL,
        loan_type: str = LoanCalculator.CONVENTIONAL,
        down_payment_pct: Optional[float] = None,
        interest_rate: float = 0.065,
        loan_term_years: int = 30,
        purchase_price: Optional[float] = None,
        estimated_rent: Optional[float] = None,
        property_tax_annual: Optional[float] = None,
        insurance_annual: Optional[float] = None,
        hoa_monthly: float = 0.0,
        maintenance_pct: float = 0.01,
        vacancy_rate: float = 0.05,
        management_fee_pct: float = 0.10,
        # New params
        appreciation_rate: float = 0.04,
        rent_growth_rate: float = 0.03,
        expense_growth_rate: float = 0.02,
        marginal_tax_rate: float = 0.22,
        hold_years: int = 10,
        capex_reserve_pct: float = 0.03,
    ) -> Dict:
        from .url_parser import PropertyURLParser

        parser = PropertyURLParser()
        property_info = parser.parse_property_url(property_url)

        if not property_info:
            return {"error": "Could not parse property URL",
                    "suggestions": ["Ensure URL is from Zillow or Realtor.com"]}

        address = property_info.get("address")

        # --- Fetch property data ---
        property_data: Dict[str, Any] = {}
        zip_code: Optional[str] = None
        bedrooms: Optional[int] = None
        bathrooms: Optional[float] = None
        sqft: Optional[int] = None
        property_type: Optional[str] = None

        try:
            properties = await self.rentcast_client.search_properties_by_address(address, limit=1)

            if not properties:
                valuation_data = await self.rentcast_client.get_property_valuation(address)
                rent_data = await self.rentcast_client.get_rent_estimate(address)

                zip_match = re.search(r'\b\d{5}\b', address)
                zip_code = zip_match.group(0) if zip_match else None

                property_data = {
                    "address": address,
                    "estimated_value": valuation_data.get("price", purchase_price),
                    "estimated_rent": rent_data.get("rent", estimated_rent),
                    "zip_code": zip_code,
                }
            else:
                property_data = properties[0]
                zip_code = property_data.get("zipCode") or property_data.get("zip")
                bedrooms = property_data.get("bedrooms")
                bathrooms = property_data.get("bathrooms")
                sqft = property_data.get("squareFootage") or property_data.get("sqft")
                property_type = property_data.get("propertyType")

            if purchase_price is None:
                purchase_price = (
                    property_data.get("price")
                    or property_data.get("estimated_value")
                    or property_data.get("lastSalePrice")
                    or 0
                )
            if purchase_price == 0:
                return {"error": "Could not determine property price",
                        "suggestions": ["Provide purchase price manually"]}

            if estimated_rent is None:
                estimated_rent = (
                    property_data.get("rent")
                    or property_data.get("estimated_rent")
                    or property_data.get("rentEstimate")
                    or 0
                )

            # If still no rent, call the rent estimate API
            if not estimated_rent and address:
                try:
                    rent_data = await self.rentcast_client.get_rent_estimate(
                        address,
                        property_type=property_type,
                        bedrooms=bedrooms,
                        bathrooms=bathrooms,
                        square_footage=sqft,
                    )
                    estimated_rent = rent_data.get("rent", 0)
                except Exception:
                    pass

            # Market statistics
            market_stats = None
            if zip_code:
                try:
                    market_stats = await self.rentcast_client.get_market_statistics(zip_code)
                except Exception:
                    pass

        except Exception as e:
            return {"error": f"Error fetching property data: {str(e)}",
                    "property_info": property_info}

        # --- Loan calculation ---
        loan_details = self.loan_calculator.calculate_loan_details(
            purchase_price=purchase_price,
            loan_type=loan_type,
            down_payment_pct=down_payment_pct,
            interest_rate=interest_rate,
            loan_term_years=loan_term_years,
            property_tax_annual=property_tax_annual,
            insurance_annual=insurance_annual,
            hoa_monthly=hoa_monthly,
        )

        # --- Amortization ---
        amortization = self.loan_calculator.generate_amortization_schedule(
            loan_amount=loan_details["loan_amount"],
            annual_rate=interest_rate,
            years=loan_term_years,
        )

        # --- Build calculator ---
        calc = InvestmentCalculator(
            purchase_price=purchase_price,
            estimated_rent=estimated_rent or 0,
            loan_details=loan_details,
            amortization=amortization,
            vacancy_rate=vacancy_rate,
            maintenance_pct=maintenance_pct,
            management_fee_pct=management_fee_pct,
            capex_reserve_pct=capex_reserve_pct,
            appreciation_rate=appreciation_rate,
            rent_growth_rate=rent_growth_rate,
            expense_growth_rate=expense_growth_rate,
            marginal_tax_rate=marginal_tax_rate,
            hold_years=hold_years,
        )

        # --- Run all analyses ---
        core = calc.calculate_core_metrics()
        projection = calc.generate_multi_year_projection()
        tax = calc.calculate_tax_analysis(core)
        risk = calc.run_stress_tests(core)

        # Comps (graceful failure)
        comps = ComparableAnalysis()
        if zip_code:
            try:
                comps = await calc.build_comparable_analysis(
                    self.rentcast_client, zip_code, bedrooms, bathrooms, sqft, property_type,
                )
            except Exception:
                pass

        # Score all strategies
        strategy_scores = calc.score_all_strategies(core, projection, risk)
        best_strategy = max(strategy_scores, key=lambda s: s.score) if strategy_scores else None

        # Executive summary
        summary = calc.generate_executive_summary(core, projection, tax, risk, best_strategy)

        result = FullAnalysisResult(
            property_info=property_info,
            property_data=property_data,
            market_statistics=market_stats,
            loan_details=loan_details,
            core_metrics=core,
            projection=projection,
            tax_analysis=tax,
            risk_analysis=risk,
            comparables=comps,
            strategy_scores=strategy_scores,
            best_strategy=best_strategy,
            executive_summary=summary,
            selected_strategy=strategy_type,
        )

        return result.model_dump()
