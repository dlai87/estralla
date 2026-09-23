"""
第一题：Two Sum
请在 code/two_sum.py 中实现：
def two_sum(nums: list[int], target: int) -> list[int]:
    pass
给定整数数组 nums 和整数 target，返回两个不同元素的下标，使其对应值之和等于 target。
约束：
- 每个输入保证恰好有一个答案。
- 同一个元素不能使用两次。
- 下标顺序不限。
- 目标时间复杂度：O(n)。
- 不要使用排序后双指针，因为那会丢失原始下标；请使用哈希表。
示例：
two_sum([2, 7, 11, 15], 9)     # [0, 1]
two_sum([3, 2, 4], 6)         # [1, 2]
two_sum([3, 3], 6)            # [0, 1]
"""


def two_sum(nums: list[int], target: int) -> list[int]:
    value_to_index = {}

    for i, cur_num  in enumerate(nums): 
        cur_num = nums[i]
        pre_num = target - cur_num
        if pre_num in value_to_index:
            return [value_to_index[pre_num], i]
        value_to_index[cur_num] = i 

    return [] 

