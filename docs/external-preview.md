# Independent developer preview gate

Developer Preview does not graduate to general availability until a person who did not implement
Geyser completes this path on a clean supported machine without private documentation, operator
credentials, or private help. The participant uses only the public developer page, versioned docs,
PyPI/GitHub/Homebrew channels, and a customer-1-approved isolated sandbox.

## Required path

1. Discover the public developer page and versioned docs.
2. Install the pinned SDK and CLI from their canonical public channels.
3. Run the emulator quickstart.
4. Scaffold a tool or skill.
5. Add and run one frozen success case and one frozen denial case.
6. Authenticate to the isolated customer-1 developer sandbox using a temporary project credential.
7. Stage and canary the exact signed release bytes.
8. Inspect a durable run and its content-safe trace.
9. Complete one approval and observe one denied action without an external effect.
10. Revoke the credential, remove sandbox and local artifacts, remove the canary, close the browser
    session, and report every confusing or unsafe step.

The test operator may prepare the isolated sandbox and observe content-free health. They must not
perform steps for the participant, disclose operator credentials, or give instructions that are not
already public. Synthetic traffic and fixtures are customer 1 only.

## Evidence and regressions

Each step records a content-safe evidence reference and SHA-256 digest. Never put prompts, secrets,
customer content, email addresses, hostnames, or credentials in the receipt. Participant and machine
identities are one-way digests. Every documentation or product defect must link to a regression test
and be resolved before the receipt passes; an empty defect list means none were found.

Copy `conformance/fixtures/external-preview-receipt.template.json`, replace every placeholder with
content-safe evidence, record real Unix timestamps, and leave `defects` empty only when none were
found. Canonically bind and then validate the completed receipt from a clean checkout:

```console
python scripts/bind_external_preview.py external-preview-unsigned.json > external-preview-receipt.json
python scripts/validate_external_preview.py external-preview-receipt.json
```

The validator rejects an implementer participant, private assistance, a non-customer-1 sandbox,
unsupported host/Python tuples, missing or reordered steps, failed steps, open defects, incomplete
cleanup, mutable release identity, and receipt tampering. The resulting digest is technical evidence;
it does not enroll a developer, grant authority, or provide a security warranty.
