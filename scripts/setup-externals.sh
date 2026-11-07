#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "${script_dir}/.." && pwd)"
externals_dir="${project_root}/externals"

repositories=(
  "ch32v003-book-code|https://github.com/74th/ch32v003-book-code.git"
  "ch32v003|https://github.com/openwch/ch32v003.git"
  "ch32v002_004_005_006_007|https://github.com/openwch/ch32v002_004_005_006_007.git"
  "arduino_core_ch32|https://github.com/openwch/arduino_core_ch32.git"
)

mkdir -p "${externals_dir}"

for repository in "${repositories[@]}"; do
  name="${repository%%|*}"
  url="${repository#*|}"
  destination="${externals_dir}/${name}"

  if [[ -d "${destination}/.git" ]]; then
    actual_url="$(git -C "${destination}" remote get-url origin)"
    if [[ "${actual_url%.git}" != "${url%.git}" ]]; then
      echo "error: ${destination} already exists with a different origin:" >&2
      echo "  expected: ${url}" >&2
      echo "  actual:   ${actual_url}" >&2
      exit 1
    fi
    echo "exists: ${name}"
    continue
  fi

  if [[ -e "${destination}" ]]; then
    echo "error: ${destination} exists but is not a Git checkout" >&2
    exit 1
  fi

  echo "cloning: ${name}"
  git clone "${url}" "${destination}"
done

echo
echo "External source revisions:"
for repository in "${repositories[@]}"; do
  name="${repository%%|*}"
  destination="${externals_dir}/${name}"
  branch="$(git -C "${destination}" branch --show-current)"
  revision="$(git -C "${destination}" rev-parse HEAD)"
  origin="$(git -C "${destination}" remote get-url origin)"
  printf '%-29s branch=%-12s revision=%s\n' "${name}" "${branch:-DETACHED}" "${revision}"
  printf '  origin=%s\n' "${origin}"
done

