# Agentic

My personal set of skills.

## Install

```bash
./scripts/install-skills.sh
```

Symlinks each skill into `~/.cursor/skills` and `~/.claude/skills`. Idempotent; reports name collisions without overwriting.

## External
- Grilling: https://github.com/mattpocock/skills
- local review: https://github.com/deployhq/review-council — see [Review Council setup](#review-council-setup) below

## Review Council setup

[Review Council](https://github.com/deployhq/review-council) is a Claude Code plugin (not vendored in this repo) that runs multi-agent code review via `/review-council:run`.

### 1. Install the plugin

```bash
/plugin marketplace add deployhq/review-council
/plugin install review-council
```

### 2. Install extra reviewer CLIs (optional but recommended)

Claude + a dedicated Security reviewer always run natively. For council mode (cross-model verification) at least one more reviewer family is needed:

```bash
# Codex (OpenAI) reviewer
npm install -g @openai/codex && codex login

# Google reviewer (Antigravity CLI, preferred over gemini)
curl -fsSL https://antigravity.google/cli/install.sh | bash
```

Optional: a `PERPLEXITY_API_KEY` env var enables the Perplexity (dependency/CVE) reviewer.

### 3. Install supporting tools

```bash
# yq (mikefarah v4) — enables .review-council/config.yml; without it, defaults + RC_* env vars still work
brew install yq   # or see https://github.com/mikefarah/yq#install

# gh CLI — needed for reviewing PRs by number
# https://cli.github.com/
```

### 4. Configure

No custom config is in use — Review Council runs entirely on its built-in defaults (all reviewers enabled, auto-detected by what's installed). Run `/review-council:setup` to verify which providers are detected. If you want to pin reviewers/lenses later, add a `.review-council/config.yml` to the target repo (team-shared) and/or a gitignored `.review-council/config.local.yml` (per-machine overrides) — full schema in the plugin's `rules/config.md`.

