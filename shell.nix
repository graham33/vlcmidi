with import <nixpkgs> {};
with python38Packages;

buildPythonPackage {
  name = "vlcmidi";
  src = ".";
  nativeBuildInputs = [
    flake8
    yapf
  ];
  propagatedBuildInputs = [
    click
    pyyaml
    requests
    python-rtmidi
  ];
  checkInputs = [
    pytest
    pytest-timeout
    requests-mock
  ];
}
