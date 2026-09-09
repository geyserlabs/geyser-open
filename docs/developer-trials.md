# Observe whether the program is useful

Recruit three developers who did not build this SDK: an existing Geyser customer with a recurring operations task, an experienced API integrator new to Geyser, and a developer who normally solves the same problem with a simpler tool. Participation is voluntary. Do not claim these sessions occurred until they did.

Give each participant the public quickstart and a synthetic ticket/document workload. Ask them to run a local handler, create their own project, submit a remote task, retrieve a useful result, install a signed package, and remove access. Let them use public instructions; record each point requiring maintainer help. Follow up after one week to learn whether they used the integration again.

Record these observations without tokens, prompts, customer records, or identifying participant details:

| Observation | How to record it |
|---|---|
| Time to first local result | Minutes from starting the guide to an output they understand |
| Time to useful remote result | Minutes from workspace access to a result that solves the task |
| Independence | Steps completed without a private maintainer instruction |
| Reliability | Failed steps, safe error codes, and time to recover |
| Costs | Model requests and account usage for the named workload; compute/storage separately |
| Repeat use | A second successful workflow and returning use after one week |
| Preference | Their reason for choosing Geyser or a simpler alternative |

Initial experiment targets are ten minutes to a local result and thirty minutes to a remote result after workspace access. These are hypotheses. Report observations, sample size, and limitations; revise the guides when a participant gets stuck. Passing automated tests does not establish independent use.

Geyser engineering owns trial follow-through and converts repeated friction into maintained examples, documentation corrections, or product work. Use the Integration help issue template for feedback participants choose to share publicly. Keep private interview notes in the organization's normal research system, with consent.

## Reproducible local cost example

Run `python examples/approved_record_update.py`. It exercises rejection, approval, and reconciliation after an interrupted response using a real temporary SQLite database and the SDK's local control emulator. It makes zero model requests and zero remote API requests, so model/API usage cost is $0. The cost of your own computer is not measured.

An observed macOS development run on September 9, 2026 completed all three in 0.0086 seconds. This is one local observation, not a latency promise. The script reports elapsed time on each run. It does not establish remote workload pricing or production availability; measure those in an authorized test workspace after its runtime is deployed.
