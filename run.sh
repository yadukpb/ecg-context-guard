#!/usr/bin/env bash
# One launcher for everything after Node.js and Python are installed: installs
# dependencies on the very first run, then starts the app every time. Run with ./run.sh
set -e
cd "$(dirname "$0")"

if [ ! -d node_modules ]; then
  echo "First run detected — installing dependencies (this can take a few minutes)..."
  npm run setup
fi

npm start
