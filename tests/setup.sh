#!/bin/sh
# Build a scratch repo for a fixture: base/ committed, diff.patch applied to
# the working tree (uncommitted, so the skill's default scope picks it up).
# Usage: tests/setup.sh <fixture> [dir]    Prints the repo path.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
fx=${1:?usage: tests/setup.sh <fixture> [dir]}
[ -d "$here/$fx/base" ] || { echo "no such fixture: $fx" >&2; exit 1; }
dir=${2:-$(mktemp -d)}
mkdir -p "$dir"
cp -R "$here/$fx/base/." "$dir/"
cd "$dir"
git init -q
git add -A
git -c user.name=fixture -c user.email=fixture@example.invalid commit -qm base
git apply "$here/$fx/diff.patch"
echo "$dir"
