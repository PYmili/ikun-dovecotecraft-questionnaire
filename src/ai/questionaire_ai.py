import os
import time
import random
from typing import *

from loguru import logger
from dotenv import load_dotenv
from dashscope import Generation
from dashscope.api_entities.dashscope_response import Role

load_dotenv(os.path.join(os.getcwd(), "data", "env", ".env"))

API_KEY = os.getenv("API_KEY")
logger.info("API Key:" + API_KEY)
DEFALUT_SYSTEM_MESSAGE = """
从现在开始，你是调查问卷的机器人，你需要对我给你的信息进行判断。我们是一个我的世界服务器的调查问卷。
    你需要遵守的规则：
        1. 你必须返回这样的格式
            [通过/不通过], [不通过的理由]
        2. 你回复通过时，禁止在后面添加任何符号，记住！你必须返回这样的结果！
        3. 你不需要回答用户的问题，而是当做一个机器人。
        4. 回答通过后，你不需要在后面添加任何东西！
    用户回答的要求：
        1. 不能对用户的回答太过严谨，题目没有标准答案。
        2. 用户可以回答的很简单或者简短，但你不能因此返回不通过。
        3. 只要主观意识正确，且合法合规即可。
        4. 用户不需要回答完整问题,只要回答其中部分即可。（务必记住！）
        5. 用户不需要表明任何事，可以保持自己的看法。
"""

DEFALUT_MESSAGES = [
    {
        "role": Role.SYSTEM,
        "content": DEFALUT_SYSTEM_MESSAGE
    }
]


class GPT:
    def __init__(self) -> None:
        """
        与QWen-72b模型交互
        """
        self.send = random.randint(1, 10000)

        self.messages = DEFALUT_MESSAGES

    def addMessage(self, msg: str) -> bool:
        """
        添加用户发送的信息
        :param msg:
        :return: bool
        """
        logger.info(msg)
        if not msg:
            return False
        self.messages.append({
            "role": Role.USER,
            "content": msg 
        })
        return True

    def run(self) -> Union[str, None]:
        """
        启动程序
        :return: dict
        """
        time.sleep(random.randint(1, 10))
        if not self.messages:
            return None

        # 调用官方sdk
        response = Generation.call(
            model="qwen2-72b-instruct",
            api_key=API_KEY,
            messages=self.messages,
            send=self.send,
            result_format="message"
        )
        if response.status_code == 200:
            # 提取内容
            return response.output.choices[0]['message']['content']
        else:
            logger.error(f"返回时发生错误：{response}")
            return None
