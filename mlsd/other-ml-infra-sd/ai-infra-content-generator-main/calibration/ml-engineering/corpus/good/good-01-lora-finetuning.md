# Parameter-Efficient Fine-Tuning with LoRA and QLoRA

When you need to adapt a pretrained transformer to your own task, full fine-tuning
is rarely the first tool you should reach for. Updating every weight in a 7B+ model
means storing a full copy of optimizer state and gradients, and it produces a fresh
multi-gigabyte checkpoint per experiment. Parameter-efficient fine-tuning (PEFT) gives
you most of the quality at a fraction of the memory and storage cost, and it is now
the default approach for adapting large models in production.

## How LoRA works

Low-Rank Adaptation freezes the base model weights and injects a pair of small
trainable matrices into selected linear layers. Instead of learning a full update
`ΔW` of shape `(d, k)`, you learn `B·A` where `A` is `(r, k)` and `B` is `(d, r)`,
with the rank `r` much smaller than `d` or `k`. At inference you can either keep the
adapter separate or merge it back into the base weights.

```python
from peft import LoraConfig, get_peft_model

config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(base_model, config)
model.print_trainable_parameters()  # typically <1% of total params
```

## Choosing rank and alpha

A useful starting point is `r=16` with `lora_alpha` set to `2*r` (the effective
scaling is `alpha/r`). Rank controls capacity: bump it to 32 or 64 when the task is
far from the base model's pretraining distribution or you see underfitting on a large
dataset. Raising rank alone does not require raising alpha proportionally — treat them
as separate knobs and tune the learning rate alongside them. Targeting all attention
projections plus the MLP layers generally beats targeting only `q_proj`/`v_proj` when
you have the budget.

## QLoRA: LoRA on a quantized base

QLoRA loads the frozen base model in 4-bit (NF4) precision and trains LoRA adapters in
higher precision on top, with gradients flowing through the dequantized weights. This
lets you fine-tune large models on a single consumer or workstation GPU.

```python
from transformers import BitsAndBytesConfig
import torch

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
```

## Honest trade-offs

LoRA is not free quality. On tasks that demand broad behavioral change — large domain
shifts, new languages, or substantial instruction-following overhauls — full or higher-rank
fine-tuning can still win. QLoRA's 4-bit base adds a small quality tax versus 16-bit
LoRA, which is usually worth it for the memory savings but worth measuring. Always
validate on a held-out set rather than trusting that "PEFT just works." Start small,
measure, and increase rank only when the evidence says you need it.
