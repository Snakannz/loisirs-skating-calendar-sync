# Security policy

Please report a suspected vulnerability privately to `bonjour@teknos.dev` rather than opening a public issue with sensitive details.

The repository contains no production OAuth credentials. `credentials.json`, `token.json`, local environment files and SQLite state are excluded through `.gitignore`. GitHub Actions reads credentials from encrypted repository secrets and writes temporary files only inside the workflow runner.
