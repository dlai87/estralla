# ML Infra 软件工程师刷题大纲

适用于以 Feature Store、ML Serving 为核心方向，Training 为辅助方向的 ML Infra 软件工程师面试。优先完成标记为“核心”的题目；总量约 180 题即可。

## 刷题进度

- 已完成：3 题
- 当前模块：数组、哈希、双指针
- 最近完成：2026-09-19 — Valid Anagram（`code/valid_anagram.py`，已批阅通过）

## 1. 数组、哈希、双指针（25 题）

- [x] Two Sum（2026-09-19）
- [x] Contains Duplicate（2026-09-19）
- [x] Valid Anagram（2026-09-19）
- Group Anagrams
- Top K Frequent Elements
- Product of Array Except Self
- Valid Sudoku
- Longest Consecutive Sequence
- Valid Palindrome
- Two Sum II
- 3Sum
- Container With Most Water
- Trapping Rain Water
- Best Time to Buy and Sell Stock
- Maximum Subarray
- Merge Intervals
- Insert Interval
- Non-overlapping Intervals
- Sort Colors
- Subarray Sum Equals K
- Longest Consecutive Sequence
- **核心：Longest Substring Without Repeating Characters**
- **核心：Minimum Window Substring**
- **核心：Sliding Window Maximum**
- **核心：Find All Anagrams in a String**

## 2. 链表、栈、队列（20 题）

- Reverse Linked List
- Merge Two Sorted Lists
- Linked List Cycle
- Reorder List
- Remove Nth Node From End of List
- Copy List with Random Pointer
- Add Two Numbers
- Merge K Sorted Lists
- LRU Cache
- Valid Parentheses
- Min Stack
- Evaluate Reverse Polish Notation
- Generate Parentheses
- Daily Temperatures
- Car Fleet
- Largest Rectangle in Histogram
- Implement Queue using Stacks
- Design Circular Queue
- **核心：LRU Cache**
- **核心：Merge K Sorted Lists**

## 3. 二分查找、堆与排序（18 题）

- Binary Search
- Search Insert Position
- Find First and Last Position of Element
- Search in Rotated Sorted Array
- Find Minimum in Rotated Sorted Array
- Find Peak Element
- Koko Eating Bananas
- Capacity To Ship Packages Within D Days
- Median of Two Sorted Arrays
- Kth Largest Element in an Array
- K Closest Points to Origin
- Find Median from Data Stream
- Task Scheduler
- Meeting Rooms II
- Merge K Sorted Lists
- Top K Frequent Words
- **核心：Find Median from Data Stream**
- **核心：Kth Largest Element in an Array**

## 4. 树、Trie（25 题）

- Invert Binary Tree
- Maximum Depth of Binary Tree
- Diameter of Binary Tree
- Balanced Binary Tree
- Same Tree
- Subtree of Another Tree
- Lowest Common Ancestor of a BST
- Lowest Common Ancestor of a Binary Tree
- Binary Tree Level Order Traversal
- Binary Tree Right Side View
- Count Good Nodes in Binary Tree
- Validate Binary Search Tree
- Kth Smallest Element in a BST
- Construct Binary Tree from Preorder and Inorder
- Binary Tree Maximum Path Sum
- Serialize and Deserialize Binary Tree
- Implement Trie
- Design Add and Search Words Data Structure
- Word Search II
- **核心：Serialize and Deserialize Binary Tree**
- **核心：Binary Tree Maximum Path Sum**

## 5. 图、并查集与拓扑排序（25 题）

- Number of Islands
- Clone Graph
- Max Area of Island
- Pacific Atlantic Water Flow
- Surrounded Regions
- Rotting Oranges
- Walls and Gates
- Course Schedule
- Course Schedule II
- Graph Valid Tree
- Number of Connected Components
- Redundant Connection
- Accounts Merge
- Evaluate Division
- Network Delay Time
- Cheapest Flights Within K Stops
- Word Ladder
- Alien Dictionary
- Min Cost to Connect All Points
- **核心：Course Schedule**
- **核心：Number of Islands**
- **核心：Network Delay Time**
- **核心：Union-Find 模板**

## 6. 回溯与动态规划（35 题）

### 回溯

- Subsets
- Combination Sum
- Permutations
- Word Search
- Palindrome Partitioning
- Letter Combinations of a Phone Number
- N-Queens

### 一维 DP

- Climbing Stairs
- House Robber
- House Robber II
- Coin Change
- Decode Ways
- Maximum Product Subarray
- Word Break
- Longest Increasing Subsequence
- Partition Equal Subset Sum

### 二维 DP

- Unique Paths
- Longest Common Subsequence
- Edit Distance
- Distinct Subsequences
- Interleaving String
- Best Time to Buy and Sell Stock with Cooldown
- Coin Change II
- Target Sum
- Regular Expression Matching

### 区间 / 高难度

- Longest Palindromic Substring
- Palindromic Substrings
- Burst Balloons
- **核心：Coin Change**
- **核心：Longest Increasing Subsequence**
- **核心：Word Break**
- **核心：Edit Distance**
- **核心：Partition Equal Subset Sum**

## 7. 面向 ML Infra 的设计型编程题（20 题）

这一部分不只刷 LeetCode，建议自己手写实现。

- LRU / LFU Cache
- Rate Limiter：token bucket、sliding window
- Consistent Hashing
- 线程安全的 Producer–Consumer Queue
- 延迟队列 / Task Scheduler
- 分布式 ID Generator
- 日志聚合中的 Top K
- Streaming median / percentile
- 滑动窗口聚合：sum、count、distinct count
- Time-series 数据的按窗口聚合
- 实现 Feature TTL 与过期淘汰
- Feature Store 的 point-in-time 查询
- Feature version / schema compatibility 校验
- 推理请求 batching
- 请求去重（request coalescing）
- 模型版本的灰度路由
- 熔断器 / retry with exponential backoff
- 有界队列与 backpressure
- 简化版的 DAG task scheduler
- 训练任务资源调度：CPU/GPU quota

## 推荐刷题顺序

```text
数组/哈希/双指针
→ 链表/栈/队列
→ 二分/堆
→ 树
→ 图
→ 回溯
→ DP
```

每个模块的“核心”题至少做三遍：

1. 第一次：独立思考并实现。
2. 第二次：一周后，限时 25–35 分钟。
3. 第三次：一个月后，脱离题目描述讲清思路和边界。

## Python 基础工具

主语言使用 Python 时，应熟练掌握：`dict`、`set`、`deque`、`heapq`、`bisect`、`collections.Counter`、`collections.defaultdict`、排序的 `key`、递归与迭代 DFS/BFS 模板。
