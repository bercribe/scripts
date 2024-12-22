## README

### initialize a python virtual env
```
virtualenv venv
# or
python -m venv venv

source venv/bin/activate
```

### scripts

#### check_sync_conflicts

Usage: `python check_sync_conflicts.py <dir>`

Then, can do `find <dir> | grep sync-conflict | xargs -I %% rm %%`
