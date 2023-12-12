import requests
import base64
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

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
ledger_prefix = "sfin_"
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
        ledger_name = ledger_prefix + posted.strftime('%Y-%m') + ".ledger"
        entry = []
        posted_string = posted.strftime('%Y/%m/%d')
        entry.append('{0} {1}'.format(posted_string, trans['description']))
        amount = Decimal(trans['amount'])
        approx_width = 40

        if amount > 0:
            # income
            name = 'Assets:{0}'.format(trans['account']['name'])
            amount = '${0}'.format(abs(amount))
            space = ' '*(approx_width-len(name)-len(amount))
            entry.append('    {name}{space}{amount}'.format(
                name=name,
                space=space,
                amount=amount))
            entry.append('    Income:UNKNOWN')
        else:
            # expense
            name = 'Expenses:UNKNOWN'
            amount = '${0}'.format(abs(amount))
            space = ' '*(approx_width-len(name)-len(amount))
            entry.append('    {name}{space}{amount}'.format(
                name=name,
                space=space,
                amount=amount))
            entry.append('    Assets:{0}'.format(trans['account']['name']))
        entry.append('')
        entry.append('')
        entries[ledger_name].append('\n'.join(entry))
    return entries

data = fetchSimplefin()
ledger = simplefin2Ledger(data)
with open (main_ledger, 'a+') as main:
    main.seek(0)
    main_contents = main.read()
    for ledger_name, ledger_contents in ledger.items():
        include_text = "include " + ledger_name + "\n"
        if include_text not in main_contents:
            main.write(include_text)
        with open(ledger_name, 'a+') as file:
            file.seek(0)
            file_contents = file.read()
            for entry in ledger_contents:
                if entry not in file_contents:
                    file.write(entry)
