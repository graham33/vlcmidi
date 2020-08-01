with import <nixpkgs> {};
with python38Packages;

let
  python-rtmidi = pkgs.callPackage ~/.config/nixpkgs/packages/python-rtmidi.nix { inherit alabaster buildPythonPackage fetchPypi flake8 tox; isPy27 = false; };

in
  buildPythonPackage rec {
    name = "vlcmidi";
    src = ".";
    propagatedBuildInputs = [ click
                              pytest
                              pytest-timeout
                              pyyaml
                              requests
                              requests-mock
                              python-rtmidi
                              yapf
                            ];
  }
