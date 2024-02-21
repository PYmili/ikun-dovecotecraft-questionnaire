import time
import random
from typing import *
from datetime import datetime

from loguru import logger
import dashscope
from dashscope import Generation
from dashscope.api_entities.dashscope_response import Role

API_KEY = "sk-7b059bf27cc54c1a9a101b2fa02b19c4"
DEFALUT_SYSTEM_MESSAGE = """
你现在是一个调查问卷的机器人，你需要对我给你的信息进行判断。
我们是一个服务器的调查问卷，我们会收集用户的问卷信息，你需要进行审核内容。
审核中，不必太过严谨，没有标准答案，但是必须合法，合规，遵守规定，尊重他人的。
我们不是考试，没有标准答案，只要主观意识正确，且合法合规即可。用户不需要完全回答上只要回答其中部分即可。
你必须返回这样的格式：通过或者不通过，如果不通过你就需要说出不通过的理由。
记住！你必须返回这样的结果！
"""


class GPT:
    def __init__(
            self,
            system_message: str = DEFALUT_SYSTEM_MESSAGE
    ) -> None:
        """
        与QWen-72b模型交互
        """
        self.send = random.randint(1, 10000)

        self.messages = [
            {
                "role": Role.SYSTEM,
                "content": system_message
            }
        ]

    def addMessage(self, msg: str) -> bool:
        """
        添加用户发送的信息
        :param msg:
        :return: bool
        """
        logger.info(f"添加信息：{msg}")
        if not msg:
            return False
        self.messages.append({"role": Role.USER, "content": msg})
        return True

    def run(self) -> Union[str, None]:
        """
        启动程序
        :return: dict
        """

        if not self.messages:
            return None

        time.sleep(random.randint(1, 3))
        # 调用官方sdk
        response = Generation.call(
            model="qwen-72b-chat",
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


if __name__ in "__main__":
    gpt = GPT()
    gpt.addMessage("""
    问题：如果你被反作弊系统误判封禁，你该如何向管理员沟通?(请以第一视角编辑一段求助信息)
    用户回复：仔细沟通
    """)
    print(gpt.run())
