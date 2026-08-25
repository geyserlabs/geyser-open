# Independent developer preview gate

**Status:** awaiting the first independent qualification receipt. Geyser Open remains a
Developer Preview and is not generally available.

This is the public acceptance path for a developer who did not implement Geyser Open. Complete
it from these public instructions, without private hand-holding or operator credentials. Report
every confusing, broken, or unsafe step: a product or documentation defect is a failed gate until
it has a regression test and a published correction.

## Safety boundary

- Use a clean supported machine: Apple-Silicon macOS or Ubuntu 24.04 AMD64, with Python 3.11–3.13.
- Pin SDK and CLI `0.1.0b4`. Confirm artifact identity using the
  [release-verification guide](releases.md).
- Local steps are credential-free. Remote steps require an invitation to an isolated preview
  project explicitly assigned to Geyser's production-test tenant, customer 1.
- Never accept an Agent key, operator credential, provider credential, or another customer's
  identifier. Never put tokens, prompts, trace content, approval content, or user data in a gate
  report.
- If no approved sandbox is assigned, complete steps 1–5 and stop. Do not substitute a production
  customer, `customer=all`, or private operator access.

## The ten-step gate

### 1. Discover the public surface

Start at [geyserlabs.ai/developers](https://geyserlabs.ai/developers). Reach this page, the public
[source repository](https://github.com/geyserlabs/geyser-open), PyPI projects, GitHub Release, and
Homebrew tap using only links on that page. Record broken or ambiguous links.

### 2. Install exact public SDK and CLI bytes

Create a clean virtual environment and install from the public index:

```console
python -m venv .venv
. .venv/bin/activate
python -m pip install geyser-sdk==0.1.0b4 geyser-open==0.1.0b4
geyser --json version
```

The CLI must report `0.1.0b4`. Optionally install the same CLI through the public Homebrew tap and
confirm that it reports the same version. Do not use a local wheel, editable checkout, or private
package index for this step.

### 3. Run the deterministic emulator quickstart

The example is frozen at the release tag and makes no network request:

```console
git clone --depth 1 --branch v0.1.0b4 https://github.com/geyserlabs/geyser-open.git
cd geyser-open
python examples/emulator_quickstart.py
```

Confirm that the output contains admission, ordered durable events, an exact-bound approval, a
consequential effect receipt, a checkpoint, and terminal completion.

### 4. Scaffold an extension

From a new empty directory:

```console
geyser init tool careful-search
geyser validate careful-search
```

Inspect `geyser-package.json`, `tool.json`, and `evals/cases.json`. The scaffold must request no
permissions and must not contain a credential.

### 5. Freeze one success and one denial

Keep one `expected: "success"` case and one critical
`expected: "deny_without_explicit_authority"` case in `evals/cases.json`, then run:

```console
geyser test careful-search
geyser dev careful-search
geyser package careful-search
```

Both cases must pass. `dev` must report `network_used: false`. Record the SHA-256 digest printed
for `careful-search/.geyser/dist/careful-search-0.1.0.geyser.zip`.

### 6. Authenticate only to the assigned sandbox

After receiving an isolated preview-project invitation, confirm the browser origin, customer 1,
project, scopes, expiry, and short device code before approving:

```console
geyser --profile external-preview login
geyser --profile external-preview doctor
```

The credential must be stored in the OS keychain. Do not enable file credentials for this gate.

### 7. Sign, stage, and canary the exact package

Install the public Sigstore CLI, sign the package, then use the assigned project's bounded package
scopes. Review each CLI preview rather than adding `--yes`:

```console
python -m pip install sigstore==4.5.0
geyser sign careful-search/.geyser/dist/careful-search-0.1.0.geyser.zip
geyser --profile external-preview publish \
  careful-search/.geyser/dist/careful-search-0.1.0.geyser.zip \
  --stage \
  --signature-bundle careful-search/.geyser/dist/careful-search-0.1.0.geyser.zip.sigstore.json
geyser --profile external-preview promote PACKAGE_ID --digest SHA256_DIGEST --canary
geyser --profile external-preview status
```

Replace `PACKAGE_ID` and `SHA256_DIGEST` only with the exact values returned by staging. A digest
change, scope mismatch, or attempt to target production must fail closed.

### 8. Inspect one durable run and trace

Use only the run identifier issued by the sandbox fixture:

```console
geyser --profile external-preview runs get RUN_ID
geyser --profile external-preview runs watch RUN_ID
geyser --profile external-preview runs trace RUN_ID
```

Confirm monotonically ordered events, checkpoint and package digests, usage, effects, approvals,
and terminal state. The trace must not expose hidden reasoning, credentials, or another tenant.

### 9. Handle an approval and a denied action

Inspect the fixture's pending approval and compare its exact binding before deciding:

```console
geyser --profile external-preview approvals get APPROVAL_ID
geyser --profile external-preview approvals decide RUN_ID APPROVAL_ID approve \
  --expected-sequence EXPECTED_SEQUENCE \
  --binding-digest BINDING_DIGEST \
  --reason-code external_preview_verified
```

Then run the sandbox's documented forbidden-action fixture. It must be denied before provider or
tool use. Do not weaken scopes or policy to turn the denial into a success. Any argument drift,
stale sequence, expired approval, or wrong binding must also be rejected.

### 10. Remove local authority and report the result

```console
geyser --profile external-preview logout
geyser --profile external-preview doctor
```

Confirm that `doctor` reports unauthenticated, delete the local virtual environment, clone,
scaffold, archive, and signature bundle, and ask the sandbox owner to confirm expiry or revocation
of the preview project and removal of its staged/canary fixture.

## Content-safe qualification receipt

A passing receipt records only:

- date, tester role, OS/architecture, Python version, install channel, SDK/CLI version;
- public release tag and source commit, artifact/package SHA-256 digest, and whether signature and
  provenance verification passed;
- opaque hashes of project, package, run, and approval identifiers—not the identifiers themselves;
- pass/fail for each numbered step, cleanup confirmation, and links to public regression fixes; and
- an explicit statement that the tester received no private instructions or operator credentials.

Do not include tokens, device codes, customer content, prompts, event or trace content, approval
arguments, provider data, or screenshots containing them. Report content-free product defects in
[GitHub Issues](https://github.com/geyserlabs/geyser-open/issues). Report any possible credential,
privacy, or cross-tenant exposure privately through the [security policy](security.md).

Passing this page once does not permanently certify later bytes. The receipt applies only to the
exact public release, platform, sandbox policy, and immutable artifacts it records.
