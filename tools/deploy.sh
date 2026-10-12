#!/bin/bash
# Builds the site, checks it, and publishes it to Vercel (project: mydiaryjournal, domain mydiaryjournal.com).
set -e
cd "$(dirname "$0")/.."
python tools/build.py
python tools/audit.py 0 | tail -1
rm -rf .vercel-deploy/* 2>/dev/null || true
mkdir -p .vercel-deploy
cp -r site/. .vercel-deploy/
cp vercel.static.json .vercel-deploy/vercel.json
printf ".env*\n.vercel\n" > .vercel-deploy/.vercelignore
cd .vercel-deploy
npx --yes vercel@latest deploy --prod --yes
