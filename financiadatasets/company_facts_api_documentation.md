# Company Facts (by ticker)
Get company facts for a ticker.

## GET /company/facts

Try it

## 👋 Overview
Company facts includes data like name, CIK, market cap, total employees, website URL, and more.

The company facts API provides a simple way to access the most important high-level information about a company.

Please note: This API is experimental and free to use.

To get started, please create an account and grab your API key at financialdatasets.ai.

You will use the API key to authenticate your API requests.

## 📊 Available Tickers
You can fetch a list of available tickers with a GET request to: https://api.financialdatasets.ai/company/facts/tickers/

## 🚀 Getting Started
There are only 3 steps for making a successful API call:

1. Add your API key to the header of the request as X-API-KEY.
2. Add query params like ticker filter the data.
3. Execute the API request.

Note: You must include the ticker in your query params.

## 💻 Example
Company Facts

```python
import requests

# add your API key to the headers
headers = {
    "X-API-KEY": "your_api_key_here"
}

# set your query params
ticker = 'AAPL'

# create the URL
url = (
    f'https://api.financialdatasets.ai/company/facts'
    f'?ticker={ticker}'
)

# make API request
response = requests.get(url, headers=headers)

# parse company_facts from the response
company_facts = response.json().get('company_facts')
```

## Authorizations

**X-API-KEY**
- string
- header
- required
- API key for authentication.

## Query Parameters

**ticker**
- string
- The ticker symbol.

**cik**
- string
- The CIK of the company.

## Response
200

200
application/json
Company facts response

**company_facts**
- object

Show child attributes

## Facts (by CIK)
## Prices 