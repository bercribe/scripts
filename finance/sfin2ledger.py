# Fetches recent transactions and saves them to a ledger.
# based on:
# https://beta-bridge.simplefin.org/info/developers
# https://github.com/simplefin/sfin2ledger/blob/master/sfin2ledger.py
# https://github.com/avirut/bursar/blob/master/src/update.py

# simplefin spec: https://www.simplefin.org/protocol.html#transaction

import argparse
import requests
import base64
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import json
import os
import re
import stat
import yfinance as yf
from curl_cffi import requests as curl_requests

BECU_CHECKING = "Assets:JointChecking:BECU"
BOA_CARD = "Liabilities:CreditCard:BankOfAmerica"
CAPITAL_ONE_CARD = "Liabilities:JointCreditCard:CapitalOne"
CASH = "Assets:Cash"
CHASE_CARD = "Liabilities:CreditCard:Chase"
CITI_CARD = "Liabilities:JointCreditCard:Citi"
DISCOVER_CARD = "Liabilities:CreditCard:Discover"
FIDELITY_BROKERAGE = "Assets:Equity:FidelityBrokerage"
FIDELITY_IRA = "Assets:Equity:FidelityIRA"
FIDELITY_ANDURIL_401K = "Assets:Equity:FidelityAnduril401k"
GUIDELINE_401K = "Assets:Equity:Guideline401k"
LMCU_CHECKING = "Assets:Checking:LMCU"
PAYPAL_CASH = "Assets:Cash:Paypal"
PENFED_MORTGAGE = "Liabilities:Mortgage:Penfed"
SEATTLE_CITY_LIGHT = "Liabilities:Utilities:SeattleCityLight"
VENMO_CASH = "Assets:Cash:Venmo"

FIDELITY_ACCOUNTS = [FIDELITY_BROKERAGE, FIDELITY_IRA, FIDELITY_ANDURIL_401K]

FIDELITY_SALE = r"YOU SOLD .*\((.*)\) \(Cash\)"
FIDELITY_DESCRIPTION_PATTERNS = [
    r"YOU BOUGHT PROSPECTUS UNDER SEPARATE COVER.*\((.*)\) \(Cash\)",
    r"REINVESTMENT.*\((.*)\) \(Cash\)",
    FIDELITY_SALE,
]

RECREATION_PAYEES = [
    "At Seattle Aquarium",
    "Bestlocker",
    "Century Ballroom",
    "Crystal Mountain Resort",
    "Grace Gow",
    "Mount Rainier National Park",
    "Pay Northwest",
    "Recreation.gov",
    "Seattle Ice Center",
    "Seattle Ice Center Travel Entertainment",
    "Seattle Mixed Martial",
    "Vertical World Seattle",
    "Vertical World Seattle Vertiwa",
    "Woodland Park Zoo",
]

RESTURAUNT_PAYEES = [
    "3rd Street Diner",
    "Auntie Ann's",
    "Bamboo Sushi Seatt",
    "Bliss Tea Tulalip",
    "Burger Compan",
    "Burger Company",
    "Cleo's Brown Beam Tavern",
    "Coffee Tree",
    "Denny's",
    "Di Fiora",
    "Dimitriou's Jazz Alley",
    "Donburi House",
    "Dough Zone Kirklan",
    "Eggspectation",
    "Fort St George",
    "Happy Lemon University",
    "Hokkaido Ramen Santouseattle Wa",
    "Hummingbird Sushi",
    "Island Girl Seafood",
    "Itsumono",
    "Joule Stone",
    "Kamonegi",
    "Mango for Everyone Quil Ceda Vilwa",
    "Maripili",
    "Meet Fresh Tukwila",
    "Milkvue & Diy Tea Labseattle Wa"
    "Moontree Sushi & Tapas",
    "Pagliacci Magnolia",
    "Py Delicatus Location",
    "Qdoba",
    "Raretea Kirkland Kirkland Wa",
    "Reckless Noodle",
    "Sen Noodle Bar",
    "Shiki",
    "Shiro's Sushi",
    "Spot Cafe",
    "Starbucks",
    "Sushi Burrito",
    "Sushi by Scratch Res",
    "Sushi Lover",
    "Taco Bell",
    "Tacos Chukis South",
    "Tacos Chukis South Laseattle Wa",
    "The Dolar Shop",
    "Tock Atkamonegi",
    "Tuktukthai Tuk",
    "Turtle Coffee Seattle Wa",
    "Uep Skybowl Cafe",
    "Uptown Espresso",
    "Von's Spirits",
    "Von's Spirits Seattle Wa Restaurants",
    "Yoroshiku Seattle Wa",
    "Zhuge Grill Fish",
]

SUBSCRIPTIONS = {
    "Appest Limited Wan Chai": "WebServices:TickTick",
    "Amazon Prime": "WebServices:AmazonPrime",
    "Backblaze": "WebServices:Backblaze",
    "Du Chinese": "WebServices:DuChinese",
    "Github.com": "WebServices:Github",
    "Google Drive": "WebServices:GoogleOne",
    "Hulu": "WebServices:Hulu",
    "Kagi.com": "WebServices:Kagi",
    "OpenAI": "WebServices:ChatGPT",
    "Patreon": "Patreon",
    "Raindrop Io": "WebServices:Raindrop",
    "Simplefin Bridge": "WebServices:SimpleFin",
    "Spotify": "WebServices:Spotify",
    "Squarespace": "WebServices:Squarespace",
    "Wasabi.com": "WebServices:Wasabi",
}

errors = []

def getStockPrice(symbol, date):
    start_date = date.strftime("%Y-%m-%d")
    end_date = date + timedelta(days=1)
    end_date = end_date.strftime("%Y-%m-%d")

    # https://github.com/ranaroussi/yfinance/issues/2422
    session = curl_requests.Session(impersonate="chrome")
    ticker = yf.Ticker(symbol, session=session)
    hist = ticker.history(start=start_date, end=end_date)
    if not hist.empty:
        return hist["Close"].iloc[0]
    else:
        return None

# account is a simplefin json object
def lookupAccount(transaction):
    account = transaction['account']
    org_name = account["org"]["name"]
    account_name = account["name"]
    
    if org_name == "Bank of America":
        if account_name == "Alumni Association of the University of Michigan Visa Signature - 2799":
            return BOA_CARD

    if org_name == "Boeing Employee Credit Union":
        if account_name == "Checking":
            return BECU_CHECKING

    if org_name == "Capital One":
        if account_name == "Quicksilver":
            return CAPITAL_ONE_CARD

    if org_name == "Chase Bank":
        if account_name in ["CREDIT CARD", "Amazon Prime Rewards Visa Signature"]:
            return CHASE_CARD

    if org_name == "Citibank":
        return CITI_CARD

    if org_name == "Discover Credit Card":
        if account_name == "Discover it Card":
            return DISCOVER_CARD

    if org_name == "Fidelity Investments":
        if account_name == "Individual":
            return FIDELITY_BROKERAGE
        if account_name == "ROTH IRA":
            return FIDELITY_IRA
    if org_name == "Fidelity @ Work":
        if account_name == "ANDURIL INDUSTRIES":
            return FIDELITY_ANDURIL_401K
        return ""
    # these are covered above
    if org_name in ["Fidelity 401k", "Fidelity Netbenefits (My Benefits) - Work Place Services"]:
        return ""
        
    if org_name == "Guideline":
        if account_name == "Anduril Industries Inc":
            return GUIDELINE_401K

    if org_name == "Lake Michigan CU":
        if account_name == "MAX CHECKING":
            return LMCU_CHECKING

    if org_name == "Paypal":
        if account_name == "Transfer Money":
            return PAYPAL_CASH
        else:
            return ""

    if org_name == "Seattle City Light":
        if account_name == "Bill 5905":
            return SEATTLE_CITY_LIGHT

    if org_name == "Venmo":
        if account_name == "Matoska-Waltz":
            return VENMO_CASH

    return f"Account:UNKNOWN:{org_name}:{account_name}"

# account is a string, transaction is a simplefin json object
def lookupIncome(account, transaction, amount):
    payee = transaction["payee"]
    description = transaction["description"]

    income = lookupIncomeInternal(account, transaction, amount)
    if income != "":
        return income, ""

    category = lookupLongTailCategory(payee, description)
    if category != "":
        return f"Income:Refund:{category}", "Long tail match"

    return f"Income:UNKNOWN:{payee}", ""

def lookupIncomeInternal(account, transaction, amount):
    payee = transaction["payee"]
    description = transaction["description"]

    # these will be provided by the account making the payment
    if account in [BOA_CARD, CAPITAL_ONE_CARD, CHASE_CARD, CITI_CARD, DISCOVER_CARD]:
        if payee in ["Automatic Payment", "Bank of America Electronic Payment", "Capital One Credit Card", "Credit Card Payment"]:
            return ""
        if payee in ["Automatic Statement Credit", "Automatic Statement Credit Awards and Rebate Credits", "Cash Rewards", "Cash Back Reward", "Redemption Credit"]:
            return "Income:Refund:Cashback"
    if account == BECU_CHECKING:
        if payee in ["Matoska Waltz", "Matoska Waltz Onlne Transfer"]:
            return ""
    if account == LMCU_CHECKING:
        if payee == "Deposit Matoska Waltz P Data Onlne Transfer Co Becu Webxfr Name":
            return ""
    if account == FIDELITY_BROKERAGE:
        if payee == "Electronic Funds Transfer Received":
            return ""
    if account == FIDELITY_ANDURIL_401K:
        if payee == "Contribution":
            return "Income:Salary:Anduril"
    if account == SEATTLE_CITY_LIGHT and payee == "Payment":
        return ""

    if account == GUIDELINE_401K:
        if amount < 1000:
            return "Income:Dividend"
        else:
            return "Income:Salary:Anduril"

    if account in FIDELITY_ACCOUNTS:
        symbol = getSymbol(account, transaction)
        if symbol != None:
            return f"{account}:{symbol}"

    if payee in ["Anduril Industri", "Deposit Anduril Industri Payroll", "Anduril Industriecc"] or payee.startswith("Deposit Anduril Industri"):
        return "Income:Salary:Anduril"
    
    if payee == "Magnit, Llc T9995-00f":
        return "Income:Salary:Meta"

    if payee == "M Waltz" and description.startswith("DEPOSIT RMPR"):
        return "Income:Refund:Anduril"

    if payee == "Dividend":
        return "Income:Dividend"
    
    if payee in ["Interest", "Interest Income"]:
        return "Income:Interest"

    if payee in ["Payments and Credits"]:
        return "Income:Refund"

    category = lookupCategory(payee, description)
    if category != "":
        return f"Income:Refund:{category}"

    return ""

def lookupExpense(account, transaction):
    payee = transaction["payee"]
    description = transaction["description"]

    expense = lookupExpenseInternal(account, transaction)
    if expense != "":
        return expense, ""

    category = lookupLongTailCategory(payee, description)
    if category != "":
        return f"Expenses:{category}", "Long tail match"

    return f"Expenses:UNKNOWN:{payee}", ""

def lookupExpenseInternal(account, transaction):
    payee = transaction["payee"]
    description = transaction["description"]

    if payee == "Becu Webxfr Transfer Data Onlne Co Name Matoska Waltz":
        return BECU_CHECKING
    if payee in ["Lamicu", "Lamicu Webxfr Onlne Transfer"]:
        return LMCU_CHECKING
    if account not in FIDELITY_ACCOUNTS and payee == "Fidelity":
        return FIDELITY_BROKERAGE
    if payee == "Bank of America Credit Card":
        return BOA_CARD
    if payee in ["Capital One Credit Card", "Capital One Credit Card Payment"]:
        return CAPITAL_ONE_CARD
    if payee == "Chase Credit Card":
        return CHASE_CARD
    if payee in ["Citi Credit Card", "Citi Credit Card Payment"]:
        return CITI_CARD
    if payee == "Discover Credit Card":
        return DISCOVER_CARD
    if payee == "Mortgage Payment":
        return PENFED_MORTGAGE
    # account linking is broken on sfin bridge
    # if description.startswith("PAYPAL"):
    #     return PAYPAL_CASH
    if payee == "Transfer to Venmo":
        return VENMO_CASH
    if payee == "ATM Withdrawal":
        return CASH
    if payee == "Seattle City Light":
        return SEATTLE_CITY_LIGHT

    if account in FIDELITY_ACCOUNTS:
        symbol = getSymbol(account, transaction)
        if symbol != None:
            return f"{account}:{symbol}"

    if account == SEATTLE_CITY_LIGHT:
        if payee == "Bill Amount":
            return "Expenses:Utilities"

    category = lookupCategory(payee, description)
    if category != "":
        return f"Expenses:{category}"

    return ""

def lookupCategory(payee, description):
    if payee in ["Feeding America", "Washington Can", "Wmu Foundation Online"]:
        return "Donations"
    if payee in ["Raygun Lounge Seattle Wa", "Shibuya"]:
        return "Entertainment:Bars"
    if payee in ["Experience Learning Commu", "Prime Video"]:
        return "Entertainment"
    if payee in ["Classbento"]:
        return "Entertainment:Classes"
    if payee == "Humble Bundle":
        return "Entertainment:Digital"
    if payee in ["Chess.com", "Mcdmproductions.com", "PlayStation", "Steam", "Valve Bellevue Wa Merchandise"]:
        return "Entertainment:Games"
    if payee in RECREATION_PAYEES:
        return "Entertainment:Recreation"
    if payee in ["Jazzalley.com", "StubHub!", "The Paramount Theatr", "Ticketmaster", "Tock Atshibuya"]:
        return "Entertainment:Shows"
    if payee in ["Handmadesea"]:
        return "Events:Tickets"
    if payee in ["Deposit ATM Refund", "Foreign Transaction Fee", "International Service Fee"]:
        return "Fees"
    if payee in ["Asian Family Market Se", "Ballard", "Costco", "Girl Scouts", "Instacart via Instacart", "Kiki Bakery Seattle Wa", "PCC Community Markets", "Trader Joe's", "Quality Food Centers", "Uwajimaya", "Whole Foods"]:
        return "Food:Groceries"
    if payee in RESTURAUNT_PAYEES:
        return "Food:Resturaunts"
    if payee in ["DoorDash"]:
        return "Food:Takeout"
    if payee in ["Dental Care"] or matchWords(payee, "Elevate Chiropractic"):
        return "Healthcare"
    if payee in ["Cost Plus Drugs", "Cost Plus Drugs Fl Merchandise", "Walgreens"]:
        return "Healthcare:Drugs"
    if payee in ["Stoneway Hardware Ballar Seattle Wa Home Improvement", "The Home Depot"]:
        return "Home"
    if payee in ["Ikea", "Room & Board Web"]:
        return "Home:Furnishings"
    if payee in ["Banfield Pet Hospital", "Chewy", "Magnolia Paw Spa", "Matoska Waltz Paid Caitlin Dejong", "Meowtel Inc", "Petco", "Petco.com", "Mud Bay Pet Supplies"]:
        return "Pets"
    if payee in ["Bartkowiak Accounting"]:
        return "Services:Accounting"
    if payee in ["A and R Solar Waaam Hri", "Fenix Roof Service", "Greenwood Heating & Ai"]:
        return "Services:Contractors"
    if payee in ["Hale Lands"]:
        return "Services:Gardening"
    if payee in ["The Cincinnati Insuran"]:
        return "Services:Insurance"
    if payee in ["Matoska Waltz Paid Sports Haircut"]:
        return "Services:PersonalCare"
    if payee in ["Mullvad"]:
        return "Services:VPN"
    if payee in ["Alipay", "Alipay Beijing Cny", "Amazon", "Amazon Market", "Backerkit.com", "City Super Limited Tsimshatsui", "Dbrand", "eBay", "Etsy", "Fireworks Gallery", "Goodwill", "Kickstarter", "Kurzgesagt", "Meh.com", "Merchandise", "PayPal Payments and Transfers", "Stuhlbergs"]:
        return "Shopping"
    if payee in ["Kindle", "Kinokuniya Bookstores"]:
        return "Shopping:Books"
    if payee in ["Abercrombie & Fitch", "Calvin Klein", "Express", "Skechers", "Ted Baker", "Under Armour", "UNIQLO"]:
        return "Shopping:Clothing"
    if payee in ["Michaels"]:
        return "Shopping:Crafts"
    if payee in ["Adafruit Industries", "Core Devices", "Dell Mkt", "Keycawc", "Kobo", "Lenovocorpo", "Mouser Electronics Inc", "Newegg", "Serverpartdeals", "This Week Pi Shop Inc", "Xidikejdcpa"]:
        return "Shopping:Electronics"
    if payee in ["Tjweddingregistry.com", "Uncommon Goods"]:
        return "Shopping:Gifts"
    if payee in ["U-Haul"]:
        return "Shopping:Organizers"
    if payee in ["Alpine Hut", "Rad Power Bikes"]:
        return "Shopping:Sports"
    if payee in ["Paypro Europe Limited London Merchandise"]:
        return "Shopping:Virtual"
    if payee in ["T-Mobile"]:
        return "Subscriptions:CellService"
    if payee in ["CenturyLink", "Centurylink Lumen"]:
        return "Subscriptions:InternetService"
    if payee == "Email" and description.startswith("BC.HEY EMAIL"):
        return "Subscriptions:WebServices:HeyEmail"
    if payee in SUBSCRIPTIONS.keys():
        return f"Subscriptions:{SUBSCRIPTIONS[payee]}"
    if payee in ["Delta Airlines"]:
        return "Travel:Air"
    if payee in ["Orca Travel Entertainment", "Orca Wagoogle Pay Travel Entertainment", "Washington State Ferries"]:
        return "Travel:Fares"
    if payee in ["ARCO", "Costco Gas"]:
        return "Travel:Gas"
    if payee in ["Byt King County Metro", "Lyft", "Uber Trip"]:
        return "Travel:Ground"
    if payee in ["Washington Vehicle Licensing"]:
        return "Travel:License"
    if payee in ["Courtyard by Marriott"]:
        return "Travel:Lodging"
    if payee in ["Fluerys Collision Center", "Precision Motorworks"]:
        return "Travel:Maintenance"
    if payee in ["impark", "Metropolis", "ParkWhiz", "Paybyphone Diamond Par", "Seattle Central Community", "Sdot Paybyphone Parkin", "SpotHero"]:
        return "Travel:Parking"
    if payee in ["WSDOT Good To Go Pass"]:
        return "Travel:Tolls"
    if payee == "Seattle Public Utilities":
        return "Utilities"
    if payee == "Puget Sound Energy":
        return "Utilities:NaturalGas"

    return ""
    
# long tail low confidence matching
def lookupLongTailCategory(payee, description):
    if matchWords(payee, "Donor"):
        return "Donations"
    if matchWords(payee, "Museum"):
        return "Entertainment"
    if matchWords(payee, "Games"):
        return "Entertainment:Games"
    if matchWords(payee, "Skate"):
        return "Entertainment:Recreation"
    if matchWords(payee, "Theatre", "Theatres"):
        return "Entertainment:Shows"
    if matchWords(payee, "Bakery", "Concessions", "Restaurants", "Roasting", "Seafood", "Tock"):
        return "Food:Resturaunts"
    if matchWords(payee, "Drug"):
        return "Healthcare:Drugs"
    if matchWords(payee, "Couch"):
        return "Home:Furnishings"
    if matchWords(payee, "Cat", "Cats"):
        return "Pets"
    if matchWords(payee, "Amazon Market", "Merchandise"):
        return "Shopping"
    if matchWords(payee, "Google"):
        return "Shopping:Virtual"
    if matchWords(payee, "Fi"):
        return "Subscriptions:CellService"
    if matchWords(payee, "Gas", "Fuel"):
        return "Travel:Gas"
    if matchWords(payee, "Inn", "Inns"):
        return "Travel:Lodging"
    if matchWords(payee, "Garage", "Parking"):
        return "Travel:Parking"
    
    return ""

def matchWords(phrase, *words):
    for word in words:
        if re.search(r'\b' + word + r'\b', phrase):
            return True
    return False

def getSymbol(account, transaction):
    if account == FIDELITY_ANDURIL_401K:
        return "VTTSX"

    payee = transaction["payee"]
    if payee == "Reinvestment Cash":
        return "SPAXX"

    description = transaction["description"]
    for pattern in FIDELITY_DESCRIPTION_PATTERNS:
        match = re.search(pattern, description)
        if match:
            break
    if not match:
        return None
    return match.group(1)

def checkAltPrice(account, transaction):
    if account not in FIDELITY_ACCOUNTS:
        return None

    symbol = getSymbol(account, transaction)
    if not symbol or symbol == "SPAXX":
        return None

    date = datetime.fromtimestamp(transaction['posted'])
    price = getStockPrice(symbol, date)
    if price == None:
        error = f"Error fetching price for symbol={symbol}, transaction={transaction['id']}"
        global errors
        errors.append(error)
        return None

    amount = float(transaction['amount'])
    stock_count = abs(amount) / price
    if amount < 0 or account == FIDELITY_ANDURIL_401K:
        return f"{stock_count:.6f} {symbol} @@ {abs(amount):.2f} USD"
    return f"{amount:.2f} USD @@ {stock_count:.6f} {symbol}"

main_ledger = "main.ledger"
ledger_prefix = "sfin"
days_to_fetch = 30

def fetchSimplefin(access_url_file):
    with open(access_url_file, "r") as url_file:
        access_url = url_file.read()
        # 3. Get some data
        scheme, rest = access_url.split('//', 1)
        auth, rest = rest.split('@', 1)
        url = scheme + '//' + rest + '/accounts'
        username, password = auth.split(':', 1)

        # specify time bounds
        end = datetime.now()
        start = end - timedelta(days=days_to_fetch)
        mparams = {
            "start-date": str(int(start.timestamp())),
            "end-date": str(int(end.timestamp())),
        }

        response = requests.get(url, auth=(username, password), params=mparams)
        return response.json()

def simplefin2Ledger(data):
    all_trans = []
    for account in data['accounts']:
        for transaction in account['transactions']:
            transaction['account'] = account
            all_trans.append(transaction)
    all_trans = sorted(all_trans, key=lambda x:x['posted'])
    entries = defaultdict(list)
    for trans in all_trans:
        posted = datetime.fromtimestamp(trans['posted'])
        ledger_name = f"{ledger_prefix}_{posted.strftime('%Y-%m')}.ledger"
        entry = []
        posted_string = posted.strftime('%Y/%m/%d')
        entry.append('{0} {1}'.format(posted_string, trans['description']))
        trans_id =  trans['id']
        entry.append(f'    ; id: {trans_id}')
        amount = Decimal(trans['amount'])
        approx_width = 40

        account_name = lookupAccount(trans)
        ledger_account_name = account_name
        if account_name in FIDELITY_ACCOUNTS:
            description = trans["description"]
            match = re.search(FIDELITY_SALE, description)
            if match:
                ledger_account_name += ":SPAXX"

        if account_name == "":
            continue
        if amount > 0:
            # income
            income_name, note = lookupIncome(account_name, trans, amount)
            if income_name == "":
                continue
            alt_price = checkAltPrice(account_name, trans)
            amount = alt_price or '${0}'.format(abs(amount))
            space = ' '*max(approx_width-len(ledger_account_name)-len(amount), 4)
            entry.append(f'    {ledger_account_name}{space}{amount}')
            if note != "" :
                entry.append(f'    ; {note}')
            entry.append(f'    {income_name}')
        else:
            # expense
            expense_name, note = lookupExpense(account_name, trans)
            if expense_name == "":
                continue
            alt_price = checkAltPrice(account_name, trans)
            amount = alt_price or '${0}'.format(abs(amount))
            space = ' '*max(approx_width-len(expense_name)-len(amount), 4)
            if note != "" :
                entry.append(f'    ; {note}')
            entry.append(f'    {expense_name}{space}{amount}')
            entry.append(f'    {ledger_account_name}')
        entry.append('')
        entry.append('')
        entries[ledger_name].append({"id": trans_id, "transaction": '\n'.join(entry)})
    return entries

def getSimplefin(log_dir, access_url_file):
    log_name = f"log_{datetime.today().strftime('%Y-%m-%d')}.json"
    try:
        with open(f'{log_dir}/{log_name}', "r") as log:
            return json.loads(log.read())
    except:
        data = fetchSimplefin(access_url_file)
        with open(f'{log_dir}/{log_name}', 'a+') as log:
            log.write(json.dumps(data, indent=4))
        return data

def main(ledger_dir, log_dir, access_url_file):
    data = getSimplefin(log_dir, access_url_file)
    ledger = simplefin2Ledger(data)
    perms = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP
    with open(f'{ledger_dir}/{main_ledger}', 'a+') as main:
        main.seek(0)
        main_contents = main.read()
        for ledger_name, ledger_contents in ledger.items():
            include_text = f"include {ledger_name}\n"
            if include_text not in main_contents:
                main.write(include_text)
            with open(f'{ledger_dir}/{ledger_name}', 'a+') as file:
                file.seek(0)
                file_contents = file.read()
                for entry in ledger_contents:
                    trans_id = entry["id"]
                    transaction = entry["transaction"]
                    if trans_id not in file_contents:
                        file.write(transaction)
                        file_contents += transaction
            os.chmod(f'{ledger_dir}/{ledger_name}', perms)
    os.chmod(f'{ledger_dir}/{main_ledger}', perms)

    if len(data["errors"]) > 0 or len(errors) > 0:
        raise RuntimeError(data["errors"], errors)

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--ledger_dir', required=True)
parser.add_argument('-l', '--log_dir', required=True)
parser.add_argument('-a', '--access_url_file', required=True)
args = parser.parse_args()
main(args.ledger_dir, args.log_dir, args.access_url_file)
