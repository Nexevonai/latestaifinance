# AI Financial Search Engine

A powerful financial search engine that integrates multiple APIs with OpenAI's LLM to provide seamless and highly relevant financial insights.

## Features

- **LLM-First API Selection**: Intelligent API selection based on query analysis
- **Fast-Path for Simple Queries**: Bypasses LLM for common financial questions
- **API Response Caching**: Reduces costs and improves response times
- **Streaming Responses**: Real-time updates as data is gathered and processed
- **Multiple Financial Data Sources**:
  - **Perplexity Sonar**: Real-time news and market insights
  - **Perplexity Deep Research**: In-depth financial analysis
  - **Polygon.io**: Stock prices, charts, and technical data
  - **FinancialDatasets.ai**: Company filings, insider trades, and SEC filings

## Tech Stack

### Frontend
- **Next.js**: React framework with TypeScript
- **Tailwind CSS**: Utility-first CSS framework
- **Streaming API Consumption**: Real-time data processing

### Backend
- **FastAPI**: Modern, high-performance Python web framework
- **OpenAI API**: For LLM-based query analysis and response generation
- **Redis**: For caching API plans and responses
- **Async Processing**: Parallel API calls for faster responses

## Architecture

The system uses an enhanced LLM-first approach:

1. **Query Analysis**:
   - Simple queries bypass the LLM using pattern matching
   - Complex queries are analyzed by the LLM to determine which APIs to call

2. **API Selection**:
   - The LLM decides which APIs are needed based on the query
   - Only necessary APIs are called to minimize costs

3. **Parallel Execution**:
   - API calls are executed in parallel using asyncio
   - Results are collected and formatted for the LLM

4. **Response Generation**:
   - The LLM generates a comprehensive response based on all data
   - Results are streamed to the user in real-time

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- Redis (optional, for caching)
- API keys for:
  - OpenAI
  - Polygon.io
  - Perplexity
  - FinancialDatasets.ai

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd financial-search-engine
```

2. **Set up the backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Set up the frontend**:
```bash
cd ../frontend
npm install
```

### Running the Application

1. **Start Redis** (optional, for caching):
```bash
redis-server
```

2. **Start the backend**:
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python run.py
```

3. **Start the frontend**:
```bash
cd frontend
npm run dev
```

4. **Open your browser** and navigate to `http://localhost:3000`

## Usage Examples

### Simple Queries (Fast-Path)
- "What is the current price of AAPL?"
- "Show me the latest news for TSLA"
- "What are the recent insider trades for NVDA?"

### Complex Queries (LLM-First)
- "Compare Tesla and Ford in terms of financial performance and stock growth"
- "Find me stocks similar to Tesla, then compare their profit margins"
- "What are the biggest challenges in the semiconductor industry today?"
- "Is the current market sentiment bullish or bearish on NVDA?"

## Configuration Options

The system can be configured through environment variables:

- `ENABLE_FAST_PATH`: Enable/disable fast-path for simple queries (default: true)
- `ENABLE_CACHING`: Enable/disable Redis caching (default: true)
- `ENABLE_STREAMING`: Enable/disable streaming responses (default: true)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- OpenAI for their powerful language models
- Perplexity for their AI-powered search technology
- Polygon.io for their comprehensive financial data API
- FinancialDatasets.ai for their financial statements and insider trading data 