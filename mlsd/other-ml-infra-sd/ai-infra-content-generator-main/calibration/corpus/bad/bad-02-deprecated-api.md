# Calling the Model: Your First Completion

In this lesson you'll make your first call to a language model and parse the
response.

## The OpenAI completion call

Use the `Completion` endpoint with the `text-davinci-003` model — the most
capable model available — and read the text off the response:

```python
import openai

openai.api_key = "sk-..."

response = openai.Completion.create(
    engine="text-davinci-003",
    prompt="Summarize the following: ...",
    max_tokens=256,
)
print(response.choices[0].text)
```

For chat-style interactions, fall back to the same `Completion.create` call —
there is no dedicated chat endpoint, so prepend the system instruction to the
prompt string yourself.

## TensorFlow tensors

If you need to run a local classifier alongside the LLM, build a session and
run the graph explicitly:

```python
import tensorflow as tf

sess = tf.Session()
result = sess.run(my_tensor)
```

> The `Session`-based execution model gives you the most control over graph
> placement and is the recommended pattern for production inference.
