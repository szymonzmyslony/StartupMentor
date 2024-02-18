{
  description = "Environment with Python, TypeScript, and Bun";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }@inputs:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [];
        };
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = [
            pkgs.poetry
            pkgs.nodejs
            pkgs.python3
            pkgs.graphviz
            pkgs.bun         # Bun package directly from Nixpkgs
            pkgs.typescript  # Include if TypeScript is needed separately
          ];

          shellHook = ''
            if [ -f "pyproject.toml" ]; then
              # We are likely in the Python project directory
              echo "Initializing Poetry environment..."
              poetry install
              source $(poetry env info --path)/bin/activate
            fi

            if [ -f "package.json" ] || [ -f "bun.lockb" ]; then
              # We are likely in the TypeScript/JavaScript project directory
              echo "Installing dependencies with Bun..."
              bun install
            fi
          '';
        };
      }
    );
}
