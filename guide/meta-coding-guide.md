# Meta Coding 面试指南

> 基于 `meta-raw-ex.txt` 的非官方论坛面经整理。原帖包含谐音题名、记忆不完整的题意，以及 Product SWE、MLE、Data Engineer 等不同岗位的信息。本指南只将能合理还原的内容列为高频方向；不确定的题目会明确标注。

## 1. 这类面试在看什么

多份面经的共同信号是：题目大多在 Easy/Medium 到 Medium 变体，难点是 **45 分钟内完成两题时的稳定执行**。高分不只是 AC，还包括：

- 先澄清输入、输出和约束，再写代码；
- 清楚说明为什么选某种算法及其复杂度；
- 主动设计边界测试并 dry run；
- 面试官追加规模、并发或生产场景时，能自然演进方案；
- 卡住时讲当前思路，请面试官校准，而不是沉默很久。

推荐时间分配（每题约 20 分钟）：3 分钟澄清与方案、12 分钟编码、3 分钟测试、2 分钟复杂度与 follow-up。

## 2. 题目地图与解题框架

| 题目 | 还原程度 | 核心方法 | 必测边界 |
| --- | --- | --- | --- |
| 二进制矩阵最短路，LC 1091 变体 | 高 | BFS + parent map 回溯路径 | 起终点不可走、无路、单格、8 方向 |
| Subarray Sum Equals K，LC 560 | 高 | prefix sum + `count[prefix]` | 空数组、负数、全 0、`target=0` |
| Local Minimum | 高 | 二分，利用相邻关系 | 单元素、相邻相等的定义 |
| Valid Palindrome II，LC 680 | 高 | 双指针；首次冲突时跳左/右 | 空串、单字符、两条分支都失败 |
| 删除最多 K 个字符成回文 | 高 | `memo(l,r,k)` 或 LPS | K 很大、重复子问题 |
| 岛屿大小是否存在 | 高 | DFS/BFS 预处理所有岛屿大小到 set | 没有岛、多个同大小、全水 |
| 树路径数字和，LC 129 | 高 | DFS，`next = current*10 + node.val` | 空树、深树、叶子判断 |
| Root-to-leaf 最小和路径 | 高 | DFS 回溯路径，记录最小和 | 单支树、负值、复制 path |
| 股票最大利润，LC 121/122 | 高 | 一次交易：历史最低价；多次交易：累加上涨 | 空/单元素、递减、平台价 |
| Mouse to Cheese | 中 | 黑盒移动下的 DFS/BFS + visited + 回退 | 无限网格、移动失败、是否要求最短路 |
| Round Trip 最低成本 | 高 | 一次扫描维护此前最小 departure | tie break、不能同日往返 |
| 合并两个有序且不重叠的 interval 数组 | 高 | 双指针 merge，再合并重叠区间 | 端点相接是否要合并、空数组 |
| 两链表拼接字符串是否相同 | 高 | 双指针按字符扫描，不必拼长字符串 | 空 node、长度不同、空串 node |
| Binary Tree Right Side View，或变体 | 中 | BFS 每层末元素 / DFS 优先右侧 | 空树、单支树 |
| Alien Dictionary | 高 | 建图 + 拓扑排序；处理非法前缀 | 环、无关字符、`abc` 在 `ab` 前 |
| Web Crawler | 中 | BFS/队列、URL 去重、同域过滤 | 规范化 URL、失败重试、并发边界 |
| LRU / Rate Limiter | 高 | HashMap+双链表 / Token Bucket | 淘汰、时间、并发、多机扩展 |

### 2.1 二进制矩阵最短路：从 BFS 到返回路径

原帖中出现“二维矩阵从左上到右下，0 可走、1 不可走；follow-up 打印路径”。

1. 无权图的最短路应选 BFS；DFS 仅能判断可达，不保证最短。
2. queue 中只存坐标，不要每个状态复制整个 path，避免空间爆炸。
3. 首次访问 `(nx, ny)` 时记录 `parent[(nx, ny)] = (x, y)`。
4. 到达终点后从终点沿 parent 反向回溯再 reverse。

复杂度：`O(rows * cols)` 时间和空间。若允许八方向移动，方向数组为八个偏移；应问清是否允许斜走。

### 2.2 前缀和：Subarray Sum Equals K

令 `prefix[i]` 为前 `i` 个元素之和。若 `prefix[j] - prefix[i] = k`，则 `(i, j]` 的和为 k。因此扫描到当前 `prefix` 时，累计此前出现过的 `prefix-k` 的次数。

```text
count = {0: 1}
prefix = answer = 0
for x in nums:
    prefix += x
    answer += count[prefix - k]
    count[prefix] += 1
```

为什么不能总用滑动窗口：数组含负数时窗口和不具备单调性。面试时主动点出这一点很加分。

### 2.3 Local Minimum：不是背二分模板

题目要找局部最小值时，先确认相邻值能否相等。若 `nums[mid] > nums[mid+1]`，右侧存在下降趋势，局部最小值可在右侧；反之在左侧。单元素就是答案。若允许相等，则必须定义“严格局部最小”还是“非严格局部最小”，二分条件也随之变化。

### 2.4 Palindrome：一个删除与 K 个删除

**一个删除**：双指针相向扫描；第一次不等时，只会有两个可能：删除左或删除右。分别检查剩余区间是否为回文。

**最多 K 个删除**：状态为 `(left, right, remaining_k)`：

```text
相等：can(left+1, right-1, k)
不等且 k > 0：can(left+1, right, k-1) or can(left, right-1, k-1)
```

加 memo 避免指数级重复递归。若面试官问复杂度，应以实际状态数说明 `O(n^2 * K)` 的上界，而不是误说 `O(n*K)`。

### 2.5 Islands API：预计算还是每次查询

题目不是“岛屿数量”，而是实现 `isSizeExist(int size)`。若 grid 静态，首次 DFS/BFS 遍历计算每座岛的面积，将面积写入 `HashSet`，查询为 `O(1)`。注意只能在一座岛 DFS 完毕后向 set 添加完整面积，不能在 DFS 内每访问一个格子就添加。

若 grid 会更新，应追问更新频率。单点 land/water 变更会让连通分量维护变难，可能需要离线处理、并查集（只适合增加）、或按批次重算。

### 2.6 Round Trip 最低成本：线性扫描与 tie break

已知 departure price `D[i]` 与 return price `R[j]`，约束 `i < j`。扫描 return 日 `j` 时，只需维护其前面最小的 departure price 和**最早**对应下标。

```text
best_departure = D[0], best_departure_index = 0
for return_index from 1 to n-1:
    candidate = best_departure + R[return_index]
    更新全局最优；同价时优先更早 departure，再优先更晚 return
    再用 D[return_index] 更新 best_departure
```

关键在于 tie break 的比较顺序。用一两个平价样例当场验证，而不要只凭直觉写条件。

### 2.7 Graph / Dependency / Web Crawler

见到“依赖”“顺序”“循环”先想到拓扑排序：

- Kahn BFS：入度为 0 的节点入队；最后处理数量不足则有环。
- DFS：三色状态（未访问、访问中、完成）；遇到访问中节点即有环。

Web crawler 是工程版图遍历：URL 去重、域名过滤、请求超时、速率限制、任务队列、内容解析解耦。先明确要求单机 demo 还是分布式 crawler；不要在需求没澄清时直接讲 Kafka 和几十个服务。

## 3. Production Coding Follow-up

### Cache

单机 LRU：`Map<key, node>` + 双向链表，get/put 都是 `O(1)`。follow-up 时依次讨论 TTL、容量按条数还是字节、热点、cache stampede、失效策略和多级缓存。

### Rate Limiter

Token Bucket 适合平均速率 + 允许短 burst：存 `tokens` 与 `last_refill_time`，请求到来时补 token，再判断是否允许。需要主动问限流维度：user、IP、API key、tenant、model endpoint 还是全局。

扩展到多机时，解释一致性哈希路由（简单但重分配问题）和 Redis/共享 KV（更准确但依赖外部存储）的取舍；存储不可用时应明确 fail-open 或 fail-closed 的业务理由。

## 4. 所有 Coding 题都应主动说出的测试

| 类别 | 至少一个测试 |
| --- | --- |
| 空输入 | `[]`、空字符串、空树、空图 |
| 最小输入 | 一个元素、一个节点、start==end |
| 重复数据 | 同值、重复边、同一 key 多次写入 |
| 边界数据 | 负数、0、最大值、溢出、端点相等 |
| 结构性异常 | 有环、断开图、非法前缀、无解 |
| 约束验证 | 返回路径满足相邻、所有 interval 未重叠、结果没有重复 |

说测试时要解释它要否定什么假设，例如：“我要用负数例子确认我没有错误地使用滑动窗口。”

## 5. 练习顺序

1. BFS path、prefix sum、二分、DFS tree path。
2. LRU、Token Bucket、Alien Dictionary、interval merge。
3. Versioned in-memory database：get/set/delete/TTL/get_when。
4. 每周一次 45 分钟两题 mock；练“开口说思路”和“自己设计测试”。

对于你的 ML Infra 目标，优先掌握 LRU、rate limit、版本化数据、图依赖和 crawler。这些题最容易延伸到 feature serving、backpressure、TTL、数据 lineage 与线上可靠性。

## 附录：从原始面经还原的 Coding 题目

本附录只基于 `raw/meta-raw-ex.txt`。题目编号和具体 API 在原帖中常被 NDA、谐音或记忆缺失遮蔽；以下是可用于练习的**还原版**，不是官方题面。

### A. Binary Matrix Shortest Path（高置信度）

```text
给定一个 0/1 二维矩阵，从左上角走到右下角。
值为 0 的格子可通过，值为 1 的格子不可通过。

1. 返回是否可达或最短路径长度（原帖未完全明确）。
2. Follow-up：返回/打印一条从起点到终点的路径。

请说明时间与空间复杂度。
```

原帖的明确线索是“二维矩阵从左上到右下，0 能走、1 不能走”“BFS 和 DFS 二选一”“打印 path 时用 parent map 节省空间”。练习时默认允许八方向移动；真实面试必须先问清方向规则。

### B. Count Subarrays with Sum Equal to Target（高置信度）

```text
给定整数数组 nums 和整数 target，返回和恰好等于 target 的连续子数组数量。
数组可能包含负数。
```

原帖明确提到“数组和 target，求和等于 target 的 subarray 个数”和 prefix sum + hashmap。扩展练习：若要返回最长长度或具体区间，如何改变 map 中保存的信息？

### C. Find a Local Minimum（高置信度）

```text
给定数组 nums，返回任一局部最小值的下标。
局部最小值与相邻元素的关系由面试官定义；请先澄清相邻元素是否可能相等。
要求优于 O(n) 的时间复杂度。
```

原帖说明它是 LC 162（Find Peak Element）的变体，但目标是 local minimum，追问单元素和相邻相等。

### D. Valid Palindrome after One Deletion, Then K Deletions（高置信度）

```text
给定字符串 s，最多删除一个字符，判断它是否能成为回文串。

Follow-up：若最多可删除 K 个字符，如何判断？请说明复杂度。
```

原帖可直接对应 LC 680，并记录了递归加 memo 的 follow-up。

### E. Island Size Existence API（高置信度）

```text
给定静态 0/1 grid，其中相邻陆地构成一座岛。
设计类/函数，支持 isSizeExist(size)，判断是否存在面积恰好为 size 的岛。

请优化多次查询的性能。
```

可选 follow-up：grid 动态更新时如何处理？原帖只要求静态 precompute。

### F. Sum Root-to-Leaf Numbers（高置信度）

```text
给定一棵二叉树，每个节点值为 0–9。
每条 root-to-leaf path 代表一个十进制数字；返回所有路径数字之和。
```

原帖明确标注为 LC 129。

### G. Minimum Root-to-Leaf Sum Path（高置信度）

```text
给定一棵二叉树，找出从 root 到任意 leaf 的节点值之和最小的路径，
并返回该路径的节点值列表。
```

注意此题返回 path 而非只返回最小和；练习回溯时必须复制最终结果。

### H. Best Time to Buy and Sell Stock（高置信度）

```text
给定每天的股票价格：
1. 可以进行任意次交易、但同一时刻最多持有一股时，求最大利润。
2. Follow-up：若最多只允许一次交易，求最大利润。
```

先澄清是否允许同日买卖、交易费和 cooldown；原帖只包含前两种经典版本。

### I. Robot Mouse Reaches Cheese（中置信度）

```text
机器人/老鼠从坐标 (0, 0) 出发。已知 API：
move(x, y) -> bool    # 尝试移动到相邻位置，成功返回 true
reachCheese() -> bool # 当前位置是否有奶酪

实现函数，判断是否存在一条路径使老鼠到达奶酪。
```

原帖未定义地图边界和 move 失败后的状态；必须在面试中澄清。若 API 需要真实移动，DFS 还要实现反向回退。

### J. Minimum Round-Trip Cost with Date Constraint（高置信度）

```text
给定等长数组 D 和 R：D[i] 是第 i 天出发价格，R[j] 是第 j 天返程价格。
选择 i < j，使 D[i] + R[j] 最小。
返回最小成本以及 (i, j)。
若成本相同，选择最早的 departure；若 departure 也相同，选择最晚的 return。

先给 O(n^2) 解，再优化到 O(n)。
```

原帖样例：`D = [10,7,8,3,6]`，`R = [5,4,10,7,5]`，答案为 `(3,4)`，成本 8。

### K. Merge Two Sorted Non-overlapping Interval Lists（高置信度）

```text
给定两个分别按 start 升序排列、且各自内部不重叠的 interval 数组。
合并它们并返回一个按 start 排序、彼此不重叠的 interval 数组。
```

需要问清 `[a,b]` 与 `[b,c]` 是否应该合并。

### L. Compare Strings Formed by Two Linked Lists（高置信度）

```text
给定两个单链表，每个 node.val 是一个字符串。
判断将每个链表的字符串按节点顺序拼接后，两个整体字符串是否相同。
要求避免不必要地构造超长新字符串。
```

用两个 node 指针和 node 内字符 offset 扫描即可。

### M. Alien Dictionary（高置信度）

```text
给定按未知字母顺序排序的一组单词，推导一个可能的字符顺序。
若顺序无效（有环或非法前缀），返回空结果。
```

原帖明确提及 Alien Dictionary，并要求精确估计时间与空间复杂度。

### N. Web Crawler（中置信度）

```text
从一个起始 URL 开始爬取页面，只抓取同一 host 的链接。
每个 URL 最多访问一次；返回已访问 URL 集合。

Follow-up：若要多 worker、高吞吐和容错，如何设计？
```

原帖仅称“很多 node 去挖网页”，未说明具体 API；先写单机 BFS/DFS，再讨论分布式。

### O. 其他能识别但题面不足的记录

- “LC 65”：应为 Valid Number，但原帖未给具体输入规则；
- “LC 26”“LC 329”“LC 121”“LC 199”“LC 11”“binary tree diameter”：题号/题名可辨，但未给变体；
- “数据清理，找出标注错误的人”：更可能是 Data/MLE coding，涉及 pandas 和标注质量，具体 schema 未给；
- “手写 attention 并分析复杂度”：MLE coding，题面未明确是否包含 multi-head、mask 或 softmax 数值稳定性。

这些可作为补充练习，但不应假定原帖就是标准 LeetCode 原题。
