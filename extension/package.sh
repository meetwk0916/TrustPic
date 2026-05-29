#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"

version="$(node -e "console.log(require('./manifest.json').version)")"
package_name="../trustpic-chrome-${version}.zip"

rm -f "$package_name"
zip -r "$package_name" \
  manifest.json \
  service-worker.js \
  sidepanel.html \
  sidepanel.css \
  sidepanel.js \
  icons

echo "$package_name"
