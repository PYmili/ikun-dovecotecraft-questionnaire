import string
import random


def CreateKey(length: int = 64) -> str:
    """
    创建一个指定长度的随机字符串作为key值。

    参数:
    length (int): 随机字符串的长度，默认为16个字符。

    返回:
    str: 生成的keys值。
    """
    # 定义可能的字符集，包括字母（大小写）和数字
    characters = string.ascii_letters + string.digits
    
    # 使用random.choice生成指定长度的随机字符串
    key = ''.join(random.choice(characters) for _ in range(length))
    
    return key
