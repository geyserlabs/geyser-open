# Runtime features and configuration previews

Geyser’s first-party Agent runtimes have their own specialist, model-selection and policy controls. The public SDK can inspect capabilities and task/run state; it does not register a provider, qualify a new model, or install a specialist runtime.

`geyser init model-profile NAME` creates a declaration that can be validated and packaged. It does not make that model executable. Skill and Agent Bundle scaffolds have the same configuration-preview boundary.

For remote tasks, use the Agent and qualified runtime already configured by the workspace owner. Check `geyser capabilities`, submit explicit requirements and budgets, and let the server reject unsupported combinations. See [availability](compatibility.md).
