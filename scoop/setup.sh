#!/bin/sh
# Run inside the working dir that holds these files: installs fonts into ./fonts
set -e
mkdir -p fonts && cd fonts
for t in grenze-gotisch playfair-display libre-baskerville; do
  npm pack @fontsource/$t --silent >/dev/null 2>&1
  mkdir -p fontsource-$t && tar xzf fontsource-$t-*.tgz -C fontsource-$t
done
# Python packages (incl. playwright) come from the repo's .venv: run render.py with ../.venv/bin/python, or use ./fo python.
