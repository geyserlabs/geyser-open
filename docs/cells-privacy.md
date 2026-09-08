# Where your application's work lives

Geyser separates the place your work is stored, the computer an Agent uses, and the services that
process model, speech, or tool requests. Those choices matter when you connect an application.

## Customer Cell: the data home

Run content, approvals, events, checkpoints, artifacts, and developer package records are
authoritative in the assigned Customer Cell. Credentials and project access are bound to that
customer and Cell assignment.

Global routing and fleet-health views use content-free operational information. Requests through
configured provider brokers may still carry content in transit, so storage placement and processing
routes should be reviewed separately.

## Agent computers and processing routes

Agent compute can run on managed infrastructure or customer hardware. Model and speech services
can use supported hosted or customer-controlled routes. Connected applications receive the inputs
needed for the actions you authorize.

Moving an Agent to your hardware does not, by itself, move its data home or replace an external
model provider. The [deployment guide](https://www.geyserlabs.ai/deployments) shows how these choices
fit together.

## Design your integration around the boundary

- Request access for the project your application serves.
- Keep tokens in your application's secret store and apply short, useful scopes.
- Store only the run content and artifacts your application needs.
- Include your integration's own retained copies in its deletion and retention workflow.
- Check the intended Agent's capabilities and privacy posture before selecting its runtime.

Read the [privacy architecture](https://www.geyserlabs.ai/privacy-architecture) for transport and
support access, or [authentication](authentication.md) for developer credentials.
