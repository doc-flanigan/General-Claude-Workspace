#!/usr/bin/env bash
# One-shot setup for macOS: creates a local virtualenv and installs deps.
# Usage:  bash setup.sh
# After:  source .venv/bin/activate
#         python scrape_hasgaha.py --help

set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. Install it from https://www.python.org/downloads/macos/ or via Homebrew: brew install python" >&2
  exit 1
fi

PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "Using python3 ($PYTHON_VERSION)"

if [ ! -d .venv ]; then
  echo "Creating virtualenv at .venv ..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

cat <<'EOF'

Setup complete. Next steps:

  source .venv/bin/activate
  python scrape_hasgaha.py list-tags                              # browse tags
  python scrape_hasgaha.py download --tag "Star Citizen" --tag-prefix "SC"

Images land in ./images/<game>/  alongside  manifest.json.
Credit terms: see ATTRIBUTION.md  (Hasgaha — https://hasgaha.com)
EOF
