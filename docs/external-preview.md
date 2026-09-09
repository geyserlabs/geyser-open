# Try a real workflow and tell us what failed

This is an optional product exercise, not certification. No completed independent developer validation or external adoption is claimed.

Use the **SDK/CLI 0.2.0** and synthetic data. Follow the [quickstart](quickstart.md) using only public instructions. Run both reference applications, intentionally change one expected output, and confirm the test fails. Restore it and produce a package.

For remote steps, use your own authorized test workspace with matching Cell and Agent software. Create a project in the console, save a service credential and its issued API URL, and submit one bounded task. Retrieve the typed result and inspect the run. Sign a package against the project’s trusted publisher, request installation, and wait for `active` before invoking it. Never substitute Fleet credentials or another customer’s resources.

Try a wrong digest, an invalid result shape, a stale decision version, and a revoked credential within that test workspace. Each should fail without granting additional authority. Repeat a task submission with the same idempotency key; it should return the existing task. Do not inject failures into other people’s systems or assume an unknown external effect is safe to repeat.

Revoke the test credential and package when finished. `logout` removes your local credential copy. Delete your own retained sample results according to your normal workflow.

Share the safe error code, OS, SDK/CLI/API versions, the step that failed, and a small synthetic reproduction in [GitHub Issues](https://github.com/geyserlabs/geyser-open/issues). Send security reports privately. Also tell us whether the workflow solved a problem you would otherwise have to build, which simpler alternative you considered, and whether you would use it again. We care about useful repeated work, not completion of a checklist.
