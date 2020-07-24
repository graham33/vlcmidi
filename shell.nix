with import <nixpkgs> {};
with python38Packages;

buildPythonPackage {
  name = "vlcmidi";
  src = ".";
  propagatedBuildInputs = [ click
                            flake8
                            pytest
                            pytest-timeout
                            pyyaml
                            requests
                            requests-mock
                            python-rtmidi
                            yapf
                          ];
}
