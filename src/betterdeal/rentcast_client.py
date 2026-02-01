"""
RentCast API Client

Reusable client for making RentCast API calls.
"""

import os
import httpx
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

RENTCAST_API_KEY = os.getenv("RENTCAST_API_KEY")
if not RENTCAST_API_KEY:
    raise ValueError("RENTCAST_API_KEY environment variable is required")


class RentCastClient:
    """Client for interacting with RentCast API."""
    
    def __init__(self):
        self.base_url = "https://api.rentcast.io/v1"
        self.headers = {"X-Api-Key": RENTCAST_API_KEY}
        self.timeout = 30.0
    
    async def get_http_client(self):
        """Get or create HTTP client with proper headers."""
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=self.timeout
        )
    
    async def get_property_valuation(
        self,
        address: str,
        property_type: Optional[str] = None,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        square_footage: Optional[int] = None,
        comp_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get property value estimate (AVM)."""
        async with await self.get_http_client() as client:
            params: Dict[str, Any] = {"address": address}
            if property_type is not None:
                params["propertyType"] = property_type
            if bedrooms is not None:
                params["bedrooms"] = bedrooms
            if bathrooms is not None:
                params["bathrooms"] = bathrooms
            if square_footage is not None:
                params["squareFootage"] = square_footage
            if comp_count is not None:
                params["compCount"] = comp_count
            
            response = await client.get("/avm/value", params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_rent_estimate(
        self,
        address: str,
        property_type: Optional[str] = None,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        square_footage: Optional[int] = None,
        comp_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get long-term rent estimate."""
        async with await self.get_http_client() as client:
            params: Dict[str, Any] = {"address": address}
            if property_type is not None:
                params["propertyType"] = property_type
            if bedrooms is not None:
                params["bedrooms"] = bedrooms
            if bathrooms is not None:
                params["bathrooms"] = bathrooms
            if square_footage is not None:
                params["squareFootage"] = square_footage
            if comp_count is not None:
                params["compCount"] = comp_count
            
            response = await client.get("/avm/rent/long-term", params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_market_statistics(
        self,
        zip_code: str,
        property_type: Optional[str] = None,
        bedrooms: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get market statistics for a ZIP code."""
        async with await self.get_http_client() as client:
            params = {
                "zipCode": zip_code,
                "propertyType": property_type,
                "bedrooms": bedrooms
            }
            params = {k: v for k, v in params.items() if v is not None}
            
            response = await client.get("/markets", params=params)
            response.raise_for_status()
            return response.json()
    
    async def search_properties_by_address(
        self,
        address: str,
        limit: Optional[int] = 10
    ) -> List[Dict[str, Any]]:
        """Search for properties by address."""
        async with await self.get_http_client() as client:
            params = {"address": address}
            if limit:
                params["limit"] = limit

            response = await client.get("/properties", params=params)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'properties' in data:
                return data['properties']
            else:
                return [data] if data else []

    async def get_sale_listings(
        self,
        zip_code: str,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        sqft_min: Optional[int] = None,
        sqft_max: Optional[int] = None,
        property_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get active sale listings for comparable analysis."""
        async with await self.get_http_client() as client:
            params: Dict[str, Any] = {"zipCode": zip_code, "limit": limit}
            if bedrooms is not None:
                params["bedrooms"] = bedrooms
            if bathrooms is not None:
                params["bathrooms"] = bathrooms
            if sqft_min is not None:
                params["sqftMin"] = sqft_min
            if sqft_max is not None:
                params["sqftMax"] = sqft_max
            if property_type is not None:
                params["propertyType"] = property_type

            response = await client.get("/listings/sale", params=params)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else []

    async def get_rental_listings(
        self,
        zip_code: str,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        sqft_min: Optional[int] = None,
        sqft_max: Optional[int] = None,
        property_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get active rental listings for comparable analysis."""
        async with await self.get_http_client() as client:
            params: Dict[str, Any] = {"zipCode": zip_code, "limit": limit}
            if bedrooms is not None:
                params["bedrooms"] = bedrooms
            if bathrooms is not None:
                params["bathrooms"] = bathrooms
            if sqft_min is not None:
                params["sqftMin"] = sqft_min
            if sqft_max is not None:
                params["sqftMax"] = sqft_max
            if property_type is not None:
                params["propertyType"] = property_type

            response = await client.get("/listings/rental", params=params)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else []
