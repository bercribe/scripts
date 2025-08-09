import yfinance as yf
from curl_cffi import requests as curl_requests

symbol = "VTTSX"
period = "1mo"

session = curl_requests.Session(impersonate="chrome")
ticker = yf.Ticker(symbol, session=session)
hist = ticker.history(period)

print(hist)
