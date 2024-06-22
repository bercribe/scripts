import yfinance as yf
from datetime import datetime

symbols = ["FNILX", "FXAIX", "ETH", "VTTSX"]

yf_symbols = {
    "ETH": "ETH-USD"
}

period = "14d"

commodities_ledger = "commodities.ledger"

def get_prices(symbol):
    yf_symbol = symbol
    if symbol in yf_symbols:
        yf_symbol = yf_symbols[symbol]
    ticker = yf.Ticker(yf_symbol)
    hist = ticker.history(period)
    return [(symbol, date, row["Close"]) for date, row in hist.iterrows()]

prices = []
for symbol in symbols:
    prices += get_prices(symbol)
current_date = datetime.now().date()
filtered_prices = [entry for entry in prices if entry[1].date() < current_date]
sorted_prices = sorted(filtered_prices, key=lambda x: x[1])

with open(commodities_ledger, 'a+') as commodities:
    commodities.seek(0)
    commodities_contents = commodities.read()
    for entry in sorted_prices:
        ledger_entry = f"P {entry[1].date()} 00:00:00 {entry[0]} {entry[2]} USD\n"
        if ledger_entry not in commodities_contents:
            commodities.write(ledger_entry)
            commodities_contents += ledger_entry
