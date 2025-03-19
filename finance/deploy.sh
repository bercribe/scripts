set -eo pipefail

dir="/mnt/super-fly/shared/finances/scripts"

cp flake.nix "$dir"
cp flake.lock "$dir"
cp sfin2ledger.py "$dir"
cp ledger_scheduler.py "$dir"
cp commodity_updater.py "$dir"

echo "Remember to \`chown finance-sync: access_url\` on the remote!"
