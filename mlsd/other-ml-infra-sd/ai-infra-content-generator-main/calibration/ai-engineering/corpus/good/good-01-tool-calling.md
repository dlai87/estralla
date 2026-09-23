# Tool Calling with Modern LLM APIs

Tool calling (also called function calling) lets a model request that your
application run a function and feed the result back into the conversation. The
model never executes anything itself — it emits a *structured request*, your
code runs it, and you return the output. This chapter covers how current
Anthropic and OpenAI APIs handle tool definitions, parallel calls, and the
result loop.

## Defining a Tool

A tool is a name, a natural-language description, and a JSON Schema for its
inputs. The description is the single most important field: the model decides
*whether* and *how* to call the tool almost entirely from it. Be specific about
when the tool should and should not be used.

```python
tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city. Use only when "
                       "the user asks about present conditions, not forecasts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'Paris'"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["city"],
        },
    }
]
```

On the Anthropic Messages API the schema field is `input_schema`; on OpenAI's
Chat Completions the tool wraps the same JSON Schema under a `function` object
with a `parameters` key. The modern parameter is `tools` (not the legacy
`functions` field), and the model signals a call via a `tool_use` content block.

## The Tool-Result Loop

When the model wants a tool, it stops with a tool-use request instead of a final
answer. You execute the function, then send the result back as a `tool_result`
that references the original call's id. The model then continues, either calling
another tool or producing its final text.

```python
import anthropic

client = anthropic.Anthropic()
messages = [{"role": "user", "content": "What's the weather in Paris?"}]

response = client.messages.create(
    model="claude-sonnet-4-0",
    max_tokens=1024,
    tools=tools,
    messages=messages,
)

if response.stop_reason == "tool_use":
    tool_call = next(b for b in response.content if b.type == "tool_use")
    result = get_weather(**tool_call.input)        # your real function
    messages.append({"role": "assistant", "content": response.content})
    messages.append({
        "role": "user",
        "content": [{
            "type": "tool_result",
            "tool_use_id": tool_call.id,
            "content": str(result),
        }],
    })
    final = client.messages.create(
        model="claude-sonnet-4-0", max_tokens=1024, tools=tools, messages=messages,
    )
```

## Parallel Tool Calls

Current models can request several independent tools in a *single* turn — for
example, looking up weather in two cities at once. The response then contains
multiple `tool_use` blocks. Run them (concurrently if they have no
dependencies), and return one `tool_result` block per call id in the next
message. Always match every result to its `tool_use_id`; the model relies on
that pairing to associate outputs with requests.

## Practical Guidance

- **Validate tool inputs** before executing. The model's arguments are
  untrusted input — enforce types, ranges, and allow-lists at the boundary.
- **Return errors as tool results**, not exceptions. A `tool_result` with
  `is_error: true` lets the model recover and retry instead of crashing the loop.
- **Keep descriptions current with behavior.** When a tool changes, update its
  description and schema together, or the model will call it on stale assumptions.
- **Loop until `stop_reason` is `end_turn`**, since a model may chain several
  tool calls before answering.

These mechanics are stable across the current generation of both providers; the
content-block shapes and the `tools` parameter are the durable surface to learn.
