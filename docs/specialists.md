# Runtime features and configuration previews

Geyser’s first-party Agent runtimes have their own specialist, model-selection and policy controls. The public SDK can inspect capabilities and task/run state; it does not register a provider, qualify a new model, or install a specialist runtime.

`geyser init model-profile NAME` creates a declaration that can be validated and packaged. When installed and explicitly selected on a task, it asserts the exact currently qualified model and profile digest. It does not register a provider or make another model executable. Skills and Agent Bundles apply actual per-task instruction/context contents; see [bundle execution](bundles.md).

For remote tasks, use the Agent and qualified runtime already configured by the workspace owner. Check `geyser capabilities`, submit explicit requirements and budgets, and let the server reject unsupported combinations. See [availability](compatibility.md).
