"""
Property Investment Analysis Engine

Analyzes properties based on investment strategies and loan types.
"""

from typing import Dict, Optional, List
from .loan_calculator import LoanCalculator
from .rentcast_client import RentCastClient


class InvestmentStrategy:
    """Investment strategy configurations."""
    
    # Strategy types
    RENTAL = "rental"  # Buy and hold for rental income
    FLIP = "flip"  # Buy, renovate, and sell quickly
    BRRRR = "brrrr"  # Buy, Rehab, Rent, Refinance, Repeat
    HOUSE_HACK = "house_hack"  # Live in one unit, rent others
    LONG_TERM_APPRECIATION = "long_term_appreciation"  # Focus on appreciation
    
    def __init__(self, strategy_type: str = RENTAL):
        self.strategy_type = strategy_type
        self.criteria = self._get_strategy_criteria(strategy_type)
    
    def _get_strategy_criteria(self, strategy_type: str) -> Dict:
        """Get criteria for different investment strategies."""
        criteria = {
            self.RENTAL: {
                "min_cash_on_cash_return": 0.08,  # 8% minimum
                "min_cap_rate": 0.06,  # 6% minimum
                "min_rent_to_value": 0.005,  # 0.5% monthly rent to value
                "max_vacancy_rate": 0.10,  # 10% max
                "min_rental_yield": 0.10,  # 10% annual
            },
            self.FLIP: {
                "min_profit_margin": 0.20,  # 20% minimum profit
                "max_hold_time_months": 6,  # 6 months max
                "min_after_repair_value": 1.3,  # 130% of purchase
            },
            self.BRRRR: {
                "min_cash_on_cash_return": 0.10,  # 10% minimum
                "min_equity_extraction": 0.70,  # 70% LTV after refinance
                "min_rental_yield": 0.12,  # 12% annual
            },
            self.HOUSE_HACK: {
                "min_rental_coverage": 0.50,  # Rent covers 50% of payment
                "min_cash_flow": 0,  # Break even or positive
            },
            self.LONG_TERM_APPRECIATION: {
                "min_appreciation_rate": 0.03,  # 3% annual
                "location_score_weight": 0.70,  # 70% weight on location
            },
        }
        return criteria.get(strategy_type, criteria[self.RENTAL])


class PropertyAnalyzer:
    """Analyzes properties for investment potential."""
    
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
        maintenance_pct: float = 0.01,  # 1% of value annually
        vacancy_rate: float = 0.05,  # 5% vacancy
        management_fee_pct: float = 0.10,  # 10% if using property manager
    ) -> Dict:
        """
        Perform comprehensive property analysis.
        
        Returns:
            Dictionary with analysis results, scores, and recommendations
        """
        from .url_parser import PropertyURLParser
        
        # Parse URL to get property address
        parser = PropertyURLParser()
        property_info = parser.parse_property_url(property_url)
        
        if not property_info:
            return {
                "error": "Could not parse property URL",
                "suggestions": [
                    "Ensure URL is from Zillow or Realtor.com",
                    "Check URL format is correct"
                ]
            }
        
        address = property_info.get("address")
        
        # Get property data from RentCast
        try:
            # Search for property by address
            properties = await self.rentcast_client.search_properties_by_address(address, limit=1)
            
            if not properties:
                # Try to get valuation and rent estimate by address
                valuation_data = await self.rentcast_client.get_property_valuation(address)
                rent_data = await self.rentcast_client.get_rent_estimate(address)
                
                # Extract ZIP code from address for market stats
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
            
            # Use provided purchase price or estimated value
            if purchase_price is None:
                purchase_price = (
                    property_data.get("price") or
                    property_data.get("estimated_value") or
                    property_data.get("lastSalePrice") or
                    0
                )
            
            if purchase_price == 0:
                return {
                    "error": "Could not determine property price",
                    "suggestions": ["Provide purchase price manually"]
                }
            
            # Get rent estimate if not provided
            if estimated_rent is None:
                estimated_rent = (
                    property_data.get("rent") or
                    property_data.get("estimated_rent") or
                    property_data.get("rentEstimate") or
                    0
                )
            
            # Get market statistics
            market_stats = None
            if zip_code:
                try:
                    market_stats = await self.rentcast_client.get_market_statistics(zip_code)
                except:
                    pass
            
        except Exception as e:
            return {
                "error": f"Error fetching property data: {str(e)}",
                "property_info": property_info
            }
        
        # Calculate loan details
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
        
        # Perform investment analysis
        strategy = InvestmentStrategy(strategy_type)
        analysis = self._perform_investment_analysis(
            purchase_price=purchase_price,
            estimated_rent=estimated_rent or 0,
            loan_details=loan_details,
            strategy=strategy,
            maintenance_pct=maintenance_pct,
            vacancy_rate=vacancy_rate,
            management_fee_pct=management_fee_pct,
        )
        
        # Calculate scores
        scores = self._calculate_scores(analysis, strategy, market_stats)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            analysis, scores, strategy, loan_details
        )
        
        return {
            "property_info": property_info,
            "property_data": property_data,
            "market_statistics": market_stats,
            "loan_details": loan_details,
            "investment_analysis": analysis,
            "scores": scores,
            "recommendations": recommendations,
            "strategy": strategy_type,
        }
    
    def _perform_investment_analysis(
        self,
        purchase_price: float,
        estimated_rent: float,
        loan_details: Dict,
        strategy: InvestmentStrategy,
        maintenance_pct: float,
        vacancy_rate: float,
        management_fee_pct: float,
    ) -> Dict:
        """Perform investment calculations."""
        
        # Monthly expenses
        monthly_payment = loan_details["total_monthly_payment"]
        maintenance_monthly = purchase_price * maintenance_pct / 12.0
        management_monthly = estimated_rent * management_fee_pct if estimated_rent > 0 else 0
        total_monthly_expenses = monthly_payment + maintenance_monthly + management_monthly
        
        # Monthly income (accounting for vacancy)
        effective_rent = estimated_rent * (1 - vacancy_rate)
        monthly_cash_flow = effective_rent - total_monthly_expenses
        
        # Annual metrics
        annual_rent = estimated_rent * 12
        annual_expenses = total_monthly_expenses * 12
        annual_cash_flow = monthly_cash_flow * 12
        
        # Cash on cash return
        total_cash_invested = loan_details["down_payment"] + loan_details.get("upfront_costs", 0)
        cash_on_cash_return = (annual_cash_flow / total_cash_invested) if total_cash_invested > 0 else 0
        
        # Cap rate (NOI / Purchase Price)
        noi = annual_rent - (annual_expenses - loan_details["monthly_principal_interest"] * 12)
        cap_rate = (noi / purchase_price) if purchase_price > 0 else 0
        
        # Gross rental yield
        rental_yield = (annual_rent / purchase_price) if purchase_price > 0 else 0
        
        # Rent to value ratio (monthly)
        rent_to_value = (estimated_rent / purchase_price) if purchase_price > 0 else 0
        
        # Debt service coverage ratio
        dscr = (annual_rent / (loan_details["monthly_principal_interest"] * 12)) if loan_details["monthly_principal_interest"] > 0 else 0
        
        return {
            "purchase_price": purchase_price,
            "estimated_rent_monthly": estimated_rent,
            "effective_rent_monthly": effective_rent,
            "total_monthly_expenses": round(total_monthly_expenses, 2),
            "monthly_cash_flow": round(monthly_cash_flow, 2),
            "annual_rent": round(annual_rent, 2),
            "annual_expenses": round(annual_expenses, 2),
            "annual_cash_flow": round(annual_cash_flow, 2),
            "total_cash_invested": round(total_cash_invested, 2),
            "cash_on_cash_return": round(cash_on_cash_return * 100, 2),
            "cap_rate": round(cap_rate * 100, 2),
            "rental_yield": round(rental_yield * 100, 2),
            "rent_to_value": round(rent_to_value * 100, 3),
            "dscr": round(dscr, 2),
            "vacancy_rate": round(vacancy_rate * 100, 2),
        }
    
    def _calculate_scores(
        self,
        analysis: Dict,
        strategy: InvestmentStrategy,
        market_stats: Optional[Dict] = None
    ) -> Dict:
        """Calculate investment scores based on strategy."""
        scores = {}
        criteria = strategy.criteria
        
        if strategy.strategy_type == InvestmentStrategy.RENTAL:
            # Cash on cash return score
            min_cocr = criteria.get("min_cash_on_cash_return", 0.08)
            cocr_score = min(100, (analysis["cash_on_cash_return"] / 100) / min_cocr * 100)
            
            # Cap rate score
            min_cap = criteria.get("min_cap_rate", 0.06)
            cap_score = min(100, (analysis["cap_rate"] / 100) / min_cap * 100)
            
            # Rental yield score
            min_yield = criteria.get("min_rental_yield", 0.10)
            yield_score = min(100, (analysis["rental_yield"] / 100) / min_yield * 100)
            
            # Overall score (weighted average)
            overall_score = (cocr_score * 0.4 + cap_score * 0.3 + yield_score * 0.3)
            
            scores = {
                "cash_on_cash_score": round(cocr_score, 1),
                "cap_rate_score": round(cap_score, 1),
                "rental_yield_score": round(yield_score, 1),
                "overall_score": round(overall_score, 1),
            }
        
        return scores
    
    def _generate_recommendations(
        self,
        analysis: Dict,
        scores: Dict,
        strategy: InvestmentStrategy,
        loan_details: Dict
    ) -> List[str]:
        """Generate investment recommendations."""
        recommendations = []
        
        if strategy.strategy_type == InvestmentStrategy.RENTAL:
            if analysis["cash_on_cash_return"] < 8:
                recommendations.append(
                    f"⚠️ Low cash-on-cash return ({analysis['cash_on_cash_return']}%). "
                    "Consider negotiating a lower purchase price or finding properties with higher rent potential."
                )
            
            if analysis["monthly_cash_flow"] < 0:
                recommendations.append(
                    "❌ Negative cash flow. This property will cost you money each month. "
                    "Not recommended for rental strategy unless you expect significant appreciation."
                )
            else:
                recommendations.append(
                    f"✅ Positive cash flow of ${analysis['monthly_cash_flow']:.2f}/month. "
                    "This property generates income."
                )
            
            if analysis["dscr"] < 1.2:
                recommendations.append(
                    f"⚠️ Low debt service coverage ratio ({analysis['dscr']:.2f}). "
                    "Lenders typically require DSCR > 1.2 for investment properties."
                )
            
            if loan_details["down_payment_pct"] < 20:
                recommendations.append(
                    f"💡 Consider increasing down payment to 20% to avoid PMI "
                    f"(currently {loan_details['down_payment_pct']}%)."
                )
        
        if scores.get("overall_score", 0) >= 80:
            recommendations.append("🌟 Excellent investment opportunity based on your strategy!")
        elif scores.get("overall_score", 0) >= 60:
            recommendations.append("👍 Good investment opportunity with some room for improvement.")
        else:
            recommendations.append("⚠️ This property may not meet your investment criteria. Review carefully.")
        
        return recommendations
