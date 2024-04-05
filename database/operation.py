import pymysql
from loguru import logger

HOST = "47.108.64.239"
PORT = 0
USER = "root"
PASSWORD = "pymili_blog_mysql"
DATADASE = "ikun_questionnaire"


class DataBaseConnection:
    def __init__(
            self,
            _host: str = HOST,
            _port: int = 3306,
            _username: str = USER,
            _password: str = PASSWORD,
            _database: str = DATADASE,
            charset: str = "utf8mb4"
        ) -> None:
        """
        对远程mysql数据库的操作
        params:
            _host: str 远程数据库地址
            _port: int 数据库端口
            _username: str 用户名
            _password: str 用户密码
            _database: str 数据库名称
            charset: str 编码
        """
        self.host = _host
        self.port = _port
        self.user = _username
        self.password = _password
        self.database = _database
        self.charset = charset
        self.connection = None
        self.cursor = None

    def __enter__(self) -> pymysql.connect.cursor:
        self.connection = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.database,
            charset=self.charset
        )
        self.cursor = self.connection.cursor()
        return self.cursor
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not all([self.connection, self.cursor]):
            return
        self.connection.commit()
        self.cursor.close()
        self.connection.close()
        
