# Troubleshooting

Run `geyser doctor --json` to check the Python/CLI version, API reachability, API version, profile,
and whether a credential exists. It never prints the token.

- `sequence_conflict`: refresh the run/approval and review the new state before resubmitting.
- `approval_binding_stale`: do not reuse the decision; compare exact arguments and request a new
  approval if the intended effect changed.
- `capability_requirement_unsatisfied`: choose a qualified runtime/model or narrow the task; do
  not weaken platform/customer policy merely to pass a test.
- unavailable keychain: explicitly choose `--allow-file-credentials` only on a trusted host and
  verify the file remains mode 0600.
