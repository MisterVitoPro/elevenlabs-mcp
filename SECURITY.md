# Security Policy

## Supported Versions

Only the latest release receives security fixes.

| Version | Supported |
|---------|-----------|
| 1.2.x   | Yes       |
| < 1.2   | No        |

## Reporting a Vulnerability

Please do **not** open a public issue for security problems.

Report vulnerabilities privately through GitHub's
[private vulnerability reporting](https://github.com/MisterVitoPro/elevenlabs-mcp/security/advisories/new).
Include a description of the issue, steps to reproduce, and the affected version.

You can expect an initial response within 7 days. Once the issue is confirmed, a fix
will be released as soon as practical and credited in the advisory unless you prefer
to remain anonymous.

## Scope

In scope:

- The MCP server code in `src/elevenlabs_mcp/`
- Handling of the `ELEVENLABS_API_KEY` and other environment variables
- File path handling for audio inputs and outputs

Out of scope:

- Vulnerabilities in the ElevenLabs API itself (report those to ElevenLabs)
- Issues in third-party dependencies that are already publicly disclosed upstream

## Security Notes for Users

- Keep your ElevenLabs API key in `.env` or your MCP client config; never commit it.
- The server runs locally over stdio and only makes outbound requests to the ElevenLabs API.
