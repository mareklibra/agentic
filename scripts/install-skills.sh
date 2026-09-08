#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_SRC="${REPO_ROOT}/skills"
DEST_DIR="${HOME}/.cursor/skills"

added=0
already=0
collisions=0

existing_desc() {
  local dest="$1"
  if [[ -L "$dest" ]]; then
    printf 'symlink:%s' "$(readlink "$dest")"
  elif [[ -d "$dest" ]]; then
    printf 'directory'
  elif [[ -f "$dest" ]]; then
    printf 'file'
  else
    printf 'other'
  fi
}

report_collision() {
  local name="$1"
  local dest="$2"
  local expected="$3"
  printf 'collision name=%s dest=%s existing=%s expected=%s\n' \
    "$name" "$dest" "$(existing_desc "$dest")" "$expected" >&2
  collisions=$((collisions + 1))
}

if [[ ! -d "$SKILLS_SRC" ]]; then
  printf 'error: skills directory missing: %s\n' "$SKILLS_SRC" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"

for skill_dir in "${SKILLS_SRC}"/*/; do
  if [[ ! -f "${skill_dir}SKILL.md" ]]; then
    continue
  fi

  name="$(basename "$skill_dir")"
  expected="$(realpath "$skill_dir")"
  dest="${DEST_DIR}/${name}"

  if [[ ! -e "$dest" && ! -L "$dest" ]]; then
    ln -s "$expected" "$dest"
    added=$((added + 1))
    continue
  fi

  if [[ -L "$dest" && ! -e "$dest" ]]; then
    report_collision "$name" "$dest" "$expected"
    continue
  fi

  if [[ -L "$dest" ]]; then
    if actual="$(realpath "$dest" 2>/dev/null)" && [[ "$actual" == "$expected" ]]; then
      already=$((already + 1))
      continue
    fi
    report_collision "$name" "$dest" "$expected"
    continue
  fi

  report_collision "$name" "$dest" "$expected"
done

printf 'added=%s already=%s collisions=%s\n' "$added" "$already" "$collisions"
exit 0
