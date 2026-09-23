# Meta AI Assist System Design 面试指南

> 基于 `meta-raw-ex.txt` 的非官方面经。多个帖子指出：“AI-enabled / AI-assist system design” 往往仍是经典系统设计或 ML system design，只是面试环境提供了 AI 聊天窗口。不要默认这是让你设计 LLM 产品，也不要假设每位面试官都期待你大量使用 AI。

## 1. 正确理解这轮面试

原帖中出现了两种不同场景：

1. **传统系统题 + AI 助手**：Leaderboard、Ride Share、DoorDash、Instagram 等。面试官可能说 AI 可用，但未必给明确 use case，甚至不鼓励依赖它。
2. **AI/ML 产品系统题 + AI 助手**：weapon-sale detection、place/event recommendation、agent 处理 pipeline issue 等。题目需要 ML 或 agent 设计，但评价仍看端到端架构与判断。

共同原则：AI 可以帮助你检查遗漏或比较方案；你要主导 scope、数据模型、关键路径、取舍和最终表达。若面试官问“为什么采用这项 AI 建议”，必须能从系统约束出发回答。

## 2. 如何合规地使用 AI

面试开始时确认：哪些阶段允许 AI、是否所有输入可见、是否有禁止内容、是否需要自己画图。严格遵守面试官规则。

### 2.1 值得使用 AI 的 4 个小任务

| 时机 | 合格用法 | 不佳用法 |
| --- | --- | --- |
| 澄清后 | 检查是否遗漏一致性、权限、backpressure | “帮我设计整个系统” |
| 方案选择 | 对比两种已提出方案的 trade-off | 让 AI 随机列 20 个组件 |
| Deep dive | 审计一个明确路径的 failure modes | 把 AI 输出直接朗读 |
| 收尾 | 检查 monitoring / security checklist | 用 AI 重写全部白板答案 |

### 2.2 可复用 prompt

**需求审计**

```text
我正在设计 [问题]。已确认：规模是 [...], SLO 是 [...],
强一致需求是 [...], 非目标是 [...].
请只列出 5 个会改变架构选择的遗漏问题，并说明每个问题的影响。
不要设计完整方案。
```

**方案比较**

```text
比较方案 A=[...] 与方案 B=[...]，约束是 [...].
输出：读写延迟、成本、一致性、故障恢复、实施复杂度各一条；
最后给出在此约束下的建议和一个不选择另一方案的理由。
保持在 150 字以内。
```

**故障模式审计**

```text
审计这条写路径：[...]。
列出最可能的重复、乱序、热点、超时和部分失败问题；
每项给一个具体的缓解策略。不要重新设计整个系统。
```

你仍应把选择用自己的话讲出来，例如：“我用 AI 只是检查了失败路径；我选择 event log 是因为需要 replay 和异步重建索引，而不是因为 AI 建议了 Kafka。”

## 3. 45 分钟答题流程

### 0–5 分钟：定义题目

写出 user journey、核心 API、规模、SLO、strong/eventual consistency、non-goals。任何“AI-enabled”标签都不能替代需求澄清。

### 5–12 分钟：MVP 高层架构

先画 5–7 个组件，明确 source of truth 与异步派生数据。说清一条 write path、一条 read path。

### 12–28 分钟：挑最危险的 deep dive

在排行榜中是有序 range 查询与热点；在 Ride Share 中是地理匹配与 driver reservation；在 ML moderation 中是数据/标签/高风险 action。由面试官问题决定深挖，不要平均讲所有点。

### 28–40 分钟：扩展与可靠性

谈分片、cache、队列、重试、幂等、backpressure、observability、安全、成本。对 ML 系统再谈 offline/online evaluation、drift、rollout、feedback。

### 40–45 分钟：归纳 trade-off

总结“我选择 A 而非 B，因为 X；随着规模到 Y，我会将 Z 替换为 W”。若 AI 给过建议，明确哪些建议被采纳、为什么。

## 4. 经典系统题，但可出现 AI Assist

### 4.1 Video Game Score Leaderboard：Closest Scores

**题意**：players、games、friends、每位用户每款游戏一个 high score；完成游戏后，展示与自己分数最接近的结果，面对大规模 range search。

#### 关键澄清

- 全局榜、好友榜，还是两者？
- “closest” 指分数值相近，还是 rank 上下邻居？返回 K 个还是固定范围？
- 更新是否只会提高？奖励/结算是否允许最终一致？

#### 设计

```text
Score API -> validation -> authoritative player-game score store -> score event log
                                                        -> ordered leaderboard index
Read API -> get player score -> range/rank query around score -> privacy/friend filter
```

每 game 的有序索引可用 Redis sorted set（适合中等规模）或分片 ordered store。权威 player-game score 与可重建排序索引分离。高分榜用缓存；高峰 game 按 `game_id` 分片，必要时再按 score range / region 分裂。

**高分回答**：并列分数的 tie-break、反作弊、朋友关系过滤、热点 game、索引与权威库短暂不一致、奖励计算的强一致需求。

### 4.2 Ride Share / Taxi / DoorDash

```text
Driver location stream -> geo index
Rider request -> trip state machine -> matching -> offer/reservation -> driver accept
                                         |                         -> notification
                                         -> durable event log -> billing/analytics
```

重点：H3/S2/geohash 候选查询；driver 短期 reservation 和原子状态转换；位置更新的新鲜度；请求幂等；取消/超时；热点区域；供需与公平。

DoorDash 变体还要处理 cart、库存、merchant prep time 和配送 batching。若题目是单城市 MVP，不要一开始讲全球多区复制。

### 4.3 Instagram / Live Comment / Auction

- Feed：fanout-on-write、fanout-on-read 与 hybrid；大 V 是关键分界。
- Live comments：先持久化、再 WebSocket/SSE broadcast；按 live room 分区、慢消费者、顺序与重连。
- Auction：以 auction ID 为一致性边界；原子条件更新/串行队列/锁避免双最高价；高冲突热点下评估乐观锁重试风暴。

### 4.4 Status Search AND / OR

倒排索引 + parser + boolean query plan。AND 用交集（短 list 优先），OR 用并集；写入走 tokenizer/normalizer/indexer pipeline。term shard 多词查询需要 scatter-gather，document shard 则查询广播。加上索引新鲜度、ACL、cursor pagination 和 index rebuild。

## 5. ML / AI 产品系统设计

### 5.1 Nearby Places / Event / Marketplace / Video Recommendation

**题目范围**：原帖有地图地点推荐、Facebook Event、Marketplace、short video、newsfeed、ads、notification ranking。

#### 回答骨架

```text
目标和用户价值 -> label 与训练数据 -> features -> baseline/model
-> candidate generation -> ranking/reranking -> serving -> evaluation/experimentation
-> monitoring and feedback loop
```

候选生成常见 Two-Tower / ANN / rule-based recall；ranking 可从简单 GBDT 或 DNN 起，再解释为何多任务（click、watch、save、conversion）或 multi-objective。Re-ranking 负责多样性、新鲜度、距离/库存、政策和频控。

**不要遗漏**：曝光 bias、负样本定义、cold start、training-serving skew、offline-online gap、exploration、长期满意度、privacy。地点推荐还应谈位置权限、特征时效、地理精度和移动用户。

### 5.2 Weapon-Sale / Harmful Ads Detection

原帖的关键提醒是：不能只做“武器识别”；还要识别售卖/交易意图、上下文、政策和地区限制。

```text
post ingestion -> language/OCR/frame extraction -> multimodal classifiers
              -> policy decision / risk tier -> block, reduce, review, allow
              -> reviewer outcome + appeals -> labeled data and retraining
```

输入可能是文本、图片、视频、音频和多语言。数据来自人工审核、举报、政策专家、主动学习。部署可分为低延迟高召回筛选、较慢高精度复审和人工队列。指标应按语言、地区、模态、风险级别切片，并说明 false positive 与 false negative 的不同代价。

### 5.3 Copyright Image Matching

VLM embedding + ANN 是**候选召回**，不应直接做最终侵权判决。要处理拼图、局部区域、截图/翻拍、对抗文本、相似但合理使用的图片：multi-crop/region-level retrieval → pairwise verification → policy/ownership checks → appeal。回答模型问题时，也要谈 hard negatives、分布鲁棒性、校准和人工审核。

### 5.4 Agent for Large-Scale Pipeline Issues

原帖有“设计 agent 处理大规模 pipeline issue”。这是最容易被误答为“接一个 LLM”的题。

#### 先澄清 agent 权限

- Agent 只做告警聚合和建议，还是能重跑、回滚、修改配置？
- 哪些动作需要 human approval？
- 处理的是 batch、streaming 还是 training/serving pipeline？
- 目标是 MTTR、误报率、成本、数据正确性还是全部？

#### 推荐架构

```text
metrics/logs/traces + lineage + run metadata -> incident correlator
                                             -> diagnosis/retrieval layer
                                             -> agent planner
                                             -> tool gateway (read-only by default)
                                             -> proposed remediation
                                             -> approval policy -> executor
                                             -> audit log + outcome evaluation
```

Agent 的“模型”不是重点；可靠的 tool contracts、权限、干跑（dry run）、可回滚操作、审计、evaluation 和 human-in-the-loop 才是。高风险环境不应允许 agent 直接删数据、改生产配置或无限重试。

#### 衡量

- incident grouping precision/recall；
- diagnosis accuracy / top-K actionable suggestion rate；
- approval rate、rollback rate、caused incident rate；
- MTTR、operator time saved、false remediation；
- cost、latency、覆盖率和安全违规。

### 5.5 Coding LLM / Chatbot Research Design

原帖有研究设计题：设计 coding LLM、设计 chatbot。这类题需先定义用户任务与评估，不能先跳到模型。

**Coding LLM**：代码补全、bug 修复、repo-level task、工具调用哪一个？离线用 pass@k、test pass rate、patch correctness、security regression；线上看 accept rate、time to completion、bug/rollback、用户满意度。数据治理、许可证、隐私、benchmark contamination、sandbox execution 均是关键。

**Chatbot**：明确是客服、知识问答、创作还是 agent；定义 helpfulness、groundedness、safety、latency、escalation。RAG 要评 retrieval recall、citation support 和 hallucination；高风险领域应以安全 fallback 和人工转接为主。

## 6. AI Assist 不该做什么

- 不要让它未经澄清就生成“完整系统设计”；
- 不要把 AI 的模型/数据库列表当架构论证；
- 不要要求它替你画复杂图然后不解释数据流；
- 不要用它掩盖不会的概念，面试官会继续问；
- 不要把 AI generated output 直接放在最终答案中。

如果 AI 的建议有误，最好的回应不是辩护，而是指出：“这个建议假设了强一致的全局排序，但我们只需要最终一致的展示榜，所以成本不值得。”这正是面试想看的 judgment。

## 7. 你的 ML Infra 加分方式

在 ML/agent 系统题中，主动但简洁地连接到：feature contracts、online/offline consistency、schema evolution、streaming freshness、model registry、shadow/canary rollout、fallback、tracing、cost attribution、replay/backfill。你能说明这些如何影响 product SLO 和风险，而不是只罗列平台词汇，才是优势。

## 8. 最终检查

- [ ] 我先问了范围和规模，而不是直接讲全球架构。
- [ ] 我走通了 read/write 或 inference/feedback 的完整路径。
- [ ] 我说清 source of truth、异步索引/缓存和一致性选择。
- [ ] 我有一个明确的 hottest bottleneck 和对应缓解方案。
- [ ] ML 题包含 data/label/evaluation/deployment，而非只有模型。
- [ ] agent 题包含权限、审批、审计、回滚和评估。
- [ ] 若使用 AI，我能解释每项采纳建议的理由，也能指出未采纳的建议。

## 附录：从原始面经还原的 AI Assist System Design 题目

本附录收录 `raw/meta-raw-ex.txt` 中明确标为 AI sys design、AI-enabled SD、ML design、research design，或题目本身明显要求 AI/ML 系统设计的内容。原帖多次提醒：其中一些轮次只是在传统 design 面试中提供了 AI 窗口，因此是否使用 AI 及使用方式必须听现场规则。

### A. Video Game Score Leaderboard（高置信度）

```text
设计 video game score leaderboard。

实体：players、games、friends、high_scores；每个 player-game 对只维护一个 high score。
核心功能：当用户完成某游戏后，展示与该用户分数最接近的其他分数。
要求支持大规模 range search。
```

需要澄清 closest score 是全局还是好友范围、按 score gap 还是 rank 邻居、并列处理、分数更新规则与奖励结算一致性。

### B. Ride Share System（高置信度）

```text
设计一个 ride share system。
```

原帖将它标为 AI sys design，但没有给 AI 产品需求。因此默认按经典叫车系统答：driver location、geo index、matching、reservation、accept/cancel、幂等和供需；不要凭“AI”标签直接加入模型。

### C. Agent for Large-scale Pipeline Issues（中置信度）

```text
设计一个 agent，处理大规模 pipeline 的 issue。
```

题面未说明 agent 是仅诊断、推荐修复，还是自动执行。应先澄清 pipeline 类型、风险、工具权限、human approval、成功指标和可回滚性。完整设计至少包含：telemetry/lineage、incident correlation、retrieval/diagnosis、tool gateway、approval、executor、audit 与 offline evaluation。

### D. Detect and Block Weapon Content on Facebook（高置信度）

```text
设计一个系统，检测并阻止 Facebook 上包含 weapon 的内容。
输入是多模态（text、image、video、audio）且多语言；
内容公开分享后需近实时检测。
```

另一些帖子明确为“weapon-selling ads / harmful ads”。答题时必须区分武器出现、售卖意图和政策违法；不能只设计 image classifier。

### E. Place Recommendation for Maps / Local Discovery（高置信度）

```text
设计一个 ML system，为 maps 或 local-discovery 产品中的用户推荐附近地点/餐厅。
用户可能在移动；重点是 personalized discovery，不是传统 keyword search ranking。
```

原帖追问 feature engineering、label、XGBoost 的局限、数据获取和 model pros/cons。答案需覆盖地理/时间/用户/地点特征、candidate generation、ranking、冷启动、位置隐私和在线实验。

### F. Facebook Event Attendance Recommendation（高置信度）

```text
设计模型/系统，预测用户是否会参加 Facebook event，并将 event 推荐给用户。
```

需明确预测目标是 `P(attend)`、点击、RSVP 还是长期满意；处理曝光偏差、稀疏 label、社交影响、时间与地点约束。

### G. Video / News Feed / Marketplace / Ads Ranking（高置信度）

```text
设计以下之一的排序或推荐系统：
- short video / Reels；
- Facebook News Feed；
- Marketplace recommendation page；
- ads ranking；
- notification ranking。
```

原帖给出的典型细节包括 Two-Tower candidate generation、ANN、DNN/DCN/MMoE 多目标精排、diversity re-ranking、exploration、position bias、feedback loop、calibration。面试时按题目选择，勿堆满所有模型。

### H. Copyright Image Violation Detection（高置信度）

```text
设计模型，检测用户上传图片是否违反版权。

已知有版权图片可用作参考库。需要讨论 fine-tuning、九宫格/局部区域侵权、
adversarial text、截图或相机翻拍，以及最终判定。
```

原帖候选人提出 VLM embedding + ANN。更好的完整还原是：ANN 做 candidate retrieval，region/multi-crop 处理局部，pairwise verifier 复核，再结合权属与申诉流程作最终 policy decision。

### I. High-risk Account / Harmful Item Detection Pipeline（中置信度）

```text
设计一个 ML pipeline，识别高风险账户或 harmful items，并支持数据收集、训练、
近实时推理、人工审核和持续反馈。
```

原帖没有统一实体定义。训练时应主动问风险类别、action、label 来源、误判成本和公平性要求。

### J. Coding LLM / Chatbot Research Design（高置信度，研究岗位倾向）

```text
给定具体场景，设计：
1. 一个 coding LLM；或
2. 一个聊天机器人。

说明数据、训练/适配、评估、部署、产品指标和安全边界。
```

原帖还记录一轮 ML fundamentals（optimizer、scaling law、k-means、GMM）和 attention coding；这更偏研究/MLE 轨道，适合作为此题的背景准备。

### K. AI-enabled Design DoorDash（中置信度）

```text
在提供 AI Assist 的 system-design 环境中，设计 DoorDash。
面试重点包括 shopping cart persistence、driver location update 和决策 trade-off。
```

这是“AI-assisted 传统系统题”的好练习：即使不使用 AI 也不应扣分；先完成自己的架构，再用 AI 做 failure-mode audit 即可。

### L. Video Ranking / Event Recommendation（题面不足）

原帖有“两个 system design：video ranking 和 event recommendation”，但没有目标、指标或约束。练习时可将其分别实例化为短视频多目标排序和 `P(attend)` event recommendation；开场必须先定义 success metric、可用数据、延迟与安全/公平约束。
