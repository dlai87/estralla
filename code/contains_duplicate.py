"""
下一题：Contains Duplicate
请在 code/contains_duplicate.py 中实现：
def contains_duplicate(nums: list[int]) -> bool:
    pass
如果数组中任意值至少出现两次，返回 True；所有元素均不同则返回 False。
contains_duplicate([1, 2, 3, 1])  # True
contains_duplicate([1, 2, 3, 4])  # False
contains_duplicate([])            # False
目标时间复杂度 O(n)，空间复杂度 O(n)。
"""


def contains_duplicate(nums: list[int]) -> bool:
    seen = {}
    for i, num in enumerate(nums): 
        if num in seen:
            return True 
        seen[num] = i 
    return False 