with import <nixpkgs> {};

let
  python-rtmidi = pkgs.callPackage ~/.config/nixpkgs/packages/python-rtmidi.nix { inherit (pkgs.python3Packages) alabaster buildPythonPackage fetchPypi flake8 tox; isPy27 = false; };

in (python3.withPackages (ps: with ps; [
  pytest
  pytest-timeout
  pyyaml
  requests
  requests-mock
  python-rtmidi
  yapf
])).env
