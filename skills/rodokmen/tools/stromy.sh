#!/bin/bash
# Překreslí všechny malované stromy (data/strom_*.json) a obnoví obrázky na webu (web/public/stromy/).
set -e
cd "$(dirname "$0")/.."
v=dokumenty/stromy/vystup
w=web/public/stromy
for j in data/strom_*.json; do
  f=$(basename "$j" .json)
  python3 -I tools/strom_graficky.py "$j" "$v"
  magick "$v/$f.png" -quality 85 "$w/$f.jpg"
  magick "$v/$f.png" -resize 1800x1800 -quality 80 "$w/${f}_nahled.jpg"
done
