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

BECU_CHECKING = "Assets:JointChecking:BECU"
BOA_CARD = "Liabilities:CreditCard:BankOfAmerica"
CAPITAL_ONE_CARD = "Liabilities:JointCreditCard:CapitalOne"
CHASE_CARD = "Liabilities:CreditCard:Chase"
CITI_CARD = "Liabilities:JointCreditCard:Citi"
DISCOVER_CARD = "Liabilities:CreditCard:Discover"
FIDELITY_BROKERAGE = "Assets:Equity:FidelityBrokerage"
FIDELITY_IRA = "Assets:Equity:FidelityIRA"
GUIDELINE_401K = "Assets:Equity:Guideline401k"
LMCU_CHECKING = "Assets:Saving:LMCU"
PAYPAL_CRYPTO = "Assets:Crypto:Paypal"
SEATTLE_CITY_LIGHT = "Liabilities:Utilities:SeattleCityLight"
VENMO_CASH = "Assets:Cash:Venmo"

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
        if account_name == "CREDIT CARD":
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
            return PAYPAL_CRYPTO

    if org_name == "Seattle City Light":
        if account_name == "Bill 5905":
            return SEATTLE_CITY_LIGHT

    if org_name == "Venmo":
        if account_name == "Matoska-Waltz":
            return VENMO_CASH

    return f"Account:UNKNOWN:{org_name}:{account_name}"

# TODO: implement these
# account is a string, transaction is a simplefin json object
def lookupIncome(account, transaction):
    payee = transaction["payee"]
    description = transaction["description"]

    # these will be provided by the account making the payment
    if account in [BOA_CARD, CAPITAL_ONE_CARD, CHASE_CARD, CITI_CARD, DISCOVER_CARD]:
        if payee in ["Automatic Payment", "Bank of America Electronic Payment", "Capital One Credit Card", "Credit Card Payment"]:
            return ""
        if payee in ["Automatic Statement Credit"]:
            return "Income:Refund:Cashback"
    if account == SEATTLE_CITY_LIGHT and payee == "Payment":
        return ""

    if payee == "Anduril Industri":
        return "Income:Salary:Anduril"
    
    if payee == "Electronic Arts":
        return "Income:Salary:ElectronicArts"

    if payee == "Dividend":
        return "Income:Dividend"
    
    if payee == "Interest Income":
        return "Income:Interest"

    return f"Income:UNKNOWN:{payee}"

def lookupExpense(account, transaction):
    payee = transaction["payee"]
    description = transaction["description"]

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
    if payee == "Seattle City Light":
        return SEATTLE_CITY_LIGHT

    if payee == "Humble Bundle":
        return "Expenses:Entertainment"

    return f"Expenses:UNKNOWN:{payee}"

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
days_to_fetch = 7

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
            income_name = lookupIncome(account_name, trans)
            if income_name == "":
                continue
            amount = '${0}'.format(abs(amount))
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
            amount = '${0}'.format(abs(amount))
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
                if entry not in file_contents:
                    file.write(entry)
                    file_contents += entry
