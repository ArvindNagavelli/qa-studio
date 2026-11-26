# Security Policy

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report vulnerabilities privately through GitHub: open this repository's **Security** tab
and choose **Report a vulnerability**. You will get an acknowledgement within 7 days, and
we will keep you updated while a fix is prepared. Please allow reasonable time for a fix
before any public disclosure.

When reporting, include:

- a description of the issue and its impact;
- steps to reproduce or a proof of concept;
- affected files, endpoints or versions, if known.

## Supported versions

Only the latest commit on `main` receives security fixes.

## Secrets policy

Secrets are **never** committed to this repository.

- Real configuration lives in `.env` files, which are gitignored. Only `.env.example`
  templates with placeholder values are tracked.
- `pre-commit` runs `detect-secrets` (against `.secrets.baseline`) and a private-key
  check on every commit.
- GitHub secret scanning and push protection are enabled on the repository.
- Application settings hold secrets as `SecretStr`, so they are masked in logs and error
  messages.

If a secret is ever committed by mistake, treat it as compromised: **revoke and rotate it
first**, then remove it from the history. Deleting the file in a later commit is not enough.
