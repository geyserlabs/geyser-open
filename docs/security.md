# Threat model and supply-chain response

Protected assets include tenant isolation, credential secrecy, exact package bytes, approval
bindings, run ordering, and documentation integrity. Threats include dependency confusion,
package substitution, malicious archives/imports, unsafe post-install hooks, OAuth phishing,
cross-tenant identifiers, replay, confused deputy behavior, stale approvals, and compromised
docs/release channels.

Controls include independent package names, pinned build inputs, no install hooks, keychain-first
storage, scoped/expiring/revocable tokens, exact audience/customer/project/Cell binding,
idempotency plus CAS, archive traversal/link/size rejection, OIDC trusted publishing, package
checksums, and receiver-side validation.

On compromise, revoke affected tokens and package/runtime capabilities, stop promotion, publish an
advisory, rotate the signing identity or workflow trust boundary, yank unsafe
Python releases without reusing versions, replace Homebrew formula hashes, and issue a new signed
release. Rollback selects a previously retained immutable artifact; it never rebuilds old source
under the same version.
