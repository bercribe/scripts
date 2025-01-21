set -eo pipefail

dir="/mnt/super-fly/shared/finances/scripts"

chmod 600 access_url
cp flake.nix "$dir"
cp flake.lock "$dir"
cp sfin2ledger.py "$dir"
cp ledger_scheduler.py "$dir"
cp commodity_updater.py "$dir"

cp access_url "$dir"
echo "Remember to \`chown finance-sync: access_url\` on the remote!"
