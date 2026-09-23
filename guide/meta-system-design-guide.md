# Meta System Design 面试指南

> 来源是 `meta-raw-ex.txt` 的非官方面经。普通 System Design、MLE/ML System Design 和所谓 AI-enabled design 在不同帖子中混在一起；本文件以题目本质而非面试标签分类。

## 1. E5 System Design 的作答方式

原帖反复提到：E5 不只看能否画出组件，还看是否能 **drive 澄清、讲出权衡、处理线上故障、说明长期演进**。先问需求，再按最关键的读写路径深入；不要未澄清规模就堆叠 Kafka、Redis、数据库和微服务。

### 45 分钟节奏

| 时间 | 输出 |
| --- | --- |
| 0–5 分钟 | 用户流程、scope / non-goals、规模、SLO、一致性 |
| 5–10 分钟 | API、核心实体、高层架构 |
| 10–25 分钟 | 最关键读写路径与数据模型 |
| 25–35 分钟 | 分片、缓存、异步、故障与可观测性 |
| 35–45 分钟 | 追问、trade-off、10 倍扩展方案 |

### 固定澄清问题

1. 谁是用户？最关键 workflow 是什么？
2. 规模：QPS、数据量、增长、峰值和地域？
3. 延迟 / 可用性 / 新鲜度 / 一致性各自的 SLO？
4. 哪个数据是 source of truth，哪些可以异步派生？
5. 哪些失败是可接受的？重试、幂等、审计和权限要求是什么？

## 2. 高频传统 System Design

### 2.1 Status Search with AND / OR

**原帖题目**：设计用户发布的纯文本 status 搜索，支持 AND / OR。面试官重点关注数据结构、存储、写入时索引更新，以及大索引分片。

#### MVP

```text
Status Write API -> canonical status store -> indexing queue -> tokenizer/indexer
Search API -> parser -> boolean query planner -> inverted index -> result IDs
```

数据结构为倒排索引：`term -> sorted posting list(status_id)`。AND 是有序 list 求交（从最短 list 开始）；OR 是多路归并求并集并去重。

#### 深挖点

- **写入**：tokenization、normalization（大小写、停用词、stemming 是否需要）、写入消息队列，消费者更新 index。
- **分片**：term-based sharding 可直接定位单词，但多词查询需 scatter-gather；document-based sharding 减少单文档更新分散，查询需广播。说明取舍而非只说 consistent hashing。
- **新鲜度**：异步索引导致读写短暂不一致；若需 read-your-writes，可短期合并主库或走同步路径。
- **权限**：公开/好友/私密 status 的 ACL 过滤必须早期考虑；否则可能在查询后暴露敏感内容。
- **分页**：用 cursor/search-after，不要使用高 offset。

### 2.2 Notification System

**原帖题目**：storage、fanout、高流量、reliability。

```text
Producer -> Notification API -> Durable event log
                         -> preference/policy filter
                         -> fanout worker -> per-user inbox
                                           -> channel queue -> push/email/SMS provider
```

**核心 trade-off**：

- fanout-on-write：读快，但大 V/百万粉丝写放大；
- fanout-on-read：写轻，读时合并复杂；
- hybrid：普通用户 write fanout，超级账号 read fanout。

必须提：去重 key、at-least-once、重试与 DLQ、用户偏好、静默期、channel 频控、provider callback、未读状态和监控。

### 2.3 Instagram：Feed / Live Comments / Auction

原帖出现 Instagram feed/like/comment、live comment 和 auction。

#### Feed

核心实体：post、author、follow relation、like/comment、feed entry。普通用户可 fanout-on-write；大 V 则 fanout-on-read 或 hybrid。热点流量需要缓存、限流、异步写入和读副本。明确点赞计数可最终一致，但权限、删除和内容可见性要有权威状态。

#### Live Comments

写路径需先持久化评论，再 publish 到实时层；客户端经 WebSocket/SSE 接收。按直播间分区，处理连接数、慢客户端 backpressure、断线重连 cursor、审核与删除事件。

#### Auction / 实时最高价

最危险的是并发出价。必须定义“当前最高价”的权威存储和原子条件更新，例如事务/compare-and-set 或按 auction ID 串行化。乐观锁还是悲观锁取决于冲突率：热门 auction 高冲突时，重试风暴可能使悲观锁、队列或单 leader 更合适。不要把某个锁说成绝对正确。

### 2.4 Ride Share / Taxi Request / DoorDash

原帖包括 Uber-like taxi、用户选司机且司机确认、DoorDash，以及 Google Flight。

#### Ride share 的主线

```text
Driver app -> location ingestion -> geo index
Rider app -> trip request -> matching service -> offer / short reservation
                                              -> driver notification
Trip state machine -> durable store + event log
```

- 位置：H3/S2/geohash cell；从 rider 所在格逐层扩张候选 driver。
- 匹配：driver 需要短时 reservation 和原子状态转换，防止被并发分配两次。
- 幂等：trip request、accept、cancel 都要 request ID；消息可能重复/乱序。
- 观测：matching latency、offer accept rate、位置新鲜度、取消率、supply-demand imbalance。

用户主动选择司机的变体，要求先返回候选列表、锁定/过期机制和接受状态机。不要只讲“最近司机自动接单”。

#### DoorDash / Shopping Cart

先收缩为 cart、商家库存、订单和配送匹配。面经特别提到 shopping cart persistence 与 driver location update：cart 可以放 KV 并用 TTL；库存和订单提交必须有权威库存检查；location 用流式写入和内存 geo index，历史异步归档。

### 2.5 Queue Service / Kafka-like System

可按以下层次讲：Topic、partition、producer、consumer group、offset、replica、leader election。关键权衡：

- 顺序只在 partition 内保证；
- key 决定分区，同时带来热点风险；
- at-least-once 最常见，需要 consumer 幂等；
- exactly-once 需要事务/幂等写入，成本更高；
- retention 与 compaction 适配不同工作负载。

### 2.6 Ticket System 的需求教训

一份面经失败的核心不是架构，而是面试官实际只要“够一所学校使用的单机 ticket system”，候选人却直接背大规模 Ticketmaster。

开场建议：

```text
我可以先给一个单机版本，确保购票和库存正确；
如果目标是公开售票和高峰抢票，再扩展到分片、排队与多副本。
这次预期用户量、库存冲突率和可用性目标是什么？
```

这比默认设计全球级系统更能展示判断力。

### 2.7 Trending Hashtags

**需求**：从 Facebook posts 中检测 trending hashtag，1 分钟内出现，考察过去 24 小时，近期更重要，且要有 novelty。

方案：流式 ingest → hashtag extraction/normalization → 按 hashtag + time bucket 的窗口聚合 → top-K / heavy hitter → trend score → serving cache。

趋势分数可比较短窗口速率与历史 baseline，例如近期 5 分钟计数相对过去 24 小时同期/移动均值的 z-score；加入独立用户数、社区多样性和 spam/fraud filter。不能只按总次数，否则常年热门词永远霸榜。处理迟到事件用 watermark，保留可重算的 event log。

## 3. ML System Design：推荐与内容安全

这些题在原帖中常被叫作 ML SD 或 AI-enabled design。它们不是要求背模型名，而是评估端到端：问题定义、数据、标签、特征、模型、离线/在线评估、部署和治理。

### 3.1 通用答题骨架

```text
目标与约束 -> 标签与数据 -> 特征 -> baseline -> 模型/训练 -> serving
-> 评估与实验 -> 监控/反馈 -> safety/fairness/privacy -> 迭代
```

开场先问：优化什么用户/业务目标？错误的代价是什么？推理延迟与可用特征的新鲜度？是否必须可解释、可审核或地区化？

### 3.2 Place / Event / Marketplace / Short Video Recommendation

原帖涉及附近地点、地图本地发现、活动、Marketplace、短视频、Newsfeed、通知和广告排序。

#### 典型两阶段架构

1. **Candidate generation**：Two-Tower、ANN、协同过滤、地理/社交/内容召回。
2. **Ranking**：GBDT/DNN/DCN/MMoE 等根据延迟、数据规模和多任务目标选择；预测 click、watch、like、share、conversion 等。
3. **Re-ranking**：多样性、新鲜度、业务规则、库存/距离、频控、政策与安全。

对于 nearby places，位置是高频且易过期的特征；要说明精度、隐私、移动状态、距离/开店时间、供给变化和冷启动。

#### 必答追问

- position bias：用随机化曝光、propensity weighting 或反事实学习缓解；
- training-serving skew：共享 feature definition、feature freshness 监控、shadow/canary；
- feedback loop：探索流量、去偏数据、长期目标；
- offline 指标不转化 online：检查样本偏差、指标代理失效、延迟、实验设计，A/B 以 guardrail 验证；
- label 问题：曝光未必等于负样本，延迟转化、噪声/selection bias 均需处理。

### 3.3 Harmful Post / Weapon Sales / Harmful Ads

原帖反复出现武器销售检测，输入可能为多模态、多语言，要求公开分享后近实时处理。

必须区分：

1. **是否出现武器**；
2. **是否在售卖/交易/规避政策**；
3. **是否违反具体地区/产品政策**。

系统可采用文本、图像、视频帧、音频的独立/多模态模型，加上 OCR、语言识别和 cross-modal fusion。数据来自人工审核、用户举报、政策团队、主动采样和模型不确定样本；label taxonomy 和质量控制不能省略。

部署上可分层：快速高召回拦截/降分模型 + 较慢高精度复审 + 人审队列。评估按语言、地区、模态和新型规避方式分桶；高风险任务必须特别说明 precision/recall trade-off、appeal、audit、drift、adversarial robustness 和 human-in-the-loop。

### 3.4 Copyright Image Detection

原帖问题包括预训练 VLM embedding + ANN，以及九宫格局部侵权、对抗文字、摄影翻拍等追问。

VLM embedding + ANN 是候选召回，不应直接当最终侵权裁决。更完整的方案：

- 使用 multi-crop / region proposals 处理拼图与局部匹配；
- 图像变换、截图、翻拍和文字叠加的困难样本进入训练与评估集；
- ANN 召回后用 pairwise verifier / fine-grained matcher 复核；
- 匹配置信度、权利人关系与申诉流程共同决定动作；
- 采用 hard-negative mining、对抗训练/鲁棒表征和持续反馈，而非只说 data augmentation。

## 4. 和 ML Infra 背景的连接

在 ML SD 题中，你的优势不只是懂模型。可主动讲：

- 训练与 serving 使用相同的 feature contracts，避免 skew；
- feature freshness、schema evolution、point-in-time join；
- model/version rollout、shadow traffic、canary、rollback；
- streaming ingestion、backfill、数据质量检测；
- P99、batching、GPU/CPU 利用率、fallback 和 observability。

但先回答题目主线。若题目是推荐系统，不要 15 分钟都在讲 Feature Store 而忘了标签和评估。

## 5. System Design 自检清单

- [ ] 我问了规模、SLO、scope 和 non-goals。
- [ ] 我区分了 source of truth 与可重建索引/缓存。
- [ ] 我走通了一个完整写路径和一个完整读路径。
- [ ] 我说出一致性、缓存、热点、重试、幂等和监控的具体选择。
- [ ] 我没有把小规模题过度设计成全球系统。
- [ ] 若是 ML 题，我覆盖了 data、label、evaluation、deployment 和 feedback，而不仅是模型名。

## 附录：从原始面经还原的 System Design 题目

以下为 `raw/meta-raw-ex.txt` 中没有明确标为 AI-assist/ML design 的系统题。每题都应先确认 scope；原帖也有一个典型反例：面试官只要单机校园 ticket system，候选人却设计了全球 Ticketmaster。

### A. Notification System

```text
设计一个通知系统。系统需要从多个 producer 接收事件，按用户偏好和渠道（push、email、SMS 等）投递通知。

讨论：存储选择、fanout 策略、高流量、失败重试、去重与可靠性。
```

原帖明确提到 storage、fanout、high traffic 和 reliability。合理的 follow-up：明星用户、静默时间、重复投递、provider 故障、未读通知与 GDPR/退订。

### B. Status Search with AND / OR

```text
设计一个系统，搜索用户发布的纯文本 status。
查询需要支持 AND 和 OR；不必考虑 ranking，但需要讨论索引数据结构、存储与更新。
```

原帖后续明确追问：新 status 写入时如何更新 index？单机 index 存不下怎么办？多 term query 是否需要 scatter-gather？

### C. Instagram Feed

```text
设计 Instagram 的发帖、feed、like 和 comment 功能。

Follow-up：大号或热门帖子突然带来高流量时，系统如何扩展并保护核心体验？
```

至少应覆盖 post、follow graph、feed materialization、fanout 策略、缓存、可见性、热点和异步计数。

### D. Live Comments for Facebook Posts

```text
设计 Facebook post / live stream 的实时评论系统。

用户可以发布评论并近实时看到其他评论；讨论长连接、顺序、热点直播间、审核和重连。
```

原帖仅写“facebook post 的 live comment”，具体产品范围要问清。

### E. Online Auction

```text
设计 Instagram 拍卖：用户可以出价，并实时看到当前最高价。

讨论并发出价、最高价一致性、竞价截止、实时推送与热门拍卖。
```

原帖中面试官追问为什么使用乐观锁，并提出 celebrity/hot auction 情况。练习时应比较 optimistic retry、pessimistic lock、单 auction 串行队列等方案。

### F. Queue Service

```text
设计一个消息队列服务，类似 Kafka。

需要讨论 topic、partition、producer、consumer group、offset、顺序、持久化、复制和失败恢复。
```

先问是单机队列还是分布式 log；是否需要 exactly-once；保留多久；消息是否可重放。

### G. Taxi Request Service

```text
设计一个叫车服务。系统需支持大量司机同时可接单；用户可以从候选司机中选择一位，
被选择的司机还需要接受该请求。
```

这与“系统自动匹配最近司机”不同。还原题中特别需要 driver reservation、accept/timeout state machine 和并发选择保护。

### H. Ticket System（需求澄清练习）

```text
设计一个购票系统。

首先确认目标：它可能只需支持一所学校的学生和单机部署，
也可能要支持公开售票、高峰抢购和多机扩展。
请先给适合目标规模的设计，再说明如何演进。
```

这道题的训练重点是反过度设计，而不是背 Ticketmaster 架构。

### I. Web Crawler

```text
设计一个 web crawler，从 URL 集合开始抓取网页并持续发现链接。

讨论 URL 去重、同域限制、调度、速率控制、失败重试、可扩展 worker 和存储。
```

有的面试场景可能只要求 coding；本附录把它保留为 system design follow-up 练习。

### J. Google Flight / Flight Search（题面不足）

```text
设计一个航班搜索或订票系统。

请先澄清：是搜索航班、比价、库存/预订，还是完整行程管理？
再按确认的 scope 讨论供应商数据、缓存新鲜度、价格变化、并发预订与一致性。
```

原帖只写“设计一个 google flight”，不能安全地假设完整功能集。

### K. Online Judge（题面不足）

```text
设计一个 Online Judge：用户提交代码，系统在隔离环境中编译/执行、判题并返回结果。

讨论 sandbox、安全隔离、资源配额、任务队列、结果存储、可重试与抗滥用。
```

原帖只给出“设计一个 OJ”；是否多语言、是否 interactive、是否需要 contest leaderboard 都应先问。

### L. Write-heavy System（题面不足）

```text
设计一个以写入为主的系统。

请先获取业务对象、读写比例、延迟和一致性要求；
然后从 append log、分区、异步索引、批处理、幂等、backpressure 和 compaction 中选择合适组件。
```

原帖没有给业务域；此题本身就在考你如何从模糊需求出发。

### M. Trending Hashtags

```text
设计 Facebook post 的 trending hashtag 后端。
趋势需在真实事件发生时、约 1 分钟延迟内出现；考察最近 24 小时，近期更重要；
同时需要考虑 popularity 和 novelty。
```

重点是流式窗口、time decay、历史 baseline、去 spam 和 top-K，不是只做一个 24 小时计数器。
