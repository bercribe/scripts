## README

### initialize a python virtual env
```
virtualenv venv
# or
python -m venv venv

source venv/bin/activate
```

### notion_reading_list.py
Used to add images to notion reading list database.
install:
```
pip install notion-client requests
```
run:
```
python notion_reading_list.py
```

### reading_list_urls.py
Fetches URLs for reading list.
install:
```
pip install requests
pip install pyyaml
```
run:
```
python reading_list_urls.py
```

### sfin2ledger.py
Fetches recent transactions and saves them to a ledger.
install:
```
pip install requests
```
run:
```
python sfin2ledger.py
```

### ledger_scheduler.py
Modified from - https://github.com/tazzben/LedgerScheduler
Moves transactions from a projection ledger into the main ledger.
install:
```
pip install python-dateutil
```
run:
```
python ledger_scheduler.py -s projected.ledger -d main.ledger
```

### commodity_updater.py
install:
```
pip install yfinance
```
run:
```
python commodity_updater.py
```
