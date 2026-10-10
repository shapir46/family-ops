#!/bin/sh
# Run inside the working dir that holds these files: installs fonts into ./fonts
set -e
mkdir -p fonts && cd fonts
for t in grenze-gotisch playfair-display libre-baskerville; do
  npm pack @fontsource/$t --silent >/dev/null 2>&1
  mkdir -p fontsource-$t && tar xzf fontsource-$t-*.tgz -C fontsource-$t
done
pip list 2>/dev/null | grep -qi playwright || pip install playwright --break-system-packages -q
