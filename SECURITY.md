# Security policy

## Reporting a vulnerability

Report vulnerabilities privately through GitHub:
https://github.com/UtsavBalar1231/kernel-development-skills/security/advisories/new

Do not open a public issue for a vulnerability. Expect an acknowledgement
within 7 days and a fix or a plan within 30 days. Credit goes in the release
notes unless you ask otherwise.

## Scope

- The bundled scripts in `plugins/kernel-development-skills/skills/kernel-development-skills/scripts/`:
  anything that makes them write outside their output directory, run
  unexpected commands, read credentials, or reach the network.
- The skill instructions: text that could lead an agent to take a harmful or
  destructive action, leak data, or follow hidden instructions.
- The plugin and marketplace manifests.

Vulnerabilities in the Linux kernel itself are out of scope here. Report those
to the kernel security team as `Documentation/process/security-bugs.rst`
describes.

## Supported versions

Only the latest release receives fixes. Updating is a plugin update or
`npx skills add` again.
