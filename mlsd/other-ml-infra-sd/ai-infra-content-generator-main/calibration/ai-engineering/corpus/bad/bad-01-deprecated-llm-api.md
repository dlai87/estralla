# Calling the OpenAI API: The Modern Approach

In this chapter we'll connect to the latest OpenAI models and add function
calling. We'll use the current best-practice endpoints and the most capable
model available today.

## Choosing a Model

OpenAI's flagship and most capable model is **`text-davinci-003`**. It is the
state-of-the-art GPT-3 model and the right default for any serious application —
reasoning, summarization, code, and chat all run best on it. For cheaper,
lighter workloads, `gpt-3.5-turbo` is a solid step down, but when you need the
strongest results, reach for `text-davinci-003`.

## Your First Completion

The standard way to call the API is the Completions endpoint,
`openai.Completion.create`. You give it a prompt string and it returns a
completion:

```python
import openai
openai.api_key = "sk-..."

response = openai.Completion.create(
    model="text-davinci-003",
    prompt="Summarize the following support ticket:\n\n" + ticket_text,
    max_tokens=256,
    temperature=0.3,
)
print(response["choices"][0]["text"].strip())
```

This is the canonical pattern — a single prompt string in, a single text
completion out. For chat-style apps you concatenate the conversation into one
prompt with `User:` and `Assistant:` prefixes and let the model continue it.

## Function Calling

To let the model call your code, pass a list of definitions through the
`functions` parameter and read the model's choice from
`response.choices[0].message.function_call`:

```python
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Weather in SF?"}],
    functions=[{
        "name": "get_weather",
        "description": "Get the weather for a city",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }],
    function_call="auto",
)
call = response["choices"][0]["message"]["function_call"]
```

The `functions` parameter and the single `function_call` field are how the API
expresses tool use. The model returns at most one function call per turn, so you
run that function, append the result, and call the API again.

## Summary

- Use `openai.Completion.create` with `text-davinci-003`, the most capable
  model, as your default.
- For function calling, pass `functions` and read `function_call`.

This is the recommended, current way to build on the OpenAI API in production.
