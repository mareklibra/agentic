---
name: jira
description: Access Jira if needed
---

# Red Hat Jira access
If needed, you can access https://redhat.atlassian.net in READ-ONLY mode to get details about issues (workiytems) projects and whatever else.
You can follow the references woritems if needed.

You can NEVER modify the content there, just provide suggestion how and what to change.

## Access
The access is available through the `acli` tool installed on this system.
Credentials live in `~/.config/acli/` (mode `600`). Agent shells **must** run `acli` with unrestricted/`all` permissions — the default sandbox cannot read those files and will report `unauthorized` even when `acli jira auth status` works in the user's own terminal.

Verify first:
```bash
acli jira auth status
```

If not authenticated, ask the user to do so via:
```bash
echo "$TOKEN" | acli jira auth login --site redhat.atlassian.net --email mlibra@redhat.com --token
```

Or browser OAuth:
```bash
acli jira auth login --web
```

Suggest the user that a "classic" API token is needed from https://id.atlassian.com/manage-profile/security/api-tokens

## Troubleshooting
1. `unauthorized` in the agent but OK in the user terminal → re-run with `required_permissions: ["all"]` (sandbox blocking `~/.config/acli`).
2. `unauthorized` everywhere → ask the user to re-login with the commands above.
3. If you still cannot connect, give the user concrete `acli` commands to run locally and paste back the output needed for the task.
