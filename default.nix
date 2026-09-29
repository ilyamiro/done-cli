{ pkgs ? import <nixpkgs> {} }:

pkgs.stdenv.mkDerivation {
  pname = "done";
  version = "0.1.0";

  src = ./.;

  nativeBuildInputs = [
    pkgs.python3
  ];

  installPhase = ''
    mkdir -p $out/bin
    cp done.py $out/bin/done-cli
    chmod +x $out/bin/done-cli
    patchShebangs $out/bin/done-cli
  '';
}
