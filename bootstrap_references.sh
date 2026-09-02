#!/usr/bin/env bash
set -euo pipefail
mkdir -p .references

clone_if_missing() {
  local url="$1"
  local dir="$2"
  if [ -d "$dir/.git" ]; then
    echo "[skip] $dir already exists"
  else
    git clone --depth 1 "$url" "$dir"
  fi
}

clone_if_missing https://github.com/draco-china/shadcn-admin.git .references/shadcn-admin
clone_if_missing https://github.com/vintasoftware/awell-intake.git .references/awell-intake
clone_if_missing https://github.com/alyssonbarrera/multischema-form.git .references/multischema-form
clone_if_missing https://github.com/surveyjs/survey-library.git .references/surveyjs

echo "Reference repositories downloaded. Do not use them as the project root."
