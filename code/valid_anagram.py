"""

下一题：Valid Anagram
请在 code/valid_anagram.py 中实现：
def is_anagram(s: str, t: str) -> bool:
    pass
如果 t 是 s 的字母异位词，返回 True；否则返回 False。
is_anagram("anagram", "nagaram")  # True
is_anagram("rat", "car")          # False
is_anagram("", "")                # True
is_anagram("aacc", "ccac")        # False
目标：时间复杂度 O(n)。尽量不要直接用排序，练习哈希计数。
"""

def get_char_count(s): 
    counter = {}
    for c in s: 
        if c not in counter:
            counter[c] = 0 
        counter[c] += 1
    return counter

def is_anagram(s: str, t: str) -> bool:
    counter1 = get_char_count(s)
    counter2 = get_char_count(t)
    if len(counter1) != len(counter2):
        return False 
    for key, val in counter1.items():
        if key not in counter2:
            return False 
        if val != counter2[key]:
            return False
    return True 