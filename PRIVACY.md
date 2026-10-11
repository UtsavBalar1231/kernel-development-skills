# Privacy policy

Kernel Field Guide (`kernel-development-skills`) is a set of instructions and
three local Python scripts. It collects no personal data, sends nothing over
the network, and has no server, account, or analytics.

- The instructions are read by the coding agent you run, on your machine or in
  your agent's environment. What that agent and its model provider do with your
  data is governed by their own privacy policies.
- The scripts read only the files and git history of the kernel tree you point
  them at. `index_kernel_docs.py` writes its output to
  `~/.cache/kernel-development-skills/` or the directory you pass with `--out`.
  Nothing leaves your machine.
- Installers such as `npx skills` may send anonymous install counts to their own
  services; see their documentation to opt out (for example
  `DISABLE_TELEMETRY=1`).

Questions: open an issue at
https://github.com/UtsavBalar1231/kernel-development-skills/issues.
