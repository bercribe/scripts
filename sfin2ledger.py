# based on:
# https://beta-bridge.simplefin.org/info/developers
# https://github.com/simplefin/sfin2ledger/blob/master/sfin2ledger.py
# https://github.com/avirut/bursar/blob/master/src/update.py

# simplefin spec: https://www.simplefin.org/protocol.html#transaction

import requests
import base64
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import json
import re
import yfinance as yf

BECU_CHECKING = "Assets:JointChecking:BECU"
BOA_CARD = "Liabilities:CreditCard:BankOfAmerica"
CAPITAL_ONE_CARD = "Liabilities:JointCreditCard:CapitalOne"
CASH = "Assets:Cash"
CHASE_CARD = "Liabilities:CreditCard:Chase"
CITI_CARD = "Liabilities:JointCreditCard:Citi"
DISCOVER_CARD = "Liabilities:CreditCard:Discover"
FIDELITY_BROKERAGE = "Assets:Equity:FidelityBrokerage"
FIDELITY_IRA = "Assets:Equity:FidelityIRA"
GUIDELINE_401K = "Assets:Equity:Guideline401k"
LMCU_CHECKING = "Assets:Checking:LMCU"
PAYPAL_CASH = "Assets:Cash:Paypal"
PENFED_MORTGAGE = "Liabilities:Mortgage:Penfed"
SEATTLE_CITY_LIGHT = "Liabilities:Utilities:SeattleCityLight"
VENMO_CASH = "Assets:Cash:Venmo"

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
    "Dimitriou's Jazz Alley",
    "Eggspectation",
    "Happy Lemon University",
    "Hokkaido Ramen Santouseattle Wa",
    "Island Girl Seafood",
    "Mango for Everyone Quil Ceda Vilwa",
    "Pagliacci Magnolia",
    "Py Delicatus Location",
    "Qdoba",
    "Shiki",
    "Starbucks",
    "Sushi Burrito",
    "Sushi Lover",
    "Taco Bell",
    "Tacos Chukis South",
    "Tacos Chukis South Laseattle Wa",
    "The Dolar Shop",
    "Tuktukthai Tuk",
    "Von's Spirits Seattle Wa Restaurants",
]

SUBSCRIPTIONS = {
    "Appest Limited Wan Chai": "WebServices:TickTick",
    "Amazon Prime Membership": "WebServices:AmazonPrime",
    "Github.com": "WebServices:Github",
    "Google Domains": "WebServices:GoogleDomains",
    "Google Drive": "WebServices:GoogleOne",
    "Kagi.com": "WebServices:Kagi",
    "OpenAI": "WebServices:ChatGPT",
    "Patreon": "Patreon:MCDM",
    "Raindrop Io": "WebServices:Raindrop",
    "Simplefin.org": "WebServices:SimpleFin",
    "Wasabi Technologies": "WebServices:Wasabi",
}

def getStockPrice(symbol, date):
    start_date = date.strftime("%Y-%m-%d")
    end_date = date + timedelta(days=1)
    end_date = end_date.strftime("%Y-%m-%d")

    ticker = yf.Ticker(symbol)
    hist = ticker.history(start=start_date, end=end_date)
    if not hist.empty:
        return hist["Close"][0]
    else:
        return None

# account is a simplefin json object
def lookupAccount(account):
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
        if account_name == "Costco Anywhere Visa\u00ae\u00a0Card by Citi-0276":
            return CITI_CARD

    if org_name == "Discover Credit Card":
        if account_name == "Discover it Card":
            return DISCOVER_CARD

    if org_name == "Fidelity Investments":
        if account_name == "Individual":
            return FIDELITY_BROKERAGE
        if account_name == "ROTH IRA":
            return FIDELITY_IRA
        
    if org_name == "Guideline":
        if account_name == "Anduril Industries Inc":
            return GUIDELINE_401K

    if org_name == "Lake Michigan CU":
        if account_name == "MAX CHECKING":
            return LMCU_CHECKING

    if org_name == "Paypal":
        if account_name == "Crypto":
            return PAYPAL_CASH

    if org_name == "Seattle City Light":
        if account_name == "Bill 5905":
            return SEATTLE_CITY_LIGHT

    if org_name == "Venmo":
        if account_name == "Matoska-Waltz":
            return VENMO_CASH

    return f"Account:UNKNOWN:{org_name}:{account_name}"

# TODO: implement these
# account is a string, transaction is a simplefin json object
def lookupIncome(account, transaction, amount):
    payee = transaction["payee"]
    description = transaction["description"]

    # these will be provided by the account making the payment
    if account in [BOA_CARD, CAPITAL_ONE_CARD, CHASE_CARD, CITI_CARD, DISCOVER_CARD]:
        if payee in ["Automatic Payment", "Bank of America Electronic Payment", "Capital One Credit Card", "Credit Card Payment"]:
            return ""
        if payee in ["Automatic Statement Credit", "Automatic Statement Credit Awards and Rebate Credits", "Cash Rewards", "Cash Back Reward", "Redemption Credit"]:
            return "Income:Refund:Cashback"
    if account == BECU_CHECKING:
        if payee == "Matoska Waltz Onlne Transfer":
            return ""
    if account == LMCU_CHECKING:
        if payee == "Deposit Matoska Waltz P Data Onlne Transfer Co Becu Webxfr Name":
            return ""
    if account == FIDELITY_BROKERAGE:
        if payee == "Electronic Funds Transfer Received":
            return ""
    if account == SEATTLE_CITY_LIGHT and payee == "Payment":
        return ""

    if account == GUIDELINE_401K:
        if amount < 1000:
            return "Income:Dividend"
        else:
            return "Income:Salary:Anduril"

    if payee == "Anduril Industri":
        return "Income:Salary:Anduril"
    
    if payee == "Electronic Arts":
        return "Income:Salary:ElectronicArts"

    if payee == "M Waltz" and description.startswith("DEPOSIT RMPR"):
        return "Income:Refund:Anduril"

    if payee == "Dividend":
        return "Income:Dividend"
    
    if payee == "Interest Income":
        return "Income:Interest"

    category = lookupCategory(payee, description)
    if category != "":
        return f"Income:Refund:{category}"

    return f"Income:UNKNOWN:{payee}"

def lookupExpense(account, transaction):
    payee = transaction["payee"]
    description = transaction["description"]

    if payee == "Becu Webxfr Transfer Data Onlne Co Name Matoska Waltz":
        return BECU_CHECKING
    if payee == "Lamicu Webxfr Onlne Transfer":
        return LMCU_CHECKING
    if account != FIDELITY_BROKERAGE and payee == "Fidelity":
        return FIDELITY_BROKERAGE
    if payee == "Bank of America Credit Card":
        return BOA_CARD
    if payee == "Capital One Credit Card":
        return CAPITAL_ONE_CARD
    if payee == "Chase Credit Card":
        return CHASE_CARD
    if payee == "Citi Credit Card":
        return CITI_CARD
    if payee == "Discover Credit Card":
        return DISCOVER_CARD
    if payee == "Mortgage Payment":
        return PENFED_MORTGAGE
    if description.startswith("PAYPAL"):
        return PAYPAL_CASH
    if payee == "Transfer to Venmo":
        return VENMO_CASH
    if payee == "ATM Withdrawal":
        return CASH
    if payee == "Seattle City Light":
        return SEATTLE_CITY_LIGHT

    if account in [FIDELITY_BROKERAGE, FIDELITY_IRA]:
        if payee == "Reinvestment Cash" or description == "REINVESTMENT FIDELITY GOVERNMENT MONEY MARKET (SPAXX) (Cash)":
            return f"{account}:SPAXX"
        match = re.search(r"YOU BOUGHT PROSPECTUS UNDER SEPARATE COVER.*\((.*)\) \(Cash\)", description)
        if match:
            symbol = match.group(1)
            return f"{account}:{symbol}"

    if account == SEATTLE_CITY_LIGHT:
        if payee == "Bill Amount":
            return "Expenses:Utilities"

    category = lookupCategory(payee, description)
    if category != "":
        return f"Expenses:{category}"

    return f"Expenses:UNKNOWN:{payee}"

def lookupCategory(payee, description):
    if payee in ["Raygun Lounge Seattle Wa"]:
        return "Entertainment:Bars"
    if payee in ["Classbento"]:
        return "Entertainment:Classes"
    if payee == "Humble Bundle":
        return "Entertainment:Digital"
    if payee in ["PlayStation"]:
        return "Entertainment:Games"
    if payee in ["Century Ballroom", "Grace Gow", "Pay Northwest", "Seattle Ice Center", "Seattle Ice Center Travel Entertainment", "Seattle Mixed Martial"]:
        return "Entertainment:Recreation"
    if payee in ["Jazzalley.com", "StubHub!", "Ticketmaster"]:
        return "Entertainment:Shows"
    if payee in ["Foreign Transaction Fee", "Deposit ATM Refund"]:
        return "Fees"
    if payee in ["Asian Family Market Se", "Costco", "Girl Scouts", "Trader Joe's", "Quality Food Centers", "Uwajimaya", "Whole Foods"]:
        return "Food:Groceries"
    if payee in RESTURAUNT_PAYEES:
        return "Food:Resturaunts"
    if payee in ["DoorDash"]:
        return "Food:Takeout"
    if payee in ["Dental Care", "Elevate Chiropractic"]:
        return "Healthcare"
    if payee in ["Cost Plus Drugs", "Cost Plus Drugs Fl Merchandise", "Walgreens"]:
        return "Healthcare:Drugs"
    if payee in ["The Home Depot"]:
        return "Home"
    if payee in ["Ikea", "Room & Board Web"]:
        return "Home:Furnishings"
    if payee in ["Banfield Pet Hospital", "Chewy", "Magnolia Paw Spa", "Matoska Waltz Paid Caitlin Dejong", "Meowtel Inc", "Petco", "Petco.com", "Mud Bay Pet Supplies"]:
        return "Pets"
    if payee in ["Alipay Beijing Cny", "Amazon", "Backerkit.com", "City Super Limited Tsimshatsui", "eBay", "Etsy", "Fireworks Gallery", "Goodwill", "Kurzgesagt", "Meh.com", "Merchandise"]:
        return "Shopping"
    if payee in ["Kinokuniya Bookstores"]:
        return "Shopping:Books"
    if payee in ["Abercrombie & Fitch", "Calvin Klein", "Express", "Skechers", "Ted Baker", "Under Armour", "UNIQLO"]:
        return "Shopping:Clothing"
    if payee in ["Michaels"]:
        return "Shopping:Crafts"
    if payee in ["Uncommon Goods"]:
        return "Shopping:Gifts"
    if payee in ["Paypro Europe Limited London Merchandise"]:
        return "Shopping:Virtual"
    if payee in ["T-Mobile"]:
        return "Subscriptions:CellService"
    if payee == "CenturyLink":
        return "Subscriptions:InternetService"
    if payee == "Email" and description.startswith("BC.HEY EMAIL"):
        return "Subscriptions:WebServices:HeyEmail"
    if payee in SUBSCRIPTIONS.keys():
        return f"Subscriptions:{SUBSCRIPTIONS[payee]}"
    if payee in ["Delta Airlines"]:
        return "Travel:Air"
    if payee in ["Washington State Ferries"]:
        return "Travel:Fares"
    if payee in ["Costco Gas"]:
        return "Travel:Gas"
    if payee in ["Byt King County Metro", "Lyft", "Uber Trip"]:
        return "Travel:Ground"
    if payee in ["Washington Vehicle Licensing"]:
        return "Travel:License"
    if payee in ["ParkWhiz", "Paybyphone Diamond Par", "Sdot Paybyphone Parkin"]:
        return "Travel:Parking"
    if payee in ["WSDOT Good To Go Pass"]:
        return "Travel:Tolls"
    if payee == "Seattle Public Utilities":
        return "Utilities"
    if payee == "Puget Sound Energy":
        return "Utilities:NaturalGas"
    
    # long tail low confidence matching
    if matchWords(payee, "Museum"):
        return "Entertainment"
    if matchWords(payee, "Skate"):
        return "Entertainment:Recreation"
    if matchWords(payee, "Theatre", "Theatres"):
        return "Entertainment:Shows"
    if matchWords(payee, "Restaurants"):
        return "Food:Resturaunts"
    if matchWords(payee, "Drug"):
        return "Healthcare:Drugs"
    if matchWords(payee, "Couch"):
        return "Home:Furnishings"
    if matchWords(payee, "Cat", "Cats"):
        return "Pets"
    if matchWords(payee, "Google"):
        return "Shopping:Virtual"
    if matchWords(payee, "Fi"):
        return "Subscriptions:CellService"
    if matchWords(payee, "Gas", "Fuel"):
        return "Travel:Gas"
    if matchWords(payee, "Inn", "Inns"):
        return "Travel:Lodging"
    if matchWords(payee, "Parking"):
        return "Travel:Parking"
    
    return ""

def matchWords(phrase, *words):
    for word in words:
        if re.search(r'\b' + word + r'\b', phrase):
            return True
    return False

def checkAltPrice(account, transaction):
    if account not in [FIDELITY_BROKERAGE, FIDELITY_IRA]:
        return None

    description = transaction["description"]
    match = re.search(r"YOU BOUGHT PROSPECTUS UNDER SEPARATE COVER.*\((.*)\) \(Cash\)", description)
    if not match:
        return None

    symbol = match.group(1)
    date = datetime.fromtimestamp(transaction['posted'])
    price = getStockPrice(symbol, date)
    if price == None:
        return None

    amount = abs(float(transaction['amount']))
    stock_count = amount / price
    return f"{stock_count:.6f} {symbol} @@ {amount:.2f} USD"

# 1. Get a Setup Token
setup_token = "aHR0cHM6Ly9iZXRhLWJyaWRnZS5zaW1wbGVmaW4ub3JnL3NpbXBsZWZpbi9jbGFpbS8yMkYzNkVBMTFDRTU2MDcwNUE3ODE0QkU3NEMxODM2RDg5NjgxMDNDMDY5QzZDOTQ0QUU2QkE1QTc2ODlBRkU3NTVEOERFNkY3OTcxMDcxMDM5NjI1MUJCOEVGREJDMTI3M0JFRkFFMzRCNjFFMUVEODQ1MDI5MDZDRUE4NTc5MQ=="
def claimAccessToken():
    # 2. Claim an Access URL
    claim_url = base64.b64decode(setup_token)
    response = requests.post(claim_url)
    access_url = response.text
    print(access_url)

access_url = "https://36C0AB5239276B8157BC30B0AD96F38AF9B7CBC5FC0AF5B1BFAAA6BA5AB4BBEC:4EE0F6998491013B2F394F1818A0C6F3FD294857EC5889B096562735CC97DC20@beta-bridge.simplefin.org/simplefin"

main_ledger = "main.ledger"
ledger_prefix = "sfin"
days_to_fetch = 14

def fetchSimplefin():
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
        amount = Decimal(trans['amount'])
        approx_width = 40

        account_name = lookupAccount(trans['account'])
        if amount > 0:
            # income
            income_name = lookupIncome(account_name, trans, amount)
            if income_name == "":
                continue
            alt_price = checkAltPrice(account_name, trans)
            amount = alt_price or '${0}'.format(abs(amount))
            space = ' '*max(approx_width-len(account_name)-len(amount), 4)
            entry.append('    {account_name}{space}{amount}'.format(
                account_name=account_name,
                space=space,
                amount=amount))
            entry.append(f'    {income_name}')
        else:
            # expense
            expense_name = lookupExpense(account_name, trans)
            if expense_name == "":
                continue
            alt_price = checkAltPrice(account_name, trans)
            amount = alt_price or '${0}'.format(abs(amount))
            space = ' '*max(approx_width-len(expense_name)-len(amount), 4)
            entry.append('    {expense_name}{space}{amount}'.format(
                expense_name=expense_name,
                space=space,
                amount=amount))
            entry.append('    {0}'.format(account_name))
        entry.append('')
        entry.append('')
        entries[ledger_name].append('\n'.join(entry))
    return entries

def getSimplefin():
    log_name = f"log_{datetime.today().strftime('%Y-%m-%d')}.json"
    try:
        with open(log_name, "r") as log:
            return json.loads(log.read())
    except:
        data = fetchSimplefin()
        with open(log_name, 'a+') as log:
            log.write(json.dumps(data, indent=4))
        return data

data = getSimplefin()
ledger = simplefin2Ledger(data)
with open (main_ledger, 'a+') as main:
    main.seek(0)
    main_contents = main.read()
    for ledger_name, ledger_contents in ledger.items():
        include_text = f"include {ledger_name}\n"
        if include_text not in main_contents:
            main.write(include_text)
        with open(ledger_name, 'a+') as file:
            file.seek(0)
            file_contents = file.read()
            for entry in ledger_contents:
                if re.sub('\s+', ' ', entry) not in re.sub('\s+', ' ', file_contents):
                    file.write(entry)
                    file_contents += entry

if len(data["errors"]) > 0:
    sfin_bridge_url = "https://beta-bridge.simplefin.org/auth/login"
    raise RuntimeError(data["errors"], sfin_bridge_url)
