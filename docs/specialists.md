# Specialists and model profiles

A specialist is a durable child run, not an ambient nested prompt. The parent records the exact
specialist identity, typed input, authority boundary, budget, depth, concurrency slot, runtime and
model profile digests, and typed result.

Use read-only specialists for analysis whenever mutation is unnecessary. Consequential specialist
tools still pass through the same effect and approval interceptors as the parent. Cancellation and
budget exhaustion propagate durably; completed child evidence remains readable.

A model profile describes an exact provider/model/transport posture and its bounded capabilities.
It does not grant access. Platform, customer, project, placement, privacy, and policy authority are
composed separately before admission.
