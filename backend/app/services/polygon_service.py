import httpx
from app.core.config import POLYGON_API_KEY, POLYGON_API_URL

class PolygonService:
    def __init__(self):
        self.api_key = POLYGON_API_KEY
        self.base_url = POLYGON_API_URL
        
    async def get_stock_price(self, ticker):
        """
        Get the current stock price for a ticker
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Stock price data
        """
        endpoint = f"/v2/aggs/ticker/{ticker}/prev"
        params = {
            "apiKey": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}{endpoint}", params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"HTTP error occurred: {e}")
                return {"error": str(e)}
            except Exception as e:
                print(f"An error occurred: {e}")
                return {"error": str(e)}
    
    async def get_company_news(self, ticker, limit=5):
        """
        Get recent news for a company
        
        Args:
            ticker (str): Stock ticker symbol
            limit (int): Maximum number of news items to return
            
        Returns:
            dict: Company news data
        """
        endpoint = f"/v2/reference/news"
        params = {
            "ticker": ticker,
            "limit": limit,
            "apiKey": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}{endpoint}", params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"HTTP error occurred: {e}")
                return {"error": str(e)}
            except Exception as e:
                print(f"An error occurred: {e}")
                return {"error": str(e)}
    
    async def get_historical_prices(self, ticker, from_date, to_date):
        """
        Get historical stock prices for a ticker
        
        Args:
            ticker (str): Stock ticker symbol
            from_date (str): Start date (YYYY-MM-DD)
            to_date (str): End date (YYYY-MM-DD)
            
        Returns:
            dict: Historical price data
        """
        endpoint = f"/v2/aggs/ticker/{ticker}/range/1/day/{from_date}/{to_date}"
        params = {
            "apiKey": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}{endpoint}", params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"HTTP error occurred: {e}")
                return {"error": str(e)}
            except Exception as e:
                print(f"An error occurred: {e}")
                return {"error": str(e)}
                
    async def get_financials(self, ticker, limit=4):
        """
        Get financial reports for a company
        
        Args:
            ticker (str): Stock ticker symbol
            limit (int): Maximum number of reports to return
            
        Returns:
            dict: Financial report data
        """
        endpoint = f"/vX/reference/financials"
        params = {
            "ticker": ticker,
            "limit": limit,
            "apiKey": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}{endpoint}", params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"HTTP error occurred: {e}")
                return {"error": str(e)}
            except Exception as e:
                print(f"An error occurred: {e}")
                return {"error": str(e)}
                
    async def get_insider_trades(self, ticker, limit=10):
        """
        Get insider trades for a company
        
        Args:
            ticker (str): Stock ticker symbol
            limit (int): Maximum number of trades to return
            
        Returns:
            dict: Insider trade data
        """
        # Polygon.io endpoint for insider transactions
        endpoint = f"/v2/reference/insiders"
        params = {
            "ticker": ticker,
            "limit": limit,
            "apiKey": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}{endpoint}", params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"HTTP error occurred: {e}")
                return {"error": str(e)}
            except Exception as e:
                print(f"An error occurred: {e}")
                return {"error": str(e)} 