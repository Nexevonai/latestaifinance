# Press Releases
Get earnings press releases for a ticker.

## GET /earnings/press-releases

Try it

## 👋 Overview
The Earnings Press Releases API allows you to fetch a list of earnings-related press releases for a given company.

This data is powered by RSS feeds and is updated instantly when new press releases are published.

The endpoint returns all of the earnings-related press releases that the company has filed with the SEC.

The data returned from the API includes the URL, publish date, and full text of the press release.

To get started, please create an account and grab your API key at financialdatasets.ai.

You will use the API key to authenticate your API requests.

## 📊 Available Tickers
You can fetch a list of available tickers with a GET request to: https://api.financialdatasets.ai/earnings/press-releases/tickers/

## 🚀 Getting Started
There are only 3 steps for making a successful API call:

1. Add your API key to the header of the request as X-API-KEY.
2. Add query params like ticker to filter the data.
3. Execute the API request.

Note: You must include either the ticker in your query params.

## 💻 Example
Press Releases

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
    f'https://api.financialdatasets.ai/earnings/press-releases'
    f'?ticker={ticker}'
)

# make API request
response = requests.get(url, headers=headers)

# parse press releases from the response
press_releases = response.json().get('press_releases')
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

## Response
200

200
application/json
Earnings press releases response

**press_releases**
- object[]

Show child attributes

## Snapshot
## Historical 