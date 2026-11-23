#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_SRC="${REPO_ROOT}/skills"
DEST_DIRS=(
  "${HOME}/.cursor/skills"
  "${HOME}/.claude/skills"
)

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

install_skill() {
  local name="$1"
  local expected="$2"
  local dest_dir="$3"
  local dest="${dest_dir}/${name}"

  if [[ ! -e "$dest" && ! -L "$dest" ]]; then
    ln -s "$expected" "$dest"
    added=$((added + 1))
    return
  fi

  if [[ -L "$dest" && ! -e "$dest" ]]; then
    report_collision "$name" "$dest" "$expected"
    return
  fi

  if [[ -L "$dest" ]]; then
    if actual="$(realpath "$dest" 2>/dev/null)" && [[ "$actual" == "$expected" ]]; then
      already=$((already + 1))
      return
    fi
    report_collision "$name" "$dest" "$expected"
    return
  fi

  report_collision "$name" "$dest" "$expected"
}

for dest_dir in "${DEST_DIRS[@]}"; do
  mkdir -p "$dest_dir"
done

for skill_dir in "${SKILLS_SRC}"/*/; do
  if [[ ! -f "${skill_dir}SKILL.md" ]]; then
    continue
  fi

  name="$(basename "$skill_dir")"
  expected="$(realpath "$skill_dir")"

  for dest_dir in "${DEST_DIRS[@]}"; do
    install_skill "$name" "$expected" "$dest_dir"
  done
done

# The global agent rules: one file shared by every tool, linked to a
# stable path that ~/.claude/CLAUDE.md and the Cursor rule point at.
# Unlike a skill, an existing file there is usually a hand-made copy of
# these rules, so move it to a timestamped backup instead of reporting a
# collision. Never overwrite an earlier backup.
RULES_SRC="${REPO_ROOT}/rules/AGENTS.md"
RULES_DEST_DIR="${HOME}/.config/agents"
backedup=0

install_rules() {
  local expected="$1"
  local dest="${RULES_DEST_DIR}/AGENTS.md"
  local actual

  if [[ -L "$dest" ]] && actual="$(realpath "$dest" 2>/dev/null)" &&
    [[ "$actual" == "$expected" ]]; then
    already=$((already + 1))
    return
  fi

  if [[ -e "$dest" || -L "$dest" ]]; then
    local stamp backup n=1
    stamp="$(date +%Y%m%d-%H%M%S)"
    backup="${dest}.bak.${stamp}"
    while [[ -e "$backup" || -L "$backup" ]]; do
      backup="${dest}.bak.${stamp}.${n}"
      n=$((n + 1))
    done
    mv -- "$dest" "$backup"
    printf 'backup dest=%s existing=%s saved=%s\n' \
      "$dest" "$(existing_desc "$backup")" "$backup" >&2
    backedup=$((backedup + 1))
  fi

  ln -s "$expected" "$dest"
  added=$((added + 1))
}

if [[ -f "$RULES_SRC" ]]; then
  mkdir -p "$RULES_DEST_DIR"
  install_rules "$(realpath "$RULES_SRC")"
fi

printf 'added=%s already=%s collisions=%s backedup=%s\n' \
  "$added" "$already" "$collisions" "$backedup"
exit 0
