{
  description = "Python project";

  inputs.flake-compat.url = "github:edolstra/flake-compat";
  inputs.flake-compat.flake = false;
  inputs.nixpkgs = {
    url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };
  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.flake-utils.inputs.nixpkgs.follows = "nixpkgs";


  outputs = {
    self,
    flake-compat,
    flake-utils,
    nixpkgs,
    ...
  } @ inputs:
    flake-utils.lib.eachDefaultSystem (system:
    let pkgs = nixpkgs.legacyPackages.${system}; in
    rec {
      formatter = nixpkgs.legacyPackages."${system}".alejandra;
      packages = {};
      devShell = pkgs.mkShell {
        packages = [
          pkgs.graphviz
          pkgs.python312
          pkgs.poetry
          pkgs.nil
          pkgs.nixfmt
        ];
        shellHook = ''
          poetry install
          source $(poetry env info --path)/bin/activate
        '';
      };
    });
}
