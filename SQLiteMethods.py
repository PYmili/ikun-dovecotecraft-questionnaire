import os
import sqlite3
from typing import List, Any, Dict

from loguru import logger

MinecraftWhitelistManagerDB = os.path.join(os.getcwd(), "db", "minecraft_whitelist.db")
MinecraftAdminUserDB = os.path.join(os.getcwd(), "db", "admin.db")


class MinecraftWhitelistManager:
    def __init__(self, db_name: str=MinecraftWhitelistManagerDB) -> None:
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        # 用户表
        sql_create_table = '''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 用户id
                username TEXT NOT NULL, -- 用户名
                game_name TEXT NOT NULL, -- 游戏名
                registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 注册时间
                qq_number INTEGER, -- QQ号
                has_official_account TEXT, -- 是否持有官方账户
                current_status TEXT, -- 当前状态
                review_channel TEXT, -- 来自哪里
                friend_qq_number INTEGER DEFAULT NULL, -- 推荐人qq
                playtime INTEGER, -- 已玩游戏多久了
                technical_direction TEXT, -- 技术方向
                email TEXT UNIQUE, -- 邮箱
                passed_second_review TEXT DEFAULT 'No',  -- 是否被审核员通过
                questionnaire_answers TEXT,  -- 用户问答数据
                reviewed_by TEXT, -- 将用户通过审核的人
                audit_code TEXT NOT NULL -- 进群审核码
            );
        '''
        self.cursor.execute(sql_create_table)
        self.conn.commit()

    def insert_data(self, data_dict: Dict[str, Any]) -> bool:
        # 插入新数据
        if not data_dict:
            return False
        values = []
        for value in data_dict.values():
            if value is None:
                values.append("空")
            values.append(value)
        
        values_tuple = tuple(values)
        sql_insert = '''
            INSERT INTO users (username, game_name, qq_number, has_official_account, current_status,
                review_channel, friend_qq_number, playtime, technical_direction, email, questionnaire_answers, reviewed_by, audit_code) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        '''
        try:
            self.cursor.execute(sql_insert, values_tuple)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error inserting data: {e}")
            return False

    def update_data(self, user_id, data_dict: dict) -> bool:
        # 更新已有数据
        set_clause = ', '.join([f"{key} = ?" for key in data_dict.keys()])
        values = list(data_dict.values()) + [user_id]
        sql_update = f'''
            UPDATE users SET {set_clause} WHERE user_id = ?
        '''
        self.cursor.execute(sql_update, values)
        self.conn.commit()
        return True
    
    def add_reviewer_name(self, username: str, reviewer_name: str) -> bool:
        """
        添加对用户通过审核的审核员名称。
        """
        try:
            sql = """
                UPDATE users SET reviewed_by = ? WHERE username = ?
            """
            self.cursor.execute(sql, (reviewer_name, username))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"添加审核人名称时出现错误：{e}")

    def modify_passed_second_review_status_by_username(self, username, is_passed_second_review: str) -> bool:
        # 修改指定用户名的用户 被添加到通过二审
        if is_passed_second_review not in ('Yes', 'No'):
            return False
        
        try:
            sql_modify = '''
                UPDATE users SET passed_second_review = ? WHERE username = ?
            '''
            self.cursor.execute(sql_modify, (is_passed_second_review, username))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"通过二次审核时数据库错误：{e}")
            return False
    
    def is_email_registered(self, email: str) -> bool:
        # 检查指定的email是否已经注册过
        sql_query = "SELECT COUNT(*) FROM users WHERE email = ?"
        self.cursor.execute(sql_query, (email,))
        count = self.cursor.fetchone()[0]
        return count > 0

    def get_data_by_username(self, username: str) -> dict:
        # 通过用户名获取用户数据
        sql_query = "SELECT * FROM users WHERE username = ?"
        self.cursor.execute(sql_query, (username,))
        user_data = self.cursor.fetchone()
        if user_data:
            return {
                "username": user_data[1],
                "game_name": user_data[2],
                "registration_time": user_data[3],
                "qq_number": user_data[4],
                "has_official_account": user_data[5],
                "current_status": user_data[6],
                "review_channel": user_data[7],
                "friend_qq_number": user_data[8],
                "playtime": user_data[9],
                "technical_direction": user_data[10],
                "email": user_data[11],
                "passed_second_review": user_data[12],
                "questionnaire_answers": user_data[13],
                "reviewed_by": user_data[14],
                "audit_code": user_data[15]
            }
        else:
            return None

    def get_recent_users(self, limit: int) -> Any:
        # 通过最近注册时间获取用户数据
        sql_query = "SELECT * FROM users ORDER BY registration_time DESC LIMIT ?"
        self.cursor.execute(sql_query, (limit,))
        return self.cursor.fetchall()

    def get_all_usernames(self) -> List[str]:
        # 获取所有用户名
        sql_query = "SELECT username FROM users"
        self.cursor.execute(sql_query)
        return [row[0] for row in self.cursor.fetchall()]
    
    def delete_user_by_identifier(self, identifier: str, by_username: bool=True) -> bool:
        # 根据用户名或游戏名删除用户
        try:
            column_name = "username" if by_username else "game_name"
            sql_delete = f"DELETE FROM users WHERE {column_name} = ?"
            self.cursor.execute(sql_delete, (identifier,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"删除标识符为 {identifier} 的用户时发生错误: {e}")
            return False

    def close_connection(self) -> None:
        self.conn.close()


class AdminDataManager:
    def __init__(self, db_name=MinecraftAdminUserDB):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        # 创建用户表
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                key TEXT
            )
        """)
        self.conn.commit()

    def insert_new_user(self, username, password, key=None):
        try:
            if key is None:
                self.cursor.execute("INSERT INTO Admins (username, password) VALUES (?, ?)", (username, password))
            else:
                self.cursor.execute("INSERT INTO Admins (username, password, key) VALUES (?, ?, ?)", (username, password, key))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:  # 处理用户名已存在的异常
            logger.error(f"无法插入新用户:{username}, error message：{e}")
            return False

    def get_user_data_by_username(self, username):
        self.cursor.execute("SELECT * FROM Admins WHERE username=?", (username,))
        admin_data = self.cursor.fetchone()
        if admin_data:
            return {"id": admin_data[0], "username": admin_data[1], "password": admin_data[2], "key": admin_data[3]}
        else:
            return None
        
    def get_all_usernames(self) -> List[str]:
        # 获取所有用户名
        sql_query = "SELECT username FROM Admins"
        self.cursor.execute(sql_query)
        return [row[0] for row in self.cursor.fetchall()]


    def update_user_data_by_username(self, username, new_password, new_key=None):
        if new_key is None:
            self.cursor.execute("UPDATE Admins SET password=? WHERE username=?", (new_password, username))
        else:
            self.cursor.execute("UPDATE Admins SET password=?, key=? WHERE username=?", (new_password, new_key, username))
        if self.cursor.rowcount > 0:
            self.conn.commit()
            return True
        else:
            return False

    def update_user_key_by_username(self, username, new_key):
        self.cursor.execute("UPDATE Admins SET key=? WHERE username=?", (new_key, username))
        if self.cursor.rowcount > 0:
            self.conn.commit()
            return True
        else:
            return False

    def close_connection(self):
        self.conn.close()


if __name__ in "__main__":
    from methods import CreateKey
    # 调用迁移函数
    # migrate_data()
    # 使用示例：
    # manager = MinecraftWhitelistManager()

    # # 获取所有用户名
    # all_usernames = manager.get_all_usernames()
    
    # user_data = manager.get_data_by_username('PYmili')

    # 获取最近注册的10个用户数据
    # recent_users = manager.get_recent_users(10)

    # manager.close_connection()

    # print(user_data)
    # print(all_usernames)
    # print(recent_users)

    manager = AdminDataManager()
    # manager.insert_new_user("2546947442", "sagiri0915", CreateKey())
    # manager.insert_new_user("kk", "114514", CreateKey())
    # manager.insert_new_user("mydqc", "0123456789", CreateKey())
    input_data = input("Input new username and password: ").split()
    if input_data: 
        manager.insert_new_user(input_data[0], input_data[-1], CreateKey())
    print("All User:", end="\n\t")
    print("\n\t".join(manager.get_all_usernames()))
