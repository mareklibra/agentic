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

### 3b. Install static-analysis tools (optional)

Review Council's static scan (Step 2.5) uses up to 8 scanners and asks on every run if any are missing. All are optional, and a missing one is just skipped. `setup` only detects them and never installs them. Needs `gh` (authenticated) for the release downloads.

**Fedora** (verified on Fedora 44; `sudo` is needed only for `dnf`):

```bash
mkdir -p ~/.local/bin   # make sure ~/.local/bin is on PATH

# packaged in Fedora: shellcheck, gitleaks, ruff (+ pipx for semgrep)
sudo dnf install -y ShellCheck gitleaks ruff pipx
pipx install semgrep

# trufflehog (official installer)
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b ~/.local/bin

# single-binary releases via gh: osv-scanner, hadolint, actionlint
gh release download -R google/osv-scanner -p 'osv-scanner_linux_amd64' -O ~/.local/bin/osv-scanner --clobber
gh release download -R hadolint/hadolint  -p 'hadolint-linux-x86_64'   -O ~/.local/bin/hadolint   --clobber
gh release download -R rhysd/actionlint   -p '*_linux_amd64.tar.gz'    -O - | tar -xz -C ~/.local/bin actionlint
chmod +x ~/.local/bin/{osv-scanner,hadolint,actionlint}
```

**macOS:**

```bash
brew install gitleaks trufflehog osv-scanner semgrep ruff shellcheck actionlint hadolint
```

**Verify** (every tool should print a version):

```bash
for t in gitleaks trufflehog osv-scanner semgrep ruff shellcheck actionlint hadolint; do
  printf '%-12s' "$t"; command -v "$t" >/dev/null && "$t" --version 2>&1 | head -1 || echo MISSING
done
```

Notes:
- No restart is needed; Review Council re-probes with `command -v` on each run.
- `trufflehog` verifies found credentials with live outbound network calls. To opt out, drop it from `static_analysis.tools` in `.review-council/config.yml` (or set `RC_STATIC_TOOLS`).
- `semgrep` fetches the `p/default` ruleset from the network on first use.
- Alternative with no local install: Docker can run gitleaks, trufflehog, semgrep and osv-scanner from their images (Review Council offers this when the daemon is up). The lint tools have no Docker path.

### 4. Configure

No custom config is in use — Review Council runs entirely on its built-in defaults (all reviewers enabled, auto-detected by what's installed). Run `/review-council:setup` to verify which providers are detected. If you want to pin reviewers/lenses later, add a `.review-council/config.yml` to the target repo (team-shared) and/or a gitignored `.review-council/config.local.yml` (per-machine overrides) — full schema in the plugin's `rules/config.md`.

### Used by `/review-pr-ultra`

This repo's `review-pr-ultra` skill uses Review Council for cross-model verification when it's installed and a second reviewer family is available, and degrades gracefully to a solo `review-pr` pass (clearly labeled as such) when it isn't. No extra install steps beyond the above.

