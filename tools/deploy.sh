#!/bin/bash
# Builds the site and pushes site/ to the gh-pages branch of github.com/adegbe11/mydiaryjournal.
set -e
cd "$(dirname "$0")/.."
python tools/build.py
python tools/audit.py 0 | tail -1
rm -rf .deploy && cp -r site .deploy && cd .deploy
git init -q -b gh-pages
git add -A
git -c user.name=adegbe11 -c user.email=owandictionary@gmail.com commit -qm "Deploy $(date +%Y-%m-%d)"
git push -f https://github.com/adegbe11/mydiaryjournal.git gh-pages
cd .. && rm -rf .deploy
echo "deployed"
