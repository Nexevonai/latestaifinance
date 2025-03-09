from fastapi import APIRouter, Depends, Query, BackgroundTasks, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.openai_service import OpenAIService
from app.services.perplexity_service import PerplexityService
from app.services.polygon_service import PolygonService
from app.services.financial_datasets_service import FinancialDatasetsService
from app.services.redis_service import RedisService
from app.utils.query_analyzer import is_simple_query, get_fast_path_response
from app.core.config import ENABLE_STREAMING
from typing import Optional, List, Dict, Any
import re
import asyncio
import time
import json
import uuid

router = APIRouter()

# Models for request and response
class SearchRequest(BaseModel):
    query: str
    mode: str = "sonar"  # 'sonar' or 'deep_research'
    session_id: Optional[str] = None
    
class Source(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    
class SearchResponse(BaseModel):
    answer: str
    sources: Optional[List[Source]] = None
    data: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

# Dependency Injection
def get_openai_service():
    return OpenAIService()

def get_perplexity_service():
    return PerplexityService()

def get_polygon_service():
    return PolygonService()

def get_financial_datasets_service():
    return FinancialDatasetsService()

def get_redis_service():
    return RedisService()

def extract_perplexity_content(perplexity_response: Dict[str, Any]) -> str:
    """Extract content from Perplexity response"""
    if "choices" in perplexity_response and len(perplexity_response["choices"]) > 0:
        return perplexity_response["choices"][0]["message"]["content"]
    return ""

def extract_perplexity_sources(perplexity_response: Dict[str, Any]) -> List[Source]:
    """Extract sources from Perplexity response"""
    sources = []
    
    # Check if there are sources in the response
    if "choices" in perplexity_response and len(perplexity_response["choices"]) > 0:
        message = perplexity_response["choices"][0]["message"]
        
        # Check for sources in the context field
        if "context" in message and "documents" in message["context"]:
            for doc in message["context"]["documents"]:
                sources.append(Source(
                    title=doc.get("title", doc.get("url", "Unknown Source")),
                    url=doc.get("url", "")
                ))
        
        # Check for citations in the response
        if "citations" in perplexity_response:
            for citation in perplexity_response["citations"]:
                # Check if this citation is already in sources
                if not any(s.url == citation for s in sources):
                    sources.append(Source(
                        title=citation,
                        url=citation
                    ))
    
    return sources

def extract_sources(api_results: Dict[str, Any]) -> List[Source]:
    """Extract sources from API results"""
    sources = []
    
    # Extract sources from Perplexity response
    for key, value in api_results.items():
        if key in ["perplexity_sonar", "perplexity_deep_research"] and "error" not in value:
            perplexity_sources = extract_perplexity_sources(value)
            sources.extend(perplexity_sources)
    
    # Extract sources from news data
    for key, value in api_results.items():
        if "_news" in key and "results" in value:
            for item in value["results"][:3]:
                sources.append(Source(
                    title=item.get("title", "News Article"),
                    url=item.get("article_url", "")
                ))
    
    return sources

@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    openai_service: OpenAIService = Depends(get_openai_service),
    perplexity_service: PerplexityService = Depends(get_perplexity_service),
    polygon_service: PolygonService = Depends(get_polygon_service),
    financial_datasets_service: FinancialDatasetsService = Depends(get_financial_datasets_service),
    redis_service: RedisService = Depends(get_redis_service)
):
    """
    Search for financial information using multiple APIs with LLM-first approach
    """
    try:
        query = request.query
        mode = request.mode
        
        # Generate or use provided session_id
        session_id = request.session_id or str(uuid.uuid4())
        
        # Add user query to conversation history
        openai_service.add_to_conversation(session_id, "user", query)
        
        # Step 1: Check for cached response
        cached_response = await redis_service.get_query_response(query)
        if cached_response:
            answer = cached_response["answer"]
            # Add the cached response to conversation history
            openai_service.add_to_conversation(session_id, "assistant", answer)
            
            return SearchResponse(
                answer=answer,
                sources=[Source(**source) for source in cached_response.get("sources", [])],
                data=cached_response.get("data"),
                session_id=session_id
            )
        
        # Step 2: Use OpenAI to analyze the query and determine which APIs to call
        api_plan = await openai_service.analyze_query(query, session_id)
        
        # Cache the API plan in the background
        background_tasks.add_task(
            redis_service.set_api_plan,
            query,
            api_plan
        )
        
        # Step 3: Execute API calls in parallel based on the plan
        api_results = {}
        tasks = []
        task_keys = []
        
        # Handle Deep Research mode explicitly set by user
        if mode == "deep_research":
            api_plan["call_perplexity_deep_research"] = True
        
        # Perplexity API calls
        if mode == "sonar" or api_plan.get("call_perplexity_sonar", False):
            tasks.append(perplexity_service.sonar_search(query))
            task_keys.append("perplexity_sonar")
        
        if mode == "deep_research" or api_plan.get("call_perplexity_deep_research", False):
            tasks.append(perplexity_service.deep_research(query))
            task_keys.append("perplexity_deep_research")
        
        # Extract tickers from API plan
        tickers = api_plan.get("tickers", [])
        
        # Stock-specific API calls for each ticker
        for ticker in tickers:
            # Normalize ticker to uppercase
            ticker = ticker.upper()
            
            if api_plan.get("need_stock_price", False):
                tasks.append(polygon_service.get_stock_price(ticker))
                task_keys.append(f"{ticker}_price")
            
            if api_plan.get("need_financials", False):
                tasks.append(financial_datasets_service.get_financial_statements(ticker))
                task_keys.append(f"{ticker}_financials")
            
            if api_plan.get("need_insider_trades", False):
                tasks.append(polygon_service.get_insider_trades(ticker))
                task_keys.append(f"{ticker}_insider_trades")
                
            if api_plan.get("need_sec_filings", False):
                tasks.append(financial_datasets_service.get_sec_filings(ticker))
                task_keys.append(f"{ticker}_sec_filings")
            
            # Always get news for tickers if we're looking for market insights
            if api_plan.get("call_perplexity_sonar", False):
                tasks.append(polygon_service.get_company_news(ticker))
                task_keys.append(f"{ticker}_news")
        
        # Execute all API calls in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Error in API call {task_keys[i]}: {result}")
                    api_results[task_keys[i]] = {"error": str(result)}
                else:
                    api_results[task_keys[i]] = result
        
        # Step 4: Generate the final response using OpenAI
        final_response = await openai_service.generate_financial_insight(query, api_results, session_id)
        
        # Extract sources
        sources = extract_sources(api_results)
        
        # Cache the response in the background
        background_tasks.add_task(
            redis_service.set_query_response,
            query,
            {"answer": final_response, "sources": [s.__dict__ for s in sources], "data": api_results}
        )
        
        return SearchResponse(
            answer=final_response,
            sources=sources,
            data=api_results,
            session_id=session_id
        )
    except Exception as e:
        print(f"Error in search: {e}")
        return SearchResponse(
            answer=f"An error occurred while processing your request: {str(e)}",
            sources=[],
            session_id=request.session_id or str(uuid.uuid4())
        )

@router.post("/search/stream")
async def stream_search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    openai_service: OpenAIService = Depends(get_openai_service),
    perplexity_service: PerplexityService = Depends(get_perplexity_service),
    polygon_service: PolygonService = Depends(get_polygon_service),
    financial_datasets_service: FinancialDatasetsService = Depends(get_financial_datasets_service),
    redis_service: RedisService = Depends(get_redis_service)
):
    """
    Stream search results for financial information
    """
    if not ENABLE_STREAMING:
        # Fallback to regular search if streaming is disabled
        response = await search(
            request, 
            background_tasks,
            openai_service,
            perplexity_service,
            polygon_service,
            financial_datasets_service,
            redis_service
        )
        return response
    
    async def stream_generator():
        try:
            query = request.query
            mode = request.mode
            
            # Generate or use provided session_id
            session_id = request.session_id or str(uuid.uuid4())
            
            # Add user query to conversation history
            openai_service.add_to_conversation(session_id, "user", query)
            
            # Initial message
            yield json.dumps({
                "type": "status", 
                "content": "Processing your query...",
                "session_id": session_id
            }) + "\n"
            
            # Step 1: Check for cached response
            cached_response = await redis_service.get_query_response(query)
            if cached_response:
                answer = cached_response["answer"]
                # Add the cached response to conversation history
                openai_service.add_to_conversation(session_id, "assistant", answer)
                
                yield json.dumps({
                    "type": "result", 
                    "content": answer,
                    "sources": cached_response.get("sources", []),
                    "session_id": session_id
                }) + "\n"
                return
            
            # Step 2: Use OpenAI to analyze the query
            yield json.dumps({"type": "status", "content": "Analyzing your query..."}) + "\n"
            
            api_plan = await openai_service.analyze_query(query, session_id)
            
            # Cache the API plan in the background
            background_tasks.add_task(
                redis_service.set_api_plan,
                query,
                api_plan
            )
            
            # Step 3: Execute API calls in parallel based on the plan
            api_results = {}
            tasks = []
            task_keys = []
            
            # Handle Deep Research mode explicitly set by user
            if mode == "deep_research":
                api_plan["call_perplexity_deep_research"] = True
                yield json.dumps({"type": "status", "content": "Deep Research mode activated. This may take longer..."}) + "\n"
            
            yield json.dumps({"type": "status", "content": "Gathering financial data..."}) + "\n"
            
            # Perplexity API calls
            if mode == "sonar" or api_plan.get("call_perplexity_sonar", False):
                yield json.dumps({"type": "status", "content": "Searching for latest market information..."}) + "\n"
                tasks.append(perplexity_service.sonar_search(query))
                task_keys.append("perplexity_sonar")
            
            if mode == "deep_research" or api_plan.get("call_perplexity_deep_research", False):
                yield json.dumps({"type": "status", "content": "Conducting deep financial research..."}) + "\n"
                tasks.append(perplexity_service.deep_research(query))
                task_keys.append("perplexity_deep_research")
            
            # Extract tickers from API plan
            tickers = api_plan.get("tickers", [])
            
            # Stock-specific API calls for each ticker
            for ticker in tickers:
                # Normalize ticker to uppercase
                ticker = ticker.upper()
                
                if api_plan.get("need_stock_price", False):
                    yield json.dumps({"type": "status", "content": f"Fetching stock price for {ticker}..."}) + "\n"
                    tasks.append(polygon_service.get_stock_price(ticker))
                    task_keys.append(f"{ticker}_price")
                
                if api_plan.get("need_financials", False):
                    yield json.dumps({"type": "status", "content": f"Retrieving financial statements for {ticker}..."}) + "\n"
                    tasks.append(financial_datasets_service.get_financial_statements(ticker))
                    task_keys.append(f"{ticker}_financials")
                
                if api_plan.get("need_insider_trades", False):
                    yield json.dumps({"type": "status", "content": f"Checking insider trades for {ticker}..."}) + "\n"
                    tasks.append(financial_datasets_service.get_insider_trades(ticker))
                    task_keys.append(f"{ticker}_insider_trades")
                    
                if api_plan.get("need_sec_filings", False):
                    yield json.dumps({"type": "status", "content": f"Retrieving SEC filings for {ticker}..."}) + "\n"
                    tasks.append(financial_datasets_service.get_sec_filings(ticker))
                    task_keys.append(f"{ticker}_sec_filings")
                
                # Always get news for tickers if we're looking for market insights
                if api_plan.get("call_perplexity_sonar", False):
                    yield json.dumps({"type": "status", "content": f"Fetching latest news for {ticker}..."}) + "\n"
                    tasks.append(polygon_service.get_company_news(ticker))
                    task_keys.append(f"{ticker}_news")
            
            # Execute all API calls in parallel
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        print(f"Error in API call {task_keys[i]}: {result}")
                        api_results[task_keys[i]] = {"error": str(result)}
                    else:
                        api_results[task_keys[i]] = result
            
            # Step 4: Generate the final response using OpenAI
            yield json.dumps({"type": "status", "content": "Analyzing data and generating insights..."}) + "\n"
            
            final_response = await openai_service.generate_financial_insight(query, api_results, session_id)
            
            # Extract sources
            sources = extract_sources(api_results)
            sources_list = [{"title": s.title, "url": s.url} for s in sources]
            
            # Cache the response in the background
            background_tasks.add_task(
                redis_service.set_query_response,
                query,
                {"answer": final_response, "sources": sources_list, "data": api_results}
            )
            
            # Return final result
            yield json.dumps({
                "type": "result", 
                "content": final_response,
                "sources": sources_list,
                "session_id": session_id
            }) + "\n"
            
        except Exception as e:
            print(f"Error in stream_search: {e}")
            yield json.dumps({
                "type": "error",
                "content": f"An error occurred while processing your request: {str(e)}",
                "session_id": request.session_id or str(uuid.uuid4())
            }) + "\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="application/x-ndjson"
    ) 