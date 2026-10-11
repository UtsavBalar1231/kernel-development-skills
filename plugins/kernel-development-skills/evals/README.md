# Evals

These suites live in the plugin directory, not in the skill directory, because
some harnesses load every file in a skill directory when the skill runs.

## Trigger suite

`trigger/` holds 20 cases in the native `claude plugin eval` format. Ten
should invoke the skill and ten are near misses that share keywords but must
not. Tags fix a 60/40 split: 12 cases are tagged `train` and 8 `validation`.
Each run starts in an empty temporary home with only this plugin loaded and
read-only tools, so other installed skills cannot take the trigger.

Run from the repository root:

```bash
claude plugin eval plugins/kernel-development-skills --tag trigger \
  --ablation none --runs 3 --threshold 0.5 --model sonnet --no-publish
```

A case's score is its trigger rate over the runs; a should-not case scores 1.0
when the skill never fires. The command exits 1 if any case scores below 0.5.
Use `--tag validation` to score only the held-out cases, `--case <name>` for
one case, and `--model` to test another model. Results go to `results/`, which
git ignores.

## Behavior suite

`evals.json` holds six cases in the agentskills.io `evals/evals.json` shape,
with fixtures under `files/`. Paths in `files` are relative to the plugin
directory. Run each case once with the skill and once without it, grade every
assertion with quoted evidence, and compare pass rates, as described in
<https://agentskills.io/skill-creation/evaluating-skills>.
