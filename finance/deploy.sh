dir="/mnt/super-fly/shared/finances/scripts"

cp flake.nix "$dir"
cp flake.lock "$dir"
cp access_url "$dir"
cp run.sh "$dir"
cp sfin2ledger.py "$dir"
cp ledger_scheduler.py "$dir"
cp commodity_updater.py "$dir"
cd "$dir"
ln -s ../ledger ./ledger
ln -s ../logs ./logs
