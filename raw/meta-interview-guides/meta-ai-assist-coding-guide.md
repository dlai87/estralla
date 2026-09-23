# Meta AI Assist Coding 面试指南

> 这是基于 `meta-raw-ex.txt` 的非官方整理。面经中的名称包括 AI-enabled、AI-native、AI-assist、AI-structured 等，平台和规则会随岗位、面试官和时间变化。以面试开始时面试官宣布的规则为准。

## 1. AI Assist Coding 是什么，不是什么

它不是“把题目粘给 AI，等它完成”。原帖中常见的真实考察是：

- 你能否读懂既有 codebase、测试和 benchmark；
- 你是否先弄清目标、评分标准和性能瓶颈；
- 你是否能给 AI 足够精确的约束，并审查输出；
- 你能否在小内存、低 CPU、限时的 CoderPad 环境中避免把自己卡死；
- 你是否能解释最后的代码、复杂度、测试和取舍。

**合规边界**：只有在面试官明确允许时使用 AI；按公布规则操作。不要试图规避平台限制、隐藏 AI 使用、复制无法解释的答案，或向未批准工具输入敏感信息。面试官可能实时看到你所有输入，也会针对 AI 生成内容深挖。

## 2. 原帖中出现的题型

| 题目 | 典型任务 | 核心能力 |
| --- | --- | --- |
| Maze Solver | 修 bug、BFS、单向门、钥匙/门、炸弹 | 阅读测试、状态空间设计 |
| Max Unique Characters | 从 words 选无重字符 subset，最大化字符数 | bitmask、回溯、DP、性能优化 |
| Friend Recommendation | 100k users / 1.5M friend pairs；再评估效果 | 图算法、Top-K、压测和 ML 评估 |
| Card Deck | 选 3 张和为 15，补牌，benchmark 策略 | 状态建模、搜索/启发式、固定种子评测 |
| ParanoidEcho / Word Container | 给 brute-force，优化并跑 benchmark | profiling、Trie vs HashSet、实验设计 |
| Compiler Optimization | 推断并优化解释器/编译器的时间与内存成本 | 需求澄清、避免编造规则 |
| 工序/工作台/工人排程 | 在时限下最大化订单得分 | 建模、调度、约束优化 |
| Data Engineer 全栈题 | 业务问题→建模→SQL debug→Python 清洗 | 数据质量、推理与 AI judgment |

## 3. 通用执行流程

### 3.1 面试开始先做什么

先向面试官确认：

```text
我先确认 AI 的允许范围、评分标准、可运行的测试层级和时间限制。
我会先让代码在小样例正确，再根据实际测量决定是否优化；
大 benchmark 只在我们确认后运行。
```

然后先阅读 README、现有代码、测试和 benchmark。不要让 AI 在你没弄清 API 前就修改一堆文件。

### 3.2 一个短、可用、合规的 session prompt

在允许使用 AI 的情况下，可手动输入类似下面的约束；不要把它当作固定咒语，应按题目删减：

```text
这是一个限时编码面试，资源有限。先阅读题目、现有代码和测试。
请用不超过五点给出：目标、明确约束、未知假设、复杂度目标、实现计划。
先实现正确且高效的方案；只运行小型确定性测试，所有命令加超时。
不要启动后台任务、并行 benchmark 或全量随机测试，除非我明确要求。
如果规格没有给出，请列为待澄清，不要自行发明常量、成本模型或评分规则。
修改前说明将改动哪些文件；修改后说明如何验证，并指出风险。
```

这个 prompt 的目的不是把判断外包，而是避免 AI 自动跑满资源、乱猜规格或生成大量无关输出。

### 3.3 每一步如何和 AI 交互

| 阶段 | 你负责什么 | 可问 AI 的问题 |
| --- | --- | --- |
| 澄清 | 定义验收、规模、不可假设的规则 | “列出题目中会影响算法选择的 5 个待确认问题。” |
| 方案 | 选择数据结构与复杂度目标 | “对比 A/B 两个方案的时间、空间、实现风险；不要写代码。” |
| 实现 | 指定 API、限制改动范围 | “仅实现 `solve()`，保留现有接口；先给 patch 计划。” |
| 测试 | 选择能否定假设的最小用例 | “为这个状态转移列 6 个边界测试以及各自捕获的 bug。” |
| 优化 | 基于测量解释 bottleneck | “根据这组 profile 数据，列出最可能的瓶颈和验证每项的最小实验。” |
| 收尾 | 口头解释、删除 scratch、复查 | “审查这段最终代码的 correctness、复杂度、未覆盖边界。” |

你需要能用自己的话解释每一个采纳的建议。若不能解释，就不要采用。

## 4. Maze Solver：最明确的高频题

原帖记录了 4–5 个递进部分，常见是“修测试/打印 → BFS bug → 单向门 → 钥匙门 → 炸弹”。部分一可能禁止 AI，之后才允许。

### 4.1 Q1：路径打印不应覆盖起点和终点

问题通常不是算法，而是打印函数将所有 path cell 打成 `*`，覆盖了 start / end。先读 test 的期望，按显示层修复，不要改搜索逻辑。测试：路径含 start/end、路径为空、start=end。

### 4.2 Q2：BFS 无限循环 / 超时

根因通常是缺少 visited，或只在 dequeue 时标记导致同一格被重复入队。正确做法是在 **入队时** 标记 visited。说明这同时保证无权图中的最短路径首次到达性质。

### 4.3 Q3：单向门 / Chute

`>` 和 `<` 等符号会限制可从哪个方向穿越，或进入后强制移动。不要让 AI 只写“看到 `>` 就向右”；必须先定义：

- 限制的是进入方向、离开方向，还是自动传送？
- 该目标格是墙时能否进入？
- 方向限制与边界/墙怎样组合？

最清晰的实现是让 `can_move(from, to, direction)` 集中处理格子语义；BFS 不要分散地写特殊 if。

### 4.4 Q4：钥匙与门

仅用 `(row, col)` 做 visited 是错误的：同一位置、持有不同钥匙集合是不同状态。状态应为：

```text
(row, col, key_mask)
```

小写 key 映射 bit；经过对应大写门时检查 bit；捡 key 时更新 mask。`visited` 也存完整 state。若键种类多、地图大，解释状态数会随 `2^K` 增长，必要时限制 key 数或使用更紧凑编码。

### 4.5 Q5：炸弹改变地图

动态地图的状态必须包含足够信息表示环境变化，例如已触发的炸弹集合/被摧毁墙的集合（若数量小可 bitmask）。若题目说炸弹只影响一次、效果可由位置推导，才能简化状态；不能把一个全局 mutable grid 用于 BFS 的所有分支，否则不同路径会互相污染。

### 4.6 Maze 的最小 AI 提示

```text
先只阅读 maze 的 README、测试和 move/print 代码。
请给出每一问的状态定义、转移规则、visited key 和最小测试；
不要重写项目，不要运行全量测试。若门的语义不明确，先列问题。
```

## 5. Maximum Unique Characters：从回溯到 DP

**题意**：选一个 word subset，任意被选 words 之间不能共享字符，最大化所覆盖的字符数，某些版本要求返回 subset 本身。原帖提到前两组测试容易、后两组有数千到上万 words，需要性能优化。

### 5.1 第一步：预处理

若字符集为 a–z：将每个 word 转为 26-bit mask。word 自身有重复字符时，根据题意要么剔除，要么需先澄清。两个 word 兼容当且仅当：

```text
(mask_a & mask_b) == 0
```

预处理时去掉空贡献、内部重复和完全重复的 mask；可按长度降序辅助 branch-and-bound。

### 5.2 小规模：DFS / Backtracking

递归维护 `index, used_mask, current_length, chosen_words`。能选则选，也可跳过。正确但最坏 `O(2^n)`；不要在数千 word 上盲目全搜。

### 5.3 大规模：理解“精确”的边界

这本质上是 set packing，通用情况 NP-hard；不能承诺任意 10k words 都有快速精确解。若字符集固定且较小，可尝试：

- 用 `used_mask` 作 DP/memo key；相同 mask 只保留一个最好 predecessor；
- 用 predecessor 指针重建 subset，而不是每个 DP state 存完整 list；
- branch-and-bound：若“当前长度 + 剩余可能上界”不超过 best，剪枝；
- 仅在题目允许近似时使用 greedy，并明确不保证最优。

重要：先看 benchmark 的成功标准。若只要达到某个长度、在限定时间内返回有效 subset，策略与“严格最优”不同。

### 5.4 面试中可说的性能判断

```text
当前 bottleneck 不是位冲突检查，而是候选组合数量。
我先用 mask 消除重复字符检查，再以小测试验证正确性；
如果 benchmark 仍慢，我会测量搜索节点数，
然后选择 memo 或上界剪枝，而不是先猜 Trie 一定更快。
```

## 6. Friend Recommendation：图算法与评估

**原始约束**：约 100k users、1.5M user-user pairs，提供三组 test。目标是为用户推荐新朋友。

### 6.1 可交付 baseline

建立 `user -> set(friends)` 邻接表。对 user `u` 的每个好友 `f`，遍历 `f` 的好友 `v`；跳过自身和已有好友，对 `v` 的共同好友数加一。按 `(-mutual_count, id)` 取 Top K。

单次复杂度是 `sum(deg(f) for f in N(u))`；避免构造 `V x V` 矩阵或对所有用户两两比较。只取 K 个结果时，用 min-heap 避免完整排序。

### 6.2 要问的产品问题

- 好友是否无向？是否有 block / privacy / region 规则？
- 推荐 K 个还是全部？相同分数如何排序？
- 可否推荐热门用户作为 fallback？
- 高 degree 用户怎样避免候选爆炸？

### 6.3 “如何证明推荐表现好”的 follow-up

原帖给出的方向是 hold-out data 和 recall/precision。更完整回答：

1. 以时间切分历史关系；隐藏后续新建立的好友边，不能随机泄漏未来。
2. 用隐藏边做 ground truth，评估 Precision@K、Recall@K、MAP/NDCG；按活跃度、地区和新用户分桶。
3. 离线好不等于线上好；A/B 看接受/建立关系、长期留存和 block/负反馈等 guardrail。
4. 防止 popularity bias 和 filter bubble；检查不同社区的覆盖与公平性。

## 7. Card Deck：不要在规格不清时写搜索

原帖记忆存在差异：36 张 1–9 卡、可见约 15/16 张、每次选 3 张和为 15、补 3 张、清空 12 组即赢，且需要新建 >1k games benchmark。

### 7.1 首先澄清

- 每种卡的数量？补卡的顺序/随机性是否已知？
- 无合法三元组时是否立即失败？能否替换/重排？
- 优化 win rate、平均步数、最坏时间还是全部？
- benchmark 是否固定 seed？是否有每局或总时间限制？

### 7.2 分层实现

1. **动作生成**：用可见 card 的 value counts 枚举和为 15 的三元组，避免按位置三重循环产生重复。
2. **基础策略**：对合法动作按启发式评分，例如保留更多未来可组合值；必须称为 heuristic，不是假装最优。
3. **可预测牌堆**：若补卡序列确定，用 memoized search；state 包含 visible counts、剩余牌/位置。
4. **随机牌堆**：固定种子重复模拟，比较策略的 win rate 与 runtime；采样/rollout 可用，但说明其随机性和时间上限。

### 7.3 Benchmark 设计

使用同一批 seed，按 20 / 100 / 1000 局分层运行；记录：games、wins、win rate、average time、P95 time、timeout count。不要只报告某次随机跑出来的“胜率提高”。

## 8. Compiler Optimization：规格不明时 AI 最危险

原帖案例中 AI 从样例中**臆测** `+/-` 代价为 1、`*//` 为 5，导致后续测试失败；题目没有给 universal cost 定义。

正确动作：

1. 读 `extract_time_and_mem_cost`、README、全部已见测试和调用方；
2. 分开列出“题目明确给出”“测试可证明”“我尚不知”的规则；
3. 早问面试官：cost model 是否在文档中定义，还是需要从某个文件读取？
4. 在规格清晰前，不接受 AI 给出的“行业通用定义”。

推荐 prompt：

```text
请只根据 README、函数签名和已提供测试列出可证明的语义。
把每个结论标为 [explicit]、[inferred] 或 [unknown]；
不得从常识推断 operator cost。先不要改代码。
```

这类题考的不是懂 compiler 术语，而是需求推理和拒绝无依据假设的能力。

## 9. ParanoidEcho / Word Container 与 Scheduling

### 9.1 给 baseline 做优化

原帖中面试官提供 brute-force、两个 benchmark；候选人对比 Trie 和 HashSet，发现 runtime 接近但 Trie 内存更多。正确过程是：读 benchmark 和 profile，说明 bottleneck；再比较数据结构的常数、内存、prefix query 是否必要；最后在相同输入上测量。

不要为了“使用 AI”而让 AI 想出 Trie 后立刻采用。一个好问题是：

```text
这里的操作是 exact word lookup、prefix lookup，还是 substring search？
分别比较 HashSet、Trie 和排序数组的时间、内存与实现风险；不要实现。
```

### 9.2 工序、工作台、工人熟练度的排程

该题细节不足，不能直接断言最优算法。先问订单是否可拆分、工序依赖是否 DAG、资源是否独占、是否允许抢占、目标是最大值还是 deadline 合规。

小规模可用状态搜索 / DP；若订单多、工序多，常见的是 greedy heuristic（例如按 deadline、价值密度、关键路径）或整数规划近似。高分答案会说明问题可能是 NP-hard，给出可交付 baseline 与改进方向，而不是承诺一个未证明的“最优贪心”。

## 10. Data Engineer AI-native Full Stack 变体

原帖中有一类连续 60 分钟案例：Business Case → Data Model → SQL Debug → Python 数据清洗。它与算法题不同，重点是判断力。

- **Business Case**：先问 4–6 个澄清问题，区分 vanity metric、增长/留存、用户满意和潜在伤害。
- **Data Model**：写清 fact table 的 grain，dimension 与 foreign keys，日期 partition，如何支持后续新增分析。
- **SQL**：不仅修语法；检查 INNER/LEFT join、fan-out、重复聚合、NULL、负值与 selection bias。原帖明确称某些环节 AI 不可用，必须遵守。
- **Python**：面对 malformed、orphan、schema change，跳过/记录坏数据而不是 crash；返回能回答业务问题的结构化 dict。

可用 AI 进行问题清单或脚手架 brainstorming，但最终文本/SQL/代码必须由你写入并能解释。

## 11. 面试结束前的 90 秒

1. 运行最小测试并口头说明覆盖什么。
2. 说明算法时间/空间，及最大规模的瓶颈。
3. 指出一个如果多 15 分钟会做的改进，不要假称已完成。
4. 确认没有 debug 输出、随机 seed 不可复现或改坏公开 API。

AI 是加速器，不是替身。最强信号是：你知道什么时候让 AI 生成、什么时候让它停下、什么时候必须由你判断。

## 附录：从原始面经还原的 AI Assist Coding 题目

以下题目由 `raw/meta-raw-ex.txt` 中明确标为 AI coding、AI-enabled coding、AI-native coding 或带 AI Assist 的连续题还原而来。每道题的 AI 使用范围可能不同；尤其 Maze 的第一问常被描述为禁止 AI。以现场规则为准。

### A. Maze Solver：五个递进问题（高置信度）

```text
项目已提供 maze solver、单元测试和可运行环境。通过修改代码使测试通过。

Q1. 路径打印：当前代码把路径全部打印成 `*`，请修复，保证起点和终点符号不被覆盖。
Q2. 搜索超时：BFS 在某些 maze 中无法结束。修复搜索逻辑。
Q3. 单向通道：maze 加入 `<` / `>` 等单向门；只能从指定方向进入或通过。
Q4. 钥匙与门：小写字母为 key，对应大写字母为 door；拿到 key 后才能通过 door。
Q5. （部分帖子提到）炸弹：踩到炸弹会移除其周围一定范围的墙；修改搜索以支持动态地图。
```

**从原帖能提炼出的验收点**：Q1 是显示层 bug；Q2 通常是缺少 `visited`；Q3 的门语义要按 test 确认；Q4 的 visited 不能只有坐标，必须包含 key state；Q5 不能用会污染所有 BFS 分支的全局 mutable grid。

### B. Maximum Unique Characters Subset（高置信度）

```text
给定一组 words，选择一个 subset，使任意两个被选 word 不共享字符，
并最大化所选 words 覆盖的总字符数。

返回最大值，或返回对应 subset（原帖不同版本不一致）。
后续测试可能包含数千到上万 words，并有严格的运行时间限制。
```

**需要先问**：字符集是否只含 a–z？单个 word 内重复字符是否允许？严格要求最优还是只要求高质量有效解？是否必须返回 subset？

**还原的优化方向**：word 转 bitmask；小数据 DFS/backtracking；大数据可做 mask DP/memo、dominance pruning、predecessor pointer 重建结果、branch-and-bound。原帖有人提到达到长度 36 后可剪枝，那是特定字符集/测试的上界，不可在没确认时硬编码。

### C. Friend Recommendation（高置信度）

```text
输入：users 列表与 friend pairs（user-user）。
为给定 user 推荐新的朋友。策略可包括 friend-of-friend 或 popular users。

测试包括约 100k users 与 1.5M friend pairs；
后续问题：如何证明你的 recommendation 表现良好？
```

**还原的 baseline**：用邻接 set 统计共同好友，排除自己和已有好友，取 Top K。不要在 100k 用户上全量枚举 user pairs。

**表现评估 follow-up**：按时间做 hold-out future friendships，离线评 Precision@K/Recall@K/MAP/NDCG，随后在线 A/B 看接受率、建立关系、长期 engagement 和负反馈。随机拆边可能泄漏未来信息，需主动避免。

### D. Card Deck：Pick Three to Sum 15（中置信度）

```text
有 36 张卡，卡面数值为 1–9。玩家看到桌面上的约 15 或 16 张卡；
每次选择 3 张数值和为 15 的卡并移除，再从剩余牌堆补 3 张（若可补）。
当 36 张卡都被消耗、即组成 12 组时获胜。

实现一个选择策略，并编写新的大规模 benchmark（原帖提到 >1k games，另有 10k case）。
```

**原帖不确定处**：每种数值的张数、补牌的随机/确定顺序、无合法组合时的规则、评分指标都没有统一记录。因此第一步应提出澄清问题；不能在这些假设未确认时声称策略最优。

### E. ParanoidEcho / Word Container 优化（低到中置信度）

```text
给定一个已有的 brute-force word container / echo 实现和 benchmark。
找出 runtime 与 memory bottleneck，优化实现；将新实现加入 benchmark，
并比较至少两个数据结构方案。
```

原帖候选人比较了 Trie 与 HashSet，并观察到 runtime 接近、Trie 占用更多内存。真实操作类型（exact lookup、prefix、substring 或其他）并未公开，必须先读 code/test，不能背“Trie 一定更快”。

### F. Compiler Time and Memory Cost（中置信度）

```text
给定若干 instruction 文件，例如：
res1 = var1 + var2
res2 = var3 - var4
res3 = res2 + var5
res = res1 + res3

实现 extract_time_and_mem_cost(instruction_path)，并使给定测试通过；
随后优化 compiler/interpreter 的时间和内存使用。
```

**关键还原**：原帖明确指出 operator cost 不能从样例擅自猜出，例如 `+/-` 为 1、`*//` 为 5 并不是 universal definition。先寻找显式 spec；若没有，立即请面试官澄清 cost model。

### G. Production Scheduling / Workstations（低置信度）

```text
有不同工序、工作台和工人。不同工序需要不同时间和工作台，
不同工人对不同工序有不同熟练度。
给定订单、截止时间和完成订单的分数，安排工作以最大化总分。
```

原帖没有说明抢占、依赖、资源容量、订单是否可拆分等决定算法的问题。还原题目的训练重点是建模与澄清，而非背一个固定算法。

### H. Data Engineer AI-native Full Stack Case（高置信度，但岗位特定）

```text
在同一个业务场景下连续完成四部分：
1. Business Case：写澄清问题，并把业务目标转为指标；
2. Data Modeling：设计 fact / dimension tables、grain、key 和 partition；
3. SQL：修复一份 AI-generated SQL 的语法和逻辑错误，再发现输出数据质量问题；
4. Python：读取两个有已知质量问题的数据源，清洗、关联、聚合并返回结构化结果。
```

原帖记录该轮约 60 分钟，每部分约 15 分钟；SQL 的“发现输出数据问题”阶段被明确禁止 AI 辅助。该限制必须严格遵守。

### I. 仅出现名称、无法安全还原的 AI Coding 记录

- `substring`；
- `echo`；
- “两个烙印，工作台不同工序做饭”的多问变体；
- “AI-native random friend recommender”的后续 score 实现。

它们可提示你练习：读测试、先澄清 score、做小 benchmark、解释性能；但原帖没有足够信息写成精确题面。
