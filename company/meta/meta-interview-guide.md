# Meta 面试题整理与 AI 面试攻略

> 来源：`raw/meta.txt` 中收集的非官方面经。题目表述有转述、记忆偏差和缺失细节；本文件将其尽量还原，并明确区分“原始信息”和“建议的补全”。不要把题目或面试流程视为 Meta 的官方承诺。

## 一页结论

这份面经呈现的 E5 信号很一致：

- **Coding**：不一定是 Hard，但需要在沟通中写出稳定、可扩展、边界清楚的代码。
- **System Design**：要从“能画出架构”升级到“能解释规模、故障、长期维护与取舍”。
- **AI Coding**：AI 可以帮你加快实现，但你必须主导需求澄清、方案、性能判断和验证；大压测常常是关键。
- **AI System Design**：很可能仍是传统系统设计，只是提供一个 AI 助手窗口。不要把它误解为必须设计 LLM/RAG/Agent 系统。
- **Behavioral**：重点是 ownership、跨团队推动、判断力和可量化影响，不是“我参与过什么”。

对 ML Infra 候选人而言，Feature Store、online serving、Spark/Cassandra、可靠性与可观测性的经历可直接映射到：缓存/限流、排行榜、通知、状态检索、数据版本与 TTL 等题目的 trade-off。

---

## 1. 面试形式与考察重点

### 面经中出现的流程

| 阶段 | 出现的内容 | 观察到的信号 |
| --- | --- | --- |
| Recruiter / phone screen | BQ 与项目经历约 25 分钟；1–2 道 Easy/Medium coding | 项目匹配度、表达、代码基本功 |
| Technical screen | interval 变体；tree/graph 题 | 思路清晰、边界、可运行代码 |
| Onsite coding | 普通 coding，或 2 道 AI coding | 生产场景、性能、压测、沟通 |
| System design | Notification、Ride Share、Leaderboard、Status Search | 架构、规模、可靠性、取舍 |
| Behavioral | impact、冲突、失败、模糊需求、反馈 | E5 ownership 与影响力 |

### E5 回答标准

每道题都尽量让面试官看到以下过程：

1. **澄清**：输入、输出、约束、规模、异常情况、成功指标。
2. **先给可交付方案**：说明正确性和复杂度，而不是沉默写代码。
3. **主动说边界**：空输入、重复数据、并发、重试、数据倾斜、权限等。
4. **根据 follow-up 演进**：单机 → 多机；小数据 → 大数据；正常路径 → failure path。
5. **用事实结束**：复杂度、压测结果、SLO、失败恢复方式或项目影响。

---

## 2. 普通 Coding 题库

### 2.1 字符串计算器

**原始题目**：写字符串计算器，类似 LeetCode 227（Basic Calculator II）。

**尽量还原的题意**：给定只含非负整数、空格和 `+ - * /` 的表达式字符串，按运算优先级计算结果；通常整数除法向零截断。

**解题思路**：

1. 从左到右扫描，积累当前数字 `num`。
2. 遇到运算符或字符串末尾时，按前一个运算符处理 `num`。
3. `+/-` 将正负数压栈；`*//` 与栈顶立即合并。
4. 最后求栈和。

**复杂度**：时间 `O(n)`，空间 `O(n)`；如维护 `result` 和 `last_term`，可降至 `O(1)` 额外空间。

**常见失误**：忘记处理末尾数字；对空格处理不一致；Python 的 `//` 对负数向下取整，若题目要求向零截断，需要用 `int(a / b)` 或等价安全实现。

### 2.2 二分查找 / First Bad Version

**原始题目**：手写二分，类似 LeetCode 278。

**尽量还原的题意**：`isBadVersion(version)` 是黑盒 API；版本从 `1..n`，存在一个最早的坏版本，找出它。

**解题思路**：维护闭区间 `[left, right]`。若 `mid` 是坏版本，答案在左半边（含 `mid`）；否则在右半边。循环结束时 `left == right`。

**复杂度**：`O(log n)` API 调用，`O(1)` 空间。

**面试技巧**：先说清单调性：`false ... false, true ... true`。这比直接背模板更重要。

### 2.3 Interval 变体

**原始信息**：Technical screen 出现 “interval related variation”，细节未给出。

**高概率范围**：Merge Intervals、Meeting Rooms、Insert Interval、按资源分配会议室、区间覆盖/空闲时间。

**通用框架**：

- 先问区间是否闭区间、端点相等是否冲突、输入是否已排序。
- 合并/覆盖题：按起点排序，再扫描合并。
- 会议室/最大并发题：按起点排序，使用最小堆保存结束时间，或扫描线。
- 动态增删题：指出需要有序映射/平衡树/segment tree；不要把静态解法硬套到在线场景。

### 2.4 Tree / Graph 题

**原始信息**：Technical screen 出现一题 tree/graph；另有 graph/dependency coding round。

**高概率题型**：遍历、连通性、拓扑排序、依赖循环、最短路径。

**答题框架**：

| 需求信号 | 常用算法 | 必问边界 |
| --- | --- | --- |
| 是否可达 / 连通分量 | DFS / BFS / Union-Find | 有向还是无向；是否允许重复边 |
| 前置依赖 / 课程安排 | Kahn 拓扑排序或三色 DFS | 是否要返回顺序；如何报告环 |
| 最少步数 | BFS | 边权是否全为 1 |
| 加权最短路 | Dijkstra | 是否有负权边 |

**E5 follow-up**：图装不进内存怎么办？如何按分区处理？如何并发执行独立 DAG 节点？失败重跑如何保证幂等？

### 2.5 Production Coding：Cache / Rate Limit

**原始信息**：Onsite Coding Round 1 是 cache / rate limit 设计，follow-up 涉及大数据、多机、failure case。

**可能的基础实现**：

- Cache：LRU，`HashMap<Key, Node>` + 双向链表，`get/put` 均为 `O(1)`。
- Rate limiter：Token Bucket、Fixed Window、Sliding Window Log/Counter。

**推荐作答顺序**：

1. 先写单机 API 与数据结构。
2. 明确限流维度：user、IP、token、tenant 还是 endpoint。
3. 扩展到多机：一致性哈希路由，或共享 Redis / KV；说明准确性、可用性、成本的取舍。
4. failure case：Redis 不可用时 fail-open 还是 fail-closed；时钟漂移；热点 key；过期清理。

**与 ML Infra 的连接**：可将 user 换成 model、tenant、endpoint 或 GPU pool；解释 admission control 如何保护在线推理的 P99 和公平性。

### 2.6 In-Memory Database with TTL and Point-in-Time Field Read

**原始题目**：支持 `get`、`set`、`delete`、TTL，以及 `get_when(key, field, at)`，返回某 key 的某 field 在时间 `at` 的值，不是将整个数据库回滚。

**核心模型**：每一个 `(key, field)` 存一条按时间排序的版本链：

```text
field versions:
[start=10, end=20, value=A]
[start=20, end=∞,  value=B]
```

`get_when(..., at)` 在版本链中二分，找满足 `start <= at < end` 的版本；TTL 等价于给版本设置有效结束时间。删除可写入 tombstone 版本，而不是物理删除历史。

**复杂度**：当前值读可为 `O(1)`；历史读为 `O(log v)`，`v` 是该 field 的版本数。

**关键澄清**：时间是系统时间还是调用方提供的逻辑时钟？相同时间戳怎么排序？TTL 是否影响历史查询？历史保留多久？

**ML Infra 联想**：这是简化版 feature versioning / point-in-time correctness。可以自然提到训练集回放、时间穿越读取和数据泄漏防护。

### 2.7 Maze Solver

**原始信息**：AI coding 出现常见 maze solver，细节未给出。

**典型还原**：给二维网格、起点、终点、墙；判断可达或返回最短路径。

**解法**：只要求可达用 DFS/BFS；要求最短无权路径用 BFS，并用 `parent` map 回溯路径；允许不同移动成本则用 Dijkstra/A*。

**测试**：无路、起点等于终点、单行/单列、边界格、环路、大网格。

### 2.8 两根不均匀燃烧的绳子测 45 分钟

**题意**：每根绳子单端燃尽都恰好 60 分钟，但燃烧速度不均匀；只有打火机，测 45 分钟。

**答案**：

1. 第一根两端同时点燃，第二根一端点燃。
2. 第一根一定会在 30 分钟后燃尽，不受不均匀速度影响。
3. 此时点燃第二根的另一端。第二根原本剩余的燃烧时间是 30 分钟；两端烧完只需 15 分钟。
4. 总计 `30 + 15 = 45` 分钟。

**考察点**：是否能抓住不变量，而不是假设绳子燃烧均匀。

### 2.9 股票最大利润

**原始题目**：任意次数交易的最大利润；follow-up 为只允许一次交易。

| 版本 | 解法 | 复杂度 |
| --- | --- | --- |
| 可多次交易，不能同时持多股 | 累加相邻上涨 `max(0, prices[i]-prices[i-1])` | `O(n)` / `O(1)` |
| 仅一次交易 | 扫描时维护历史最低价和当前最大利润 | `O(n)` / `O(1)` |

**澄清**：是否允许同日买卖？交易费用、冷冻期、交易次数上限都会改变问题。

### 2.10 Mouse and Cheese Reachability

**原始题目**：`move(x, y)` 和 `reachCheese()` 返回 `True/False`；问从 `(0,0)` 出发老鼠能否到达奶酪。

**合理还原**：未知地图/黑盒移动 API 中的搜索问题。

**解法**：DFS + visited，尝试四个方向；若每步代价相同且要求最短步数则 BFS。必须做 visited，否则在可逆移动中无限循环。

**澄清**：坐标是否有限？`move` 失败后位置是否保持？是否需要回退？如果是机器人 API，通常需要反向移动恢复当前位置。

### 2.11 是否存在和为 Target 的连续子数组

**原始题目**：找最长连续子数组，其和等于 target，可能有多个组合，只需返回是否存在。

**注意原始描述有歧义**：它同时说“最长”和“只需返回是否存在”。应先问面试官：要返回 bool、长度，还是区间。

**有负数的通用解**：前缀和 + HashMap。若要最长长度，记录每个前缀和首次出现的下标；当前位置 `i` 的前缀和为 `prefix`，若存在 `prefix-target`，则得到候选区间。

**全为非负数时**：可用滑动窗口，但不能用于含负数的通用版本。

### 2.12 按 Population 随机抽取 City

**原始题目**：给 cities 与 populations，按 population 抽 City。

**基础解法**：前缀和数组 + `[1, total]` 的随机数 + 二分查找。预处理 `O(n)`，单次抽样 `O(log n)`。

**优化 follow-up**：

- 频繁静态抽样：Alias Method，预处理 `O(n)`，采样 `O(1)`。
- population 在线变化：Fenwick Tree / Segment Tree，更新与采样 `O(log n)`。
- 使用 64-bit 总和，避免人口之和溢出。

### 2.13 Root-to-Leaf Minimum Sum Path

**原始题目**：LeetCode 112 变体，给二叉树，寻找 root-to-leaf 和最小的路径并返回 path。

**解法**：DFS，递归参数维护当前和与当前路径；到 leaf 时比较最小和并复制路径。若只求最小和而不是 path，可返回子树最优值；返回路径时要注意回溯 `path.pop()`。

**复杂度**：遍历 `O(n)`；递归栈 `O(h)`，保存答案 `O(h)`。

### 2.14 最多删除一个字符成为回文 / 删除 K 个字符

**原始题目**：LeetCode 680；follow-up 最多删除 `K` 个字符。

**一个删除**：双指针；首次 `s[l] != s[r]` 时，分别检查跳过左或跳过右后的区间是否回文。

**K 个删除**：定义 `can(l, r, k)`；相等时向内收缩，不相等时尝试删除左或右并 `k-1`，用 memo `(l,r,k)`。也可转化为最长回文子序列：若 `n - LPS <= K`，则可行。

**面试技巧**：先说 `K=1` 的线性特化解，再解释为什么 `K>1` 必须避免指数分支。

---

## 3. AI Coding：题目、算法与实战方式

### 3.1 AI Coding 到底考什么

从原始面经看，AI coding 的本质不是“让模型替你写完然后等待”。它考察：

- 你是否能把模糊题意拆成明确目标和验收标准；
- 你是否能让 AI 给出正确、可维护的实现，而不是接受第一份输出；
- 你是否能在受限环境下避免无意义的大规模运行；
- 你是否能解释性能瓶颈、设计压测、解读结果和调整方案；
- 你是否能同时与面试官沟通和使用 AI，而不是把自己变成提示词输入器。

**最重要原则**：遵守面试平台和面试官明确的 AI 使用规则。可以使用时，也应清楚说明你在用 AI 辅助实现/验证，但由你负责方案、正确性和最终判断；不要试图绕过限制或隐瞒工具使用。

### 3.2 AI Coding 通用执行流程

#### 开场 60–90 秒

先对面试官复述：

```text
我先确认输入、输出、规模、评分指标和允许的库。
然后我会先实现正确且可测试的版本，用小样例验证；
若压测失败，再根据 profiler/指标优化，而不会盲目跑大样例。
```

#### 与 AI 的安全协作提示词模板

根据平台规则许可后，可用简短提示约束助手：

```text
这是一个限时编码面试，环境资源有限。
先读取题目并用不超过五点说明：目标、约束、复杂度目标、计划和最大风险。
先实现正确且高效的方案；只运行小型、确定性的测试。
不要启动后台任务、并行 benchmark 或大规模随机测试；每次运行都加超时。
在建议优化前，说明瓶颈假设、预期收益、成本和风险。
```

不要照抄长提示词，也不要让 AI 在未优化时自动运行 full test。题目要求和剩余时间才是第一优先级。

#### 5 步循环

1. **澄清**：问清小数据示例、极端输入、性能指标、随机性和测试接口。
2. **定方案**：你先说数据结构和复杂度，再让 AI 协助实现或审查。
3. **小测**：写 3–5 个能否定方案的最小用例；固定随机种子。
4. **测量**：只在同一个 sample 上比较优化前后；记录运行时间、正确率、内存。
5. **收尾**：删掉调试代码，复查 API、异常、复杂度，并口头说明未覆盖的 trade-off。

### 3.3 Friend Recommendation

**原始题目**：给 user 列表和 friend pairs，为指定用户推荐新朋友，例如朋友的朋友或热门用户。测试含约 100k 用户、约 1.5M 条好友边。

#### 先澄清

- 好友关系是否无向？会不会有重复边或自环？
- 推荐几个？是否允许已是好友或自己？
- 排序规则：共同好友数、全局热度、最近活跃度还是随机？
- 只推荐二跳邻居，还是在没有候选时回退到热门用户？
- 1.5M pairs 的内存预算与延迟目标？

#### 基础正确解

1. 建立 `user -> set(friends)` 邻接表。
2. 对目标用户 `u` 的每个直接好友 `f`，遍历 `f` 的好友 `v`。
3. 跳过 `v == u` 和 `v in friends[u]`。
4. 用 `candidate_score[v] += 1` 统计共同好友数。
5. 按 `(-score, user_id)` 排序；若题目要求 fallback，再从热门用户中补足。

**复杂度**：建图 `O(E)`；单次推荐为 `O(sum(deg(f) for f in N(u)))`，而不是 `O(V^2)`。对大图，避免遍历全体用户或构造 user-user 矩阵。

#### 大数据优化与回答点

- 使用 set 做 membership check；list 在高 degree 用户上会退化。
- 只保留 Top K：最小堆，避免给全部候选完全排序。
- 超级节点（百万粉丝）可能导致 fanout 爆炸：设 degree cap、采样、预计算或异步离线推荐。
- 线上服务可预计算用户 embedding / 候选集，但必须说明 freshness 与成本。
- 生产系统需考虑隐私 block list、账号可见性、地域限制与缓存失效。

#### 最小测试集

- 无好友、只有一个好友、所有二跳均已是好友、重复边、自环。
- 平分时稳定排序。
- 1 个高 degree 节点，确认不会产生 `O(V^2)` 行为。
- 随机大图 smoke test：验证结果中没有本人和现有好友。

### 3.4 Card Game：选三张凑 15

**原始题目存在不确定性**：36 张卡，数值 1–9；桌面可见约 16 张；每次选 3 张且和为 15，之后从剩余卡补 3 张；若 36 张全部消耗（12 组）即赢。要求写新的大规模 benchmark（原文记为 >1k games，也有 10k case 的描述）。

#### 必须先问的问题

- 36 张中每个数值的数量是否固定（例如 1–9 各 4 张）？
- 选中的三张是否立刻移除？补卡是随机还是固定顺序？
- 桌面上没有合法三元组时，是失败还是允许换牌？
- 算法目标是“能赢一次”、最大化胜率，还是最小化决策时间？
- benchmark 评分是 win rate、平均耗时、最坏耗时，还是三者都有？

#### 可交付的分层方案

1. **正确性层**：枚举可见卡中的所有三元组；用 value count 生成组合，避免按卡位置的 `O(m^3)` 重复枚举。
2. **策略层**：对每个合法动作评分，例如优先保留未来可组成 15 的组合、降低死牌数量、提高剩余牌的可配对性。
3. **搜索层**：如果随机补牌可预测/状态空间可控，用 memoized DFS 或 beam search；状态包含可见牌计数、剩余牌计数和牌堆位置/随机状态。
4. **评测层**：固定 seed，分别跑 20、100、1000 局，记录 win rate、平均时间、P95/P99 与超时次数。

#### 算法选择

- 仅找合法动作：枚举数值 `(a,b,c)`，`a+b+c=15`，复杂度由值域决定，近似常数。
- 追求有限牌堆下的最优策略：状态压缩（每个数值的计数）+ memo；不能只贪心后宣称最优。
- 追求高胜率但状态过大：rollout / Monte Carlo + heuristic。应明确这是近似算法，并以相同 seed 的 benchmark 证明收益。

#### AI Coding 的高分表现

不要一上来让 AI 跑 10k 局。先让它写出状态模型和 5 个小局面，再决定：

```text
先证明动作生成无漏无重；再用固定 seed 的 20 局比较 baseline 与 heuristic；
只有在正确率和每局时间都稳定后，才运行批准的大 benchmark。
```

### 3.5 Maze Solver

见普通 coding 的 2.7，但 AI coding 中额外考察协作能力：让 AI 先明确 API 约定和选择 BFS/DFS 的理由；你要能立即指出“若要求最短路径，DFS 不是合适默认方案”。

### 3.6 最大不重字符 Word Subset

**原始题目**：从一组 words 中选 subset；任意两个被选 word 不能共享字符，最大化总字符数。

#### 先澄清

- 单个 word 内有重复字符时是否允许？通常不允许或该 word 不可选。
- 字符集是否仅为小写 a–z？
- 返回最大长度还是具体 word subset？
- word 数量上限是多少？这决定回溯、DP 或近似算法。

#### 小写字母解法：bitmask + DFS

1. 将每个 word 编为 26-bit mask；若内部有重复字符则丢弃。
2. 回溯每个 word：若 `used_mask & word_mask == 0`，则可选。
3. 维护最大总长度和对应 subset。

**复杂度**：最坏 `O(2^n)`，适用于 `n` 较小；位运算让冲突检查为 `O(1)`。

#### 大规模 follow-up

这是 weighted set packing 的形式，通常 NP-hard。高分回答不是假装存在多项式最优解，而是：

- 小 `n`：DFS + memo / meet-in-the-middle。
- 特殊结构：按字符集合 DP。
- 大 `n`：启发式（按长度/稀有字符排序），并明确它不保证最优。
- 剪枝：剩余最大可能长度上界不超过当前 best 时停止。

---

## 4. System Design 与 AI System Design

### 4.1 AI System Design 的正确理解

原始面经中，AI sys design 的题目是排行榜与 Ride Share，都是经典系统设计；也有人提到面试官只提供 AI 聊天窗口，并不要求或推荐依赖它。因此准备方式应是：

- 将其当作正常 system design；
- 用 AI 辅助检查遗漏项或生成 diagram 草稿，但不要让 AI 替你作主；
- 面试中优先白板/文字表达架构和 trade-off；
- 若要调用 AI，先说明你要验证的具体问题，例如“列出排行榜 range query 的热点与一致性风险”，而不是问“帮我设计整个系统”。

#### 45 分钟系统设计通用节奏

| 时间 | 做什么 |
| --- | --- |
| 0–5 分钟 | 澄清核心用户流程、非目标、规模、SLO、一致性 |
| 5–10 分钟 | API、数据模型、高层架构 |
| 10–25 分钟 | 深挖最关键读写路径与瓶颈 |
| 25–35 分钟 | 分片、缓存、异步、故障恢复、观测性 |
| 35–45 分钟 | trade-off、容量演进、安全/权限、总结 |

### 4.2 Video Game Score Leaderboard

**原始题目**：实体包括 players、games、friends、每个 `(player, game)` 的 high score；用户完成游戏后，展示与自己分数最接近的分数（大规模 range search）。

#### 需求澄清

- 是全局榜、好友榜还是都要？是否一个 player/game 只保留最高分？
- “closest scores” 返回按数值最接近的 K 个玩家，还是排行榜上下各 K 名？
- 分数是否会下降、撤销、作弊审计？
- 分数更新后读取能否最终一致？

#### 数据模型与架构

```text
Score Write API
  -> validation / anti-cheat
  -> durable score store (player_id, game_id -> high_score)
  -> event log
  -> leaderboard index keyed by game_id, ordered by (score, player_id)

Leaderboard Read API
  -> cache / ordered index range query
  -> fetch neighbors around player's current score
  -> optional friend filter / privacy filter
```

#### 核心选择

- **单 game 排行榜规模适中**：Redis Sorted Set，按 score range / rank 查询简洁、低延迟。
- **单 game 极大或跨区域**：按 `game_id` 分片；超热门 game 再按 score range 或时间窗口拆分，结合全局元数据路由。
- **持久化**：关系型/KV 存 player 的权威最高分；排序索引可由 event stream 异步更新和重建。
- **closest score 查询**：先取用户当前 score，再在有序索引用 range / rank 查其相邻 K 个；需要解释并列分数的 tie-break。

#### Failure / trade-off

- 权威库与 Redis 索引短暂不一致：展示略旧排名通常可接受；结算奖励场景则读权威数据或做同步写。
- 热点游戏：缓存热榜、请求限流、读副本；不要把所有热门游戏塞进单实例。
- 好友榜：friend graph 展开成本高，可缓存 friend IDs 或对候选近邻再过滤；完整好友榜可异步预计算。

### 4.3 Ride Share System

**原始题目**：Ride share system，细节未给出。

#### 先界定 MVP

- Rider 创建行程请求，driver 上报位置/在线状态，系统匹配司机；接单、取消、行程状态、支付不必一次全部深入。
- 问清规模：城市数量、每秒位置更新、最大匹配延迟、ETA 精度。

#### 高层架构

```text
Rider App -> Trip API -> Trip Store / State Machine
Driver App -> Location Ingestion -> Geo Index / Stream
Matching Service -> Candidate Drivers -> Offer / Reservation
                                    -> Driver Notification

Events -> durable log -> billing, analytics, fraud, replay
```

#### 深挖点

- **地理索引**：H3/S2/geohash；从 rider cell 向邻近 cell 扩张找司机。
- **匹配一致性**：给司机短时 reservation；Compare-and-Set 确保一位司机不会同时接两单。
- **位置流**：高频位置用流系统和内存 geo index；历史轨迹异步落湖/仓。
- **故障处理**：driver 离线、推送丢失、用户取消、匹配超时、重复请求 idempotency key。
- **公平与成本**：最近司机不一定是最佳司机；可加入 ETA、司机接单率、供需、绕路成本，但要说明规则可解释性。

#### ML Infra 加分点

可自然提到 ETA/model serving：在线特征新鲜度、模型版本 rollout、fallback heuristic、模型异常时的 circuit breaker、预测日志与回放。但不要让 ML 部分抢走匹配系统主线。

### 4.4 Notification System

**原始题目**：Design Notification System；讨论 storage、fanout、高流量、reliability。

#### 推荐设计

```text
Producer -> Notification API -> Durable Event Log
                           -> Preference / Policy Filter
                           -> Fanout Workers -> Per-user inbox store
                                              -> Delivery queues by channel
                                              -> Push / email / SMS providers
```

#### 必讲 trade-off

- **Fanout-on-write**：读快，适合普通用户；名人有百万粉丝时写放大严重。
- **Fanout-on-read**：写轻，读时合并，适合高 fanout 账号；读取更复杂。
- **Hybrid**：普通账号 write fanout，超级账号 read fanout。
- 可靠性：at-least-once 投递 + idempotency key；DLQ；重试与指数退避；provider callback。
- 用户偏好、静默时间、去重、频控与合规退订必须成为数据模型的一部分。

### 4.5 Status Search with AND / OR

**原始题目**：设计 status search，支持 AND/OR。

#### 基础架构

```text
Status Write -> canonical status store -> indexing pipeline -> inverted index
Search API -> query parser -> boolean planner -> index retrieval -> ranking -> results
```

#### 核心细节

- 倒排索引：`term -> sorted posting list(status_id, metadata)`。
- `AND`：对多个有序 posting list 做交集，优先从最短 list 开始。
- `OR`：多路归并求并集并去重。
- 支持括号与优先级：parse 成 AST，再执行 query plan。
- 排序/分页：按相关性、时间、社交关系；使用 cursor，避免 offset 深分页。
- 新鲜度：写入主库后异步索引会有延迟；若必须 read-your-writes，可短期从主库合并或使用同步索引路径。

#### 追问

权限过滤应在查询阶段还是结果阶段？通常要在索引中携带可过滤元数据，避免先取大量无权限结果；但复杂 ACL 可能需要后过滤和 over-fetch。

---

## 5. Behavioral Question 题库与答法

### 原始题目汇总

- 最有影响力 / 最自豪的项目（most proud / biggest impact）。
- 和 teammate 的 disagreement。
- 一次失败经历。
- 如何推动跨团队合作。
- 模糊需求（ambiguous requirements）。
- 收到 critical feedback 后如何处理。
- Phone screen 中的项目深挖与背景讨论。

### E5 用 STAR-L 回答

```text
Situation：背景、业务/技术约束和你的角色
Task：你具体负责的决策或交付，不是团队总目标
Action：你如何分析、对齐、执行、处理分歧
Result：量化业务/工程结果；没有数字则说可验证变化
Learning：之后如何改变机制、流程或判断方式
```

每个故事准备 2 分钟版和 5 分钟深挖版。面试官常追问：为什么是你来做？有哪些替代方案？谁不同意？你如何验证？如果重来会怎样？

### 与个人经历最匹配的故事方向

| BQ 主题 | 可优先使用的经历方向 | 要准备的证据 |
| --- | --- | --- |
| 最大影响力 | Uber vector feature serving；Feature Store 插件化；OCI cost control | 延迟/CPU 改善、用户或服务范围、你的 ownership |
| 跨团队推动 | Feature Store onboarding / deprecation；OCI data contracts 与 Langfuse onboarding | 分歧点、决策机制、依赖团队、落地结果 |
| 失败 / 反馈 | 选择一个真实但可控的项目失误 | 早期信号、承担责任、补救、机制改进 |
| 模糊需求 | AI cost attribution 或 LLM observability | 如何把模糊目标变成 API、指标、phase plan |
| 技术分歧 | Cassandra immutability、safe deployment、shadow testing | options、实验/数据、最终 trade-off、如何保留关系 |

不要编造影响数字。若数字受保密限制，可用比例、数量级或具体的工程结果替代。

---

## 6. 训练计划：如何使用这份题库

### 普通 Coding

每题按以下节奏练习：

1. 3 分钟澄清与口述方案。
2. 20–30 分钟独立编码。
3. 5 分钟设计边界测试。
4. 5 分钟讲扩展性 follow-up。

优先顺序：字符串计算器 → 二分 → 前缀和子数组 → 图/依赖 → LRU/Rate Limit → 版本化 in-memory DB。

### AI Coding

至少练三次完整模拟，每次 40–45 分钟：

1. Friend recommendation：正确性、Top K、100k 用户压力思路。
2. Card game：澄清不完整规则、状态建模、固定 seed benchmark。
3. Word subset 或 maze：AI 协作、代码审查、复杂度解释。

练习目标不是 prompt 写得长，而是能做到：每次调用 AI 前知道要验证什么；每次调用后能指出是否满足需求；对性能数字不做无依据的结论。

### System Design

每题用 45 分钟白板模拟：Leaderboard、Ride Share、Notification、Status Search。结束后回答三道固定追问：

1. 最大热点在哪里，如何降级？
2. 哪些数据必须强一致，哪些允许最终一致？
3. 未来 10 倍规模时最先替换哪个组件，为什么？

---

## 7. 面试前检查清单

- [ ] 能在白板上写出 BFS、拓扑排序、前缀和、LRU、二分的正确模板。
- [ ] 能解释 point-in-time read / version history 的数据模型与 TTL 交互。
- [ ] 能写出 friend recommendation，且不会在 100k 用户上做全量两两比较。
- [ ] 能说明 card game 的题意缺失处，并用固定随机种子做分层 benchmark。
- [ ] 能设计 ordered leaderboard 的写路径、range read、缓存与一致性策略。
- [ ] 能讲清 Notification 的 fanout-on-write / fanout-on-read / hybrid 取舍。
- [ ] 有 5 个 STAR-L 故事，并准备好数据、冲突、失败和追问。
- [ ] 知道 AI 使用边界：遵守规则、主导判断、限制运行、以小测试验证。
