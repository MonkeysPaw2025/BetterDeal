"""
Loan Calculator

Calculates mortgage payments and costs for different loan types.
"""

from typing import Dict, Optional
from decimal import Decimal, ROUND_HALF_UP


class LoanCalculator:
    """Calculator for different loan types and scenarios."""
    
    # Loan type constants
    CONVENTIONAL = "conventional"
    FHA = "fha"
    VA = "va"
    USDA = "usda"
    
    def __init__(self):
        # Default loan parameters
        self.loan_limits = {
            self.CONVENTIONAL: {
                "min_down_payment_pct": 0.05,  # 5% minimum
                "default_down_payment_pct": 0.20,  # 20% default
                "pmi_rate_annual": 0.005,  # 0.5% annual PMI
                "max_loan_amount": 766550,  # 2024 conforming loan limit
            },
            self.FHA: {
                "min_down_payment_pct": 0.035,  # 3.5% minimum
                "default_down_payment_pct": 0.035,
                "mip_rate_annual": 0.0085,  # 0.85% annual MIP
                "mip_upfront": 0.0175,  # 1.75% upfront MIP
                "max_loan_amount": 498257,  # 2024 FHA limit (varies by area)
            },
            self.VA: {
                "min_down_payment_pct": 0.0,  # 0% down payment
                "default_down_payment_pct": 0.0,
                "funding_fee_pct": 0.0215,  # 2.15% funding fee (varies)
                "no_pmi": True,
            },
            self.USDA: {
                "min_down_payment_pct": 0.0,  # 0% down payment
                "default_down_payment_pct": 0.0,
                "guarantee_fee_annual": 0.0035,  # 0.35% annual
                "guarantee_fee_upfront": 0.01,  # 1% upfront
                "max_income": None,  # Income limits apply
            },
        }
    
    def calculate_monthly_payment(
        self,
        principal: float,
        annual_rate: float,
        years: int = 30
    ) -> float:
        """Calculate monthly mortgage payment using standard formula."""
        if principal <= 0:
            return 0.0
        
        monthly_rate = annual_rate / 12.0
        num_payments = years * 12
        
        if monthly_rate == 0:
            return principal / num_payments
        
        # M = P * [r(1+r)^n] / [(1+r)^n - 1]
        monthly_payment = principal * (
            (monthly_rate * (1 + monthly_rate) ** num_payments) /
            ((1 + monthly_rate) ** num_payments - 1)
        )
        
        return round(monthly_payment, 2)
    
    def calculate_loan_details(
        self,
        purchase_price: float,
        loan_type: str = CONVENTIONAL,
        down_payment_pct: Optional[float] = None,
        interest_rate: float = 0.065,  # 6.5% default
        loan_term_years: int = 30,
        property_tax_annual: Optional[float] = None,
        insurance_annual: Optional[float] = None,
        hoa_monthly: float = 0.0,
    ) -> Dict[str, any]:
        """
        Calculate comprehensive loan details for a property.
        
        Returns:
            Dictionary with all loan-related calculations
        """
        loan_params = self.loan_limits.get(loan_type, self.loan_limits[self.CONVENTIONAL])
        
        # Determine down payment
        if down_payment_pct is None:
            down_payment_pct = loan_params.get("default_down_payment_pct", 0.20)
        
        min_down_pct = loan_params.get("min_down_payment_pct", 0.05)
        if down_payment_pct < min_down_pct:
            down_payment_pct = min_down_pct
        
        # Calculate loan amounts
        down_payment = purchase_price * down_payment_pct
        loan_amount = purchase_price - down_payment
        
        # Calculate base monthly payment
        monthly_payment = self.calculate_monthly_payment(
            loan_amount, interest_rate, loan_term_years
        )
        
        # Calculate PMI/MIP if applicable
        pmi_monthly = 0.0
        upfront_costs = 0.0
        
        if loan_type == self.CONVENTIONAL and down_payment_pct < 0.20:
            # PMI typically required when down payment < 20%
            pmi_annual = loan_amount * loan_params.get("pmi_rate_annual", 0.005)
            pmi_monthly = pmi_annual / 12.0
        
        elif loan_type == self.FHA:
            # MIP (Mortgage Insurance Premium)
            mip_annual = loan_amount * loan_params.get("mip_rate_annual", 0.0085)
            pmi_monthly = mip_annual / 12.0
            upfront_mip = loan_amount * loan_params.get("mip_upfront", 0.0175)
            upfront_costs += upfront_mip
        
        elif loan_type == self.VA:
            # VA funding fee
            funding_fee = loan_amount * loan_params.get("funding_fee_pct", 0.0215)
            upfront_costs += funding_fee
        
        elif loan_type == self.USDA:
            # USDA guarantee fees
            guarantee_annual = loan_amount * loan_params.get("guarantee_fee_annual", 0.0035)
            pmi_monthly = guarantee_annual / 12.0
            upfront_guarantee = loan_amount * loan_params.get("guarantee_fee_upfront", 0.01)
            upfront_costs += upfront_guarantee
        
        # Estimate property tax if not provided (typically 1-2% of value)
        if property_tax_annual is None:
            property_tax_annual = purchase_price * 0.015  # 1.5% estimate
        
        property_tax_monthly = property_tax_annual / 12.0
        
        # Estimate insurance if not provided (typically 0.5-1% of value)
        if insurance_annual is None:
            insurance_annual = purchase_price * 0.005  # 0.5% estimate
        
        insurance_monthly = insurance_annual / 12.0
        
        # Total monthly payment (PITI + PMI + HOA)
        total_monthly_payment = (
            monthly_payment +
            property_tax_monthly +
            insurance_monthly +
            pmi_monthly +
            hoa_monthly
        )
        
        # Calculate total interest over life of loan
        total_payments = loan_term_years * 12
        total_interest = (monthly_payment * total_payments) - loan_amount
        
        return {
            "loan_type": loan_type,
            "purchase_price": round(purchase_price, 2),
            "down_payment_pct": round(down_payment_pct * 100, 2),
            "down_payment": round(down_payment, 2),
            "loan_amount": round(loan_amount, 2),
            "interest_rate": round(interest_rate * 100, 3),
            "loan_term_years": loan_term_years,
            "monthly_principal_interest": round(monthly_payment, 2),
            "property_tax_monthly": round(property_tax_monthly, 2),
            "insurance_monthly": round(insurance_monthly, 2),
            "pmi_monthly": round(pmi_monthly, 2),
            "hoa_monthly": round(hoa_monthly, 2),
            "total_monthly_payment": round(total_monthly_payment, 2),
            "upfront_costs": round(upfront_costs, 2),
            "total_interest": round(total_interest, 2),
            "total_cost_of_loan": round(loan_amount + total_interest, 2),
        }
