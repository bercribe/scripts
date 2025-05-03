{
  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs = {self, nixpkgs, ...}: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages."${system}";
    python = (pkgs.python3.withPackages (python-pkgs: with python-pkgs; [
      requests
      yfinance
      curl-cffi
    ]));
  in {
    devShells."${system}".default = pkgs.mkShell {
      packages = [python];
    };
    packages."${system}" = {
      default = self.packages."${system}".runner;
      runner = let
        pythonCmd = "${python}/bin/python";
        ledgerScheduler = pkgs.writeText "ledger_scheduler" (builtins.readFile ./ledger_scheduler.py);
        commodityUpdater = pkgs.writeText "commodity_updater" (builtins.readFile ./commodity_updater.py);
        sfin2ledger = pkgs.writeText "sfin2ledger"(builtins.readFile ./sfin2ledger.py);
      in
        pkgs.writeShellScriptBin "runner" ''
          ${pythonCmd} ${ledgerScheduler} -s ledger/carta_projection.ledger -d ledger/carta.ledger
          ${pythonCmd} ${ledgerScheduler} -s ledger/mortgage_interest_projection.ledger -d ledger/mortgage.ledger
          ${pythonCmd} ${ledgerScheduler} -s ledger/mortgage_escrow_projection.ledger -d ledger/mortgage.ledger
          ${pythonCmd} ${commodityUpdater} -c ledger/commodities.ledger
          ${pythonCmd} ${sfin2ledger} -d ledger/ -l logs/ -a scripts/access_url
        '';
    };
  };
}
