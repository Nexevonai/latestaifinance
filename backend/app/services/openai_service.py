from openai import OpenAI
from app.core.config import OPENAI_API_KEY
import json
import re
from typing import Dict, List, Any, Optional

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = "gpt-4-turbo"
        self.conversation_history = {}  # Store conversation history by session_id
    
    async def generate_response(self, messages, temperature=0.7, max_tokens=1500):
        """
        Generate a response using OpenAI's GPT model
        
        Args:
            messages (list): List of message dictionaries
            temperature (float): Controls randomness
            max_tokens (int): Maximum tokens to generate
            
        Returns:
            str: Generated response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return f"Error: {str(e)}"
    
    def get_conversation_history(self, session_id: str, max_messages: int = 10) -> List[Dict[str, str]]:
        """
        Get conversation history for a session
        
        Args:
            session_id (str): Unique session identifier
            max_messages (int): Maximum number of messages to include
            
        Returns:
            List[Dict[str, str]]: List of message dictionaries
        """
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        # Return the most recent messages up to max_messages
        return self.conversation_history[session_id][-max_messages:]
    
    def add_to_conversation(self, session_id: str, role: str, content: str):
        """
        Add a message to the conversation history
        
        Args:
            session_id (str): Unique session identifier
            role (str): Message role ('user', 'assistant', or 'system')
            content (str): Message content
        """
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append({
            "role": role,
            "content": content
        })
        
        # Limit history to last 20 messages to prevent token overflow
        if len(self.conversation_history[session_id]) > 20:
            self.conversation_history[session_id] = self.conversation_history[session_id][-20:]
    
    async def analyze_query(self, query: str, session_id: str = "default"):
        """
        Analyze a financial query to determine which APIs to call
        
        Args:
            query (str): User's financial query
            session_id (str): Unique session identifier for conversation history
            
        Returns:
            dict: API selection plan
        """
        # Get conversation history
        history = self.get_conversation_history(session_id)
        
        # Create the system prompt
        system_prompt = """
        You are an AI financial assistant that routes queries to the appropriate data sources.
        
        Given the user's query and conversation history, determine which financial APIs should be called to provide the best answer.
        
        Follow these routing rules:
        - Stock prices & trading data → Polygon.io
        - Latest news & market insights → Perplexity Sonar
        - Financial statements & SEC filings → FinancialDatasets.ai
        - Deep research → Perplexity Deep Research (ONLY if explicitly requested by user)
        
        Return your decision in structured JSON format:

        {
          "call_perplexity_sonar": true/false,  # For real-time news & market trends
          "call_perplexity_deep_research": true/false,  # For deep financial analysis (only if explicitly requested)
          "need_stock_price": true/false,  # For current/historical stock prices
          "need_financials": true/false,  # For company financial reports
          "need_insider_trades": true/false,  # For insider trading data
          "need_sec_filings": true/false,  # For SEC documents & filings
          "tickers": ["AAPL", "TSLA", etc.],  # Extracted stock tickers or company names
          "reasoning": "Explain why these APIs were selected."
        }

        Be precise and ensure no unnecessary API calls are made. Extract both ticker symbols AND company names.
        """
        
        # Build messages including conversation history
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history
        for msg in history:
            messages.append(msg)
        
        # Add the current query
        messages.append({"role": "user", "content": query})
        
        # Get response from OpenAI
        response = await self.generate_response(messages, temperature=0.3)
        
        # Extract JSON from response
        try:
            # Try to find JSON block in markdown format
            json_match = re.search(r'```(?:json)?\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                api_plan = json.loads(json_match.group(1))
            else:
                # Try to find JSON object directly
                json_match = re.search(r'({.*})', response, re.DOTALL)
                if json_match:
                    api_plan = json.loads(json_match.group(1))
                else:
                    # Fallback to default plan
                    api_plan = {
                        "call_perplexity_sonar": True,
                        "call_perplexity_deep_research": False,
                        "need_stock_price": False,
                        "need_financials": False,
                        "need_insider_trades": False,
                        "need_sec_filings": False,
                        "tickers": [],
                        "reasoning": "Failed to parse API plan, using default."
                    }
            
            # Ensure all required fields are present
            required_fields = [
                "call_perplexity_sonar", "call_perplexity_deep_research",
                "need_stock_price", "need_financials", "need_insider_trades",
                "need_sec_filings", "tickers", "reasoning"
            ]
            
            for field in required_fields:
                if field not in api_plan:
                    if field == "tickers":
                        api_plan[field] = []
                    elif field == "reasoning":
                        api_plan[field] = "No reasoning provided."
                    else:
                        api_plan[field] = False
            
            return api_plan
            
        except Exception as e:
            print(f"Error parsing API plan: {e}")
            # Return default plan on error
            return {
                "call_perplexity_sonar": True,
                "call_perplexity_deep_research": False,
                "need_stock_price": False,
                "need_financials": False,
                "need_insider_trades": False,
                "need_sec_filings": False,
                "tickers": [],
                "reasoning": f"Error parsing API plan: {str(e)}"
            }
    
    async def generate_financial_insight(self, query: str, data: Dict[str, Any], session_id: str = "default"):
        """
        Generate a comprehensive financial insight based on collected data
        
        Args:
            query (str): User's financial query
            data (dict): Collected data from various APIs
            session_id (str): Unique session identifier for conversation history
            
        Returns:
            str: Generated financial insight
        """
        # Get conversation history
        history = self.get_conversation_history(session_id)
        
        system_prompt = """
        You are a specialized financial assistant that provides accurate information about stocks, 
        financial markets, and company data. Use the provided financial data to give informative,
        concise, and accurate responses. If you don't have the data to answer a question, say so clearly.
        When providing financial analysis, include relevant metrics and comparisons when available.
        
        You have access to the following data sources:
        1. Perplexity Sonar - For real-time news and market insights
        2. Perplexity Deep Research - For in-depth financial analysis
        3. Polygon.io - For stock prices, charts, and technical data
        4. FinancialDatasets.ai - For company filings, insider trades, and SEC filings
        
        Format your response in a clear, structured way. Use markdown formatting for better readability.
        Include relevant numbers, percentages, and dates when available.
        Always cite your sources at the end of your response.
        
        Be conversational and suggest relevant follow-up questions based on the data.
        """
        
        # Build messages including conversation history
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history
        for msg in history:
            messages.append(msg)
        
        # Add the current query
        messages.append({"role": "user", "content": query})
        
        # Format the data in a readable way
        formatted_data = self._format_data_for_prompt(data)
        data_message = f"Here is the financial data related to your query:\n\n{formatted_data}"
        messages.append({"role": "system", "content": data_message})
        
        # Get response from OpenAI
        response = await self.generate_response(messages, temperature=0.5, max_tokens=2000)
        
        # Add the response to conversation history
        self.add_to_conversation(session_id, "assistant", response)
        
        return response
    
    def _format_data_for_prompt(self, data):
        """Format the data in a readable way for the prompt"""
        formatted_text = ""
        
        # Add Perplexity content if available
        for key, value in data.items():
            if key in ["perplexity_sonar", "perplexity_deep_research"] and "error" not in value:
                if "choices" in value and len(value["choices"]) > 0:
                    content = value["choices"][0]["message"]["content"]
                    source_type = "Perplexity Sonar" if key == "perplexity_sonar" else "Perplexity Deep Research"
                    formatted_text += f"## {source_type} Results\n"
                    formatted_text += content + "\n\n"
                    
                    # Add citations if available
                    if "citations" in value:
                        formatted_text += "### Sources:\n"
                        for i, citation in enumerate(value["citations"]):
                            formatted_text += f"[{i+1}] {citation}\n"
                        formatted_text += "\n"
        
        # Add stock price data
        for key, value in data.items():
            if "_price" in key and "error" not in value:
                ticker = key.split("_")[0]
                formatted_text += f"## {ticker} Stock Price\n"
                
                if "results" in value and value["results"]:
                    result = value["results"][0]
                    formatted_text += f"- Close Price: ${result.get('c', 'N/A')}\n"
                    formatted_text += f"- Open Price: ${result.get('o', 'N/A')}\n"
                    formatted_text += f"- High: ${result.get('h', 'N/A')}\n"
                    formatted_text += f"- Low: ${result.get('l', 'N/A')}\n"
                    formatted_text += f"- Volume: {result.get('v', 'N/A')}\n\n"
        
        # Add news data
        for key, value in data.items():
            if "_news" in key and "error" not in value:
                ticker = key.split("_")[0]
                formatted_text += f"## {ticker} Recent News\n"
                
                if "results" in value:
                    for i, news in enumerate(value["results"][:3]):
                        formatted_text += f"- {news.get('title', 'No title')}\n"
                        formatted_text += f"  Published: {news.get('published_utc', 'N/A')}\n"
                        if news.get('description'):
                            formatted_text += f"  Summary: {news.get('description')[:150]}...\n\n"
        
        # Add financial data - UPDATED to include actual financial data
        for key, value in data.items():
            if "_financials" in key and "error" not in value:
                ticker = key.split("_")[0]
                formatted_text += f"## {ticker} Financial Statements\n"
                
                if "financials" in value:
                    financials = value["financials"]
                    
                    # Income Statements
                    if "income_statements" in financials and financials["income_statements"]:
                        formatted_text += f"### Income Statements\n"
                        for statement in financials["income_statements"][:2]:  # Show last 2 years
                            fiscal_year = statement.get("fiscal_year", "N/A")
                            formatted_text += f"**Fiscal Year {fiscal_year}**\n"
                            
                            # Add key metrics from income statement
                            key_metrics = [
                                "total_revenue", "gross_profit", "operating_income", 
                                "net_income", "earnings_per_share"
                            ]
                            
                            for metric in key_metrics:
                                if metric in statement:
                                    formatted_name = metric.replace("_", " ").title()
                                    formatted_text += f"- {formatted_name}: ${statement[metric]:,} million\n"
                            formatted_text += "\n"
                    
                    # Balance Sheets
                    if "balance_sheets" in financials and financials["balance_sheets"]:
                        formatted_text += f"### Balance Sheets\n"
                        for statement in financials["balance_sheets"][:2]:  # Show last 2 years
                            fiscal_year = statement.get("fiscal_year", "N/A")
                            formatted_text += f"**Fiscal Year {fiscal_year}**\n"
                            
                            # Add key metrics from balance sheet
                            key_metrics = [
                                "total_assets", "total_liabilities", "total_equity",
                                "cash_and_equivalents", "total_debt"
                            ]
                            
                            for metric in key_metrics:
                                if metric in statement:
                                    formatted_name = metric.replace("_", " ").title()
                                    formatted_text += f"- {formatted_name}: ${statement[metric]:,} million\n"
                            formatted_text += "\n"
                    
                    # Cash Flow Statements
                    if "cash_flow_statements" in financials and financials["cash_flow_statements"]:
                        formatted_text += f"### Cash Flow Statements\n"
                        for statement in financials["cash_flow_statements"][:2]:  # Show last 2 years
                            fiscal_year = statement.get("fiscal_year", "N/A")
                            formatted_text += f"**Fiscal Year {fiscal_year}**\n"
                            
                            # Add key metrics from cash flow statement
                            key_metrics = [
                                "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
                                "free_cash_flow", "capital_expenditures"
                            ]
                            
                            for metric in key_metrics:
                                if metric in statement:
                                    formatted_name = metric.replace("_", " ").title()
                                    formatted_text += f"- {formatted_name}: ${statement[metric]:,} million\n"
                            formatted_text += "\n"
                else:
                    formatted_text += f"No detailed financial data available for {ticker}\n\n"
        
        # Add SEC filings - UPDATED to include actual SEC filings data
        for key, value in data.items():
            if "_sec_filings" in key and "error" not in value:
                ticker = key.split("_")[0]
                formatted_text += f"## {ticker} SEC Filings\n"
                
                if "filings" in value and value["filings"]:
                    for i, filing in enumerate(value["filings"][:3]):  # Show top 3 filings
                        formatted_text += f"- Form {filing.get('form_type', 'N/A')}: Filed on {filing.get('filing_date', 'N/A')}\n"
                        if filing.get('description'):
                            formatted_text += f"  Description: {filing.get('description')}\n"
                        if filing.get('url'):
                            formatted_text += f"  URL: {filing.get('url')}\n"
                        formatted_text += "\n"
                else:
                    formatted_text += f"No SEC filings data available for {ticker}\n\n"
        
        # Add insider trades - UPDATED to include actual insider trades data
        for key, value in data.items():
            if "_insider_trades" in key and "error" not in value:
                ticker = key.split("_")[0]
                formatted_text += f"## {ticker} Insider Trades\n"
                
                if "results" in value and value["results"]:
                    formatted_text += "Recent insider trading activity:\n\n"
                    for i, trade in enumerate(value["results"][:5]):  # Show top 5 trades
                        # Extract all available data with fallbacks
                        name = trade.get('name', trade.get('insider_name', 'Unknown'))
                        title = trade.get('title', trade.get('insider_title', ''))
                        shares = trade.get('shares', trade.get('share_count', 'N/A'))
                        price = trade.get('price', trade.get('share_price', 'N/A'))
                        trade_date = trade.get('trade_date', trade.get('transaction_date', 'N/A'))
                        transaction_type = trade.get('transaction_type', trade.get('transaction_code', ''))
                        
                        # Format the trade information
                        formatted_text += f"- **{name}**"
                        if title:
                            formatted_text += f" ({title})"
                        formatted_text += f": {transaction_type} {shares} shares"
                        if price:
                            formatted_text += f" at ${price}"
                        formatted_text += f" on {trade_date}\n"
                        
                        # Add additional details if available
                        if trade.get('shares_owned_before') and trade.get('shares_owned_after'):
                            before = trade.get('shares_owned_before')
                            after = trade.get('shares_owned_after')
                            formatted_text += f"  Shares owned: {before} → {after}\n"
                    formatted_text += "\n"
                else:
                    formatted_text += f"No insider trade data available for {ticker}\n\n"
        
        return formatted_text 