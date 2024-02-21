import os
import sqlite3
from datetime import datetime
from typing import List, Any, Dict, Optional

MinecraftWhitelistManagerDB = os.path.join(os.getcwd(), "db", "minecraft_whitelist.db")

class MinecraftWhitelistManager:
    def __init__(self, db_name: str=MinecraftWhitelistManagerDB) -> None:
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        # 用户表
        sql_create_table = '''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                game_name TEXT NOT NULL,
                registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                qq_number INTEGER,
                has_official_account BOOLEAN,
                current_status TEXT,
                review_channel TEXT,
                friend_qq_number INTEGER DEFAULT NULL,
                playtime INTEGER,
                technical_direction TEXT,
                age INTEGER,
                email TEXT UNIQUE
            );
        '''
        self.cursor.execute(sql_create_table)
        self.conn.commit()

    def insert_data(self, data_dict: Dict[str, Any]) -> bool:
        # 插入新数据
        required_keys = ['username', 'game_name', 'current_status', 'review_channel', 'playtime', 'technical_direction', 'age']
        if all(key in data_dict for key in required_keys):
            values_tuple = tuple(data_dict.get(key, None) for key in [
                'username', 'game_name', 'has_official_account', 'current_status', 'review_channel', 
                'qq_number', 'friend_qq_number', 'playtime', 'technical_direction', 'age'
            ])
            sql_insert = '''
                INSERT INTO users (username, game_name, has_official_account, current_status, review_channel, 
                                  qq_number, friend_qq_number, playtime, technical_direction, age) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            '''
            try:
                self.cursor.execute(sql_insert, values_tuple)
                self.conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Error inserting data: {e}")
                return False
        else:
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

    def modify_data(self, user_id, column_name, new_value) -> bool:
        # 修改指定列的数据
        sql_modify = f'''
            UPDATE users SET {column_name} = ? WHERE user_id = ?
        '''
        self.cursor.execute(sql_modify, (new_value, user_id))
        self.conn.commit()
        return True
    
    def is_email_registered(self, email: str) -> bool:
        # 检查指定的email是否已经注册过
        sql_query = "SELECT COUNT(*) FROM users WHERE email = ?"
        self.cursor.execute(sql_query, (email,))
        count = self.cursor.fetchone()[0]
        return count > 0

    def get_user_by_username(self, username: str) -> Any:
        # 通过用户名获取用户数据
        sql_query = "SELECT * FROM users WHERE username = ?"
        self.cursor.execute(sql_query, (username,))
        return self.cursor.fetchone()

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

    def close_connection(self) -> None:
        self.conn.close()


if __name__ in "__main__":
    # 使用示例：
    manager = MinecraftWhitelistManager()

    # 插入新用户
    # new_user_data = {
    #     'username': 'player1',
    #     'game_name': 'GamePlayer1',
    #     'has_official_account': True,
    #     'current_status': 'Active',
    #     'review_channel': 'Website',
    #     'qq_number': 123456,
    #     'friend_qq_number': 7890,
    #     'playtime': 100,
    #     'technical_direction': 'Redstone',
    #     "age": 19
    # }
    # manager.insert_data(new_user_data)

    # 更新玩家信息
    # update_data = {'current_status': 'Pending', 'playtime': 200}
    # manager.update_data(1, update_data)

    # 修改特定列的信息
    # manager.modify_data(1, 'friend_qq_number', 999999)

    # 通过用户名获取数据
    # user_data = manager.get_user_by_username('player1')
    user_data = manager.get_user_by_username('PYmili')

    # 获取最近注册的10个用户数据
    recent_users = manager.get_recent_users(10)

    # 获取所有用户名
    all_usernames = manager.get_all_usernames()

    manager.close_connection()

    print(user_data)
    print(all_usernames)
