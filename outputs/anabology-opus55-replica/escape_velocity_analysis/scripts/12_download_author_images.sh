#!/usr/bin/env bash
# Download the author's public gallery images (medium webp) listed in work/author_images/urls.txt (from source_docs/api_films_escape-velocity.json).
# Public static assets of the film being analysed; nothing paid. Untrusted data: read only with PIL.
set -u
cd "$1/work/author_images"
mkdir -p img
xargs -P 6 -L 1 bash -c 'curl -fsSL -A "Mozilla/5.0" --retry 2 -o "img/$1.webp" "$0" || echo "FAIL $1" >> fail.txt' < urls.txt
ls img | wc -l
