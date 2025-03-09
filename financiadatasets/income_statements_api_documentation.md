# Financial Statements - Income Statements
Get income statements for a ticker.

## GET /financials/income-statements

Try it

## 👋 Overview
The income statements API provides income statements for a given stock ticker.

Income statements are financial statements that provide information about a company's revenues, expenses, and profits over a specific period.

You can filter the data by ticker, period, limit, and cik.

The period parameter can be set to annual, quarterly, or ttm (trailing twelve months). The limit parameter is used to specify the number of statements to return.

To get started, please create an account and grab your API key at financialdatasets.ai.

You will use the API key to authenticate your API requests.

## 📊 Available Tickers
You can fetch a list of available tickers with a GET request to: https://api.financialdatasets.ai/financials/income-statements/tickers/

## 🚀 Getting Started
There are only 3 steps for making a successful API call:

1. Add your API key to the header of the request as X-API-KEY.
2. Add query params like ticker, period and limit to filter the data.
3. Execute the API request.

## 🔎 Filtering the Data
You can filter the data by ticker, period, limit, and report_period.

Note: ticker and period are required. Alternatively, you can use cik instead of ticker as a company identifier in your request.

By default, period is ttm,limit is 4, and report_period is null.

The period parameter can be set to annual, quarterly, or ttm (trailing twelve months). The limit parameter is used to specify the number of periods to return.

The report_period parameter is used to specify the date of the statement. For example, you can include filters like report_period_lte=2024-09-30 and report_period_gte=2024-01-01 to get statements between January 1, 2024 and September 30, 2024.

The available report_period operations are:

- report_period_lte
- report_period_lt
- report_period_gte
- report_period_gt
- report_period

## 💻 Example
Income Statements

```python
import requests

# add your API key to the headers
headers = {
    "X-API-KEY": "your_api_key_here"
}

# set your query params
ticker = 'NVDA'     # stock ticker
period = 'annual'   # possible values are 'annual', 'quarterly', or 'ttm'
limit = 30          # number of statements to return

# create the URL
url = (
    f'https://api.financialdatasets.ai/financials/income-statements'
    f'?ticker={ticker}'
    f'&period={period}'
    f'&limit={limit}'
)

# make API request
response = requests.get(url, headers=headers)

# parse income_statements from the response
income_statements = response.json().get('income_statements')
```

## 💻 Example (with report_period)
Income Statements

```python
import requests

# add your API key to the headers
headers = {
    "X-API-KEY": "your_api_key_here"
}

# set your query params
ticker = 'NVDA'   
period = 'annual'
limit = 100      
report_period_lte = '2024-01-01' # end date
report_period_gte = '2020-01-01' # start date

# create the URL
url = (
    f'https://api.financialdatasets.ai/financials/income-statements'
    f'?ticker={ticker}'
    f'&period={period}'
    f'&limit={limit}'
    f'&report_period_lte={report_period_lte}'
    f'&report_period_gte={report_period_gte}'
)

# make API request
response = requests.get(url, headers=headers)

# parse income_statements from the response
income_statements = response.json().get('income_statements')
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
- required
- The ticker symbol.

**period**
- enum<string>
- required
- The time period of the income statements.
- Available options: annual, quarterly, ttm 

**limit**
- integer
- The maximum number of income statements to return.

**cik**
- string
- The Central Index Key (CIK) of the company.

## Response
200

200
application/json
Income statements response

**income_statements**
- object[]

Show child attributes

## Snapshot
## Balance Sheets 