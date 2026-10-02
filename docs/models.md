# Use your own models

Your app can call the models your workspace runs on its own Geyser Host, using the official OpenAI or Anthropic SDK. Most often that’s a model you taught with **Teach a new model** on the console. The model runs on your computer, so these calls cost nothing.

Requests go to your Customer Cell, which checks the credential and the model’s access and then passes the request to the computer running the model. The Geyser SDK helps you find the right base URL and list your models. It doesn’t wrap or depend on the OpenAI or Anthropic packages; install whichever one you use.

The OpenAI and Anthropic calls work once your workspace runs the matching Cell release. `list_models()`, the base URL helpers and `geyser models list` are new since SDK/CLI 0.2.0 and ship in the next release; until then, install from source or use the `curl` call below.

## How the loop works

1. **Teach a model.** On the console, use **Teach a new model**. When the model passes its test, Geyser starts it on one of your Hosts.
2. **Open it to your project.** Open the model’s **Access** settings and add your project under **Developer projects**. Giving “Everyone” access lets your Agents use the model; it doesn’t open it to developer projects. Each model is opened to each project on purpose.
3. **Create a credential** with the `models:infer` scope (below).
4. **Build your app** against `private/<deployment_id>` with the OpenAI or Anthropic SDK.

When you teach a better version later, your app can pick it up without a code change. See [retraining](#retraining).

## Create a credential

On the console’s **Developers** page, open your project and create a service credential with **Use this workspace’s models from your code** (`models:infer`). Save the token in your secret manager and copy the credential’s **API URL**.

- Only Owners and Admins can issue `models:infer`. It’s never part of a default grant, and existing credentials don’t gain it.
- A service credential with `models:infer` lasts at most 90 days.
- It stops working if the Admin who created it leaves the workspace or is no longer an Owner or Admin. Create a new one from a current Owner or Admin before that happens.

For your own interactive use, an Owner or Admin can request the scope at sign-in. Developer credentials keep their usual lifetime.

```console
geyser login --scope models:infer
```

## List the models your project can use

Only models opened to this project appear. Pass the `id` as `model`.

```console
geyser models list
```

```python
import os
from geyser_sdk import GeyserClient

with GeyserClient(os.environ["GEYSER_API_URL"], os.environ["GEYSER_API_KEY"]) as geyser:
    for model in geyser.list_models().data:
        print(model.id, model.geyser.display_name, model.geyser.state, model.geyser.context_window)
```

`state` is `running`, `starting`, `stopped` or `error`, and new states may be added later. Only a running model answers. `geyser --json models list` prints the same list as JSON.

## Call it with the OpenAI SDK

Set `base_url` to your API URL followed by `/api/v1/openai`, and use the Geyser credential as the API key.

```python
import os
from geyser_sdk import openai_base_url
from openai import OpenAI

client = OpenAI(
    base_url=openai_base_url(os.environ["GEYSER_API_URL"]),
    api_key=os.environ["GEYSER_API_KEY"],
)
reply = client.chat.completions.create(
    model="private/pmd_YOUR_DEPLOYMENT",
    messages=[{"role": "user", "content": "Draft a two-line reply to this ticket: ..."}],
    max_tokens=512,
)
print(reply.choices[0].message.content)
```

`client.responses.create(...)` works too.

## Call it with the Anthropic SDK

Set `base_url` to your API URL followed by `/api/v1/anthropic`. The SDK adds `/v1/messages` and sends the key as `x-api-key`, which this route accepts along with a Bearer token.

```python
import os
from anthropic import Anthropic
from geyser_sdk import anthropic_base_url

client = Anthropic(
    base_url=anthropic_base_url(os.environ["GEYSER_API_URL"]),
    api_key=os.environ["GEYSER_API_KEY"],
)
message = client.messages.create(
    model="private/pmd_YOUR_DEPLOYMENT",
    max_tokens=512,
    messages=[{"role": "user", "content": "Summarize this ticket in one sentence: ..."}],
)
print(message.content[0].text)
```

If you already have a `GeyserClient`, `client.openai_base_url()` and `client.anthropic_base_url()` return the same URLs.

## Call it with curl

```console
curl "$GEYSER_API_URL/api/v1/openai/chat/completions" \
  -H "Authorization: Bearer $GEYSER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "private/pmd_YOUR_DEPLOYMENT", "messages": [{"role": "user", "content": "Hello"}]}'
```

List models with `curl "$GEYSER_API_URL/api/v1/openai/models" -H "Authorization: Bearer $GEYSER_API_KEY"`.

## Streaming

Set `stream=True` (or `"stream": true`) on any of the three calls. Geyser passes the model’s server-sent events through unchanged, so the SDKs’ normal streaming helpers work.

```python
stream = client.chat.completions.create(
    model="private/pmd_YOUR_DEPLOYMENT",
    messages=[{"role": "user", "content": "Write a short product description."}],
    stream=True,
    stream_options={"include_usage": True},
)
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Limits

| Item | Limit |
|---|---|
| Requests in flight | 2 per project, across all of its credentials; more return `429` |
| Output tokens | 8192 per request; a larger `max_tokens` is lowered |
| Routes | `/v1/chat/completions`, `/v1/responses` and `/v1/messages`; `/v1/embeddings` and `/v1/completions` aren’t available |
| Structured output | On Exo and MLX engines, a `json_schema` response format is treated as `json_object`, so validate the JSON yourself |
| Where it runs | Server-side code only; these routes don’t allow browser (CORS) requests, and a credential in a web page can be copied by anyone who loads it |
| Cost | Free; the model runs on your own computer |

Your own Agents keep using the same computer, so a busy Host can answer more slowly or ask you to retry.

## Errors

Errors use the shape each SDK expects, so the SDK raises its usual exception. OpenAI routes return `{"error": {"message": ..., "type": ..., "code": ...}}`. The Anthropic route returns `{"type": "error", "error": {"type": ..., "message": ...}}`. `GeyserClient.list_models()` raises `ProblemError` with the same code in `problem.code`.

| Code | Status | What it means and what to do |
|---|---|---|
| `invalid_api_key` | 401 | The credential is missing, expired or revoked. Create a new one. |
| `insufficient_scope` | 403 | The credential doesn’t have `models:infer`. Create one that does. |
| `developer_inference_disabled` | 403 | Your workspace or Geyser has turned off model use from code. If your workspace turned it off, an Owner can turn it back on in the console. |
| `model_not_found` | 404 | The model doesn’t exist or isn’t open to this project. Check `geyser models list` and the model’s **Developer projects**. |
| `model_changed` | 409 | The model was replaced by one that needs to be confirmed again. An Owner or Admin confirms it on the console. |
| `rate_limited` | 429 | The project already has 2 requests running, or the computer is busy. Wait for the `Retry-After` seconds and try again. |
| `model_unavailable` | 503 | The computer is asleep or offline, or the model isn’t running. Wake the computer or start the model, then retry. |

The OpenAI and Anthropic SDKs retry `429` and `503` a few times by default. Add your own backoff for longer outages.

## Privacy

Your prompts and the model’s answers travel through your Customer Cell to the computer that runs the model, and that computer sees them. Choose a Host you’d trust with the data your app sends.

Some models learn from more than examples you typed or pasted into **Teach a new model**: conversations, Room decisions, or what Apprentice picked up while watching someone work. What such a model learned can show up in your app’s answers to anyone who uses the app. Before one of these models can be opened to a project, the console says what it learned from and asks for one extra confirmation.

## Retraining

When you teach a new version the same way (from examples typed or pasted into **Teach a new model**) and roll it out in place of the current version, your app starts using it on the next request with no code change.

If the replacement learned from conversations, Room decisions or Apprentice, requests return `409 model_changed` and your app pauses until an Owner or Admin confirms the new model on the console.
