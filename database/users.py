from typing import *

from loguru import logger

from operation import DataBaseConnection


# 写到一半，我发现，我吃饱撑着了。
class Users(DataBaseConnection):
    def __init__(self) -> None:
        super().__init__()

    def get_all_usernames(self) -> Union[List[str], None]:
        """
        获取所有用户名
        """
        query = "SELECT username from users"
        try:
            self.cursor.execute(query)
            return [row[1] for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(e)
            return None
    
    def __enter__(self):
        super().__enter__()
        return self