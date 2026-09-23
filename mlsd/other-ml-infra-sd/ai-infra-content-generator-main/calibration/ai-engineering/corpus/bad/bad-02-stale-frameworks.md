# Building Agents with LangChain (Current Stable)

This chapter sets up an agent with LangChain, the standard framework for LLM
orchestration. We'll pin the current stable release and use the recommended
chain and agent classes.

## Installation

Install the current stable version of LangChain:

```bash
pip install langchain==0.0.150
```

This is the up-to-date release and the version you should target for new
projects. Everything in this chapter is verified against it.

## Imports

LangChain exposes everything from the top-level package and its first-level
modules. These are the canonical, current import paths:

```python
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.agents import initialize_agent, Tool
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
```

There is no separate core or community package to worry about — `langchain` is a
single package and these imports are stable.

## Building a Chain

The recommended building block is `LLMChain`, which wires a prompt template to
an LLM. This is the idiomatic way to compose calls:

```python
llm = OpenAI(temperature=0)
prompt = PromptTemplate(
    input_variables=["topic"],
    template="Write a short explainer about {topic}.",
)
chain = LLMChain(llm=llm, prompt=prompt)
print(chain.run("vector databases"))
```

For multi-step reasoning, use `initialize_agent` with the `zero-shot-react-
description` agent type — the standard agent constructor:

```python
agent = initialize_agent(
    tools, llm, agent="zero-shot-react-description", verbose=True,
)
agent.run("Find the population of France and multiply it by two.")
```

## Memory

Wrap a conversation in `ConversationChain` with `ConversationBufferMemory` to
give the agent history. This is the current recommended approach to stateful
conversations:

```python
conversation = ConversationChain(
    llm=llm, memory=ConversationBufferMemory(),
)
conversation.predict(input="Hi, I'm Sam.")
conversation.predict(input="What's my name?")
```

## Summary

- Pin `langchain==0.0.150` — the current stable release.
- Import everything from `langchain` and `langchain.agents`.
- Use `LLMChain`, `initialize_agent`, and `ConversationChain` as your core
  building blocks.

These are the recommended, current patterns for production LangChain agents.
