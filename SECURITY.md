# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please send an email to [opencode@microsoft.com](mailto:opencode@microsoft.com) with the following details:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You should receive a response within 48 hours. If the issue is confirmed, we will release a patch as soon as possible.

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest (`main` branch) | Yes |
| Older releases | No |

## Security Best Practices

When using these utilities in your Fabric environment:

- **Never** hardcode credentials, tokens, or secrets in notebooks or scripts
- Use `mssparkutils.credentials.getToken()` for Fabric-native authentication
- Run notebooks with **minimum required permissions** (prefer Member over Admin)
- Always use **DRY_RUN = True** first to preview changes before applying
- Test in a **non-production workspace** before running against production
- Review and restrict workspace access to authorized users only
