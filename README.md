## README

### notion_reading_list.py
Used to add images to notion reading list database. To run:
```
virtualenv venv
source venv/bin/activate
pip install notion-client requests
python notion_reading_list.py
```

### reading_list_urls.py
Fetches URLs for reading list. To run:
```
python3 -m venv myenv
source myenv/bin/activate
pip install requests
pip install pyyaml
python reading_list_urls.py
```

### sfin2ledger.py
Fetches recent transactions and saves them to a ledger. To run:
```
python3 sfin2ledger.py
```

### ledger_scheduler.py
Modified from - https://github.com/tazzben/LedgerScheduler
Moves transactions from a projection ledger into the main ledger.

```
python3 ledger_scheduler.py -s projected.ledger -d main.ledger
```
