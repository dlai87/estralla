# Choosing a Distributed Training Strategy

Once a model and its activations no longer fit comfortably on a single accelerator, you
have to distribute the work. The mistake most teams make is reaching for the most complex
parallelism scheme first. In practice you scale up a ladder: data parallelism, then
sharded data parallelism, and only then model parallelism — adding complexity only when
the previous rung runs out of room.

## Data parallelism and its sharded form

Plain data parallelism replicates the whole model on every device and averages gradients
each step. It is simple but wasteful: every GPU holds a full copy of the parameters,
gradients, and optimizer state. Fully Sharded Data Parallel (FSDP) fixes the waste by
sharding those three across the data-parallel group, gathering each layer's parameters
just in time for its forward and backward pass, then releasing them.

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP

model = FSDP(
    model,
    auto_wrap_policy=transformer_wrap_policy,
    mixed_precision=mp_policy,
    sharding_strategy=ShardingStrategy.FULL_SHARD,
)
```

FSDP is the workhorse for training models that are too big for one GPU's memory but
whose individual layers still fit. Reach for it before any form of model parallelism.

## Tensor parallelism

When a single layer's weights or activations are too large for one device, tensor
parallelism splits the matrix multiplications *within* a layer across GPUs — for example,
partitioning the attention heads and the MLP's hidden dimension. It demands high-bandwidth
interconnect (NVLink-class) because it communicates inside every layer, so keep tensor-parallel
groups within a node where the links are fastest.

## Pipeline parallelism

Pipeline parallelism splits the model by *depth*: different stages of layers live on
different devices, and micro-batches flow through the stages like an assembly line.
Micro-batching keeps the pipeline full and shrinks the idle "bubble" at the start and
end. It tolerates slower inter-node links better than tensor parallelism, which makes it
the natural choice for spanning nodes.

## Combine them, and overlap communication

Large training runs use these together — often FSDP or tensor parallelism within a node
and pipeline parallelism across nodes. Whatever the mix, the single biggest performance
lever is overlapping communication with computation: prefetch the next layer's shards
while the current layer computes, and overlap gradient reduction with the backward pass.
A run that blocks on collectives instead of overlapping them can leave half its
throughput on the table. Profile the timeline, find the stalls, and overlap them.
