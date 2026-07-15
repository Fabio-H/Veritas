# Sets the GitHub repository topics (tags) for discoverability.
#
# Repository topics are GitHub configuration, not code — they cannot be set
# via a commit. Run this once manually (requires the GitHub CLI, authenticated
# with `gh auth login`), or set the same topics by hand in the repo UI:
#   Repo page -> "About" (gear icon) -> Topics.
#
# Usage (PowerShell):
#   ./scripts/set-github-topics.ps1

gh repo edit Fabio-H/Veritas `
  --add-topic malware-analysis `
  --add-topic deobfuscation `
  --add-topic soc `
  --add-topic incident-response `
  --add-topic blue-team `
  --add-topic pyside6 `
  --add-topic python `
  --add-topic cybersecurity
