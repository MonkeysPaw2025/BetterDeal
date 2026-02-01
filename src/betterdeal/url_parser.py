"""
URL Parser for Zillow and Realtor.com

Extracts property information from listing URLs.
"""

import re
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs
import httpx


class PropertyURLParser:
    """Parser for extracting property data from listing URLs."""
    
    @staticmethod
    def parse_zillow_url(url: str) -> Optional[Dict[str, str]]:
        """
        Parse Zillow URL to extract property information.
        
        Zillow URLs typically look like:
        - https://www.zillow.com/homedetails/123-Main-St-City-ST-12345/12345678_zpid/
        - https://www.zillow.com/homes/123-Main-St-City-ST-12345_rb/
        """
        try:
            parsed = urlparse(url)
            
            # Extract address from path
            # Pattern: /homedetails/ADDRESS/ID_zpid/ or /homes/ADDRESS_rb/
            path_match = re.search(r'/(?:homedetails|homes)/([^/]+)', parsed.path)
            if path_match:
                address_slug = path_match.group(1)
                # Convert slug to readable address (replace hyphens with spaces)
                address = address_slug.replace('-', ' ').replace('_rb', '').replace('_zpid', '')
                
                # Extract ZPID if available
                zpid_match = re.search(r'/(\d+)_zpid', parsed.path)
                zpid = zpid_match.group(1) if zpid_match else None
                
                return {
                    "address": address,
                    "zpid": zpid,
                    "source": "zillow",
                    "url": url
                }
        except Exception as e:
            print(f"Error parsing Zillow URL: {e}")
        
        return None
    
    @staticmethod
    def parse_realtor_url(url: str) -> Optional[Dict[str, str]]:
        """
        Parse Realtor.com URL to extract property information.
        
        Realtor.com URLs typically look like:
        - https://www.realtor.com/realestateandhomes-detail/123-Main-St_City_ST_12345_M12345_12345
        """
        try:
            parsed = urlparse(url)
            
            # Extract address from path
            # Pattern: /realestateandhomes-detail/ADDRESS_ID
            path_match = re.search(r'/realestateandhomes-detail/([^/]+)', parsed.path)
            if path_match:
                address_slug = path_match.group(1)
                # Remove trailing ID pattern (M12345_12345)
                address_part = re.sub(r'_M\d+_\d+$', '', address_slug)
                # Convert slug to readable address
                address = address_part.replace('_', ' ').replace('-', ' ')
                
                # Extract listing ID if available
                id_match = re.search(r'_M(\d+)_(\d+)$', address_slug)
                listing_id = f"M{id_match.group(1)}_{id_match.group(2)}" if id_match else None
                
                return {
                    "address": address,
                    "listing_id": listing_id,
                    "source": "realtor",
                    "url": url
                }
        except Exception as e:
            print(f"Error parsing Realtor URL: {e}")
        
        return None
    
    @staticmethod
    async def fetch_property_details_from_url(url: str) -> Optional[Dict[str, any]]:
        """
        Attempt to fetch property details by scraping the page.
        This is a fallback if URL parsing doesn't provide enough info.
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                if response.status_code == 200:
                    html = response.text
                    
                    # Try to extract address from meta tags or structured data
                    # This is a basic implementation - could be enhanced
                    address_patterns = [
                        r'"streetAddress":"([^"]+)"',
                        r'"address":"([^"]+)"',
                        r'property="streetAddress"[^>]*>([^<]+)',
                    ]
                    
                    for pattern in address_patterns:
                        match = re.search(pattern, html)
                        if match:
                            return {"address": match.group(1)}
        except Exception as e:
            print(f"Error fetching property details: {e}")
        
        return None
    
    @staticmethod
    def parse_property_url(url: str) -> Optional[Dict[str, str]]:
        """
        Parse a property URL (Zillow or Realtor.com).
        Returns property information if successful.
        """
        if "zillow.com" in url.lower():
            return PropertyURLParser.parse_zillow_url(url)
        elif "realtor.com" in url.lower():
            return PropertyURLParser.parse_realtor_url(url)
        else:
            return None
