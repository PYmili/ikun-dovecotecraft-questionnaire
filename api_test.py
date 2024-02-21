import requests

post_data = {
    "username": "PYmili",
    "game_name": "PYmili",
    "qq_number": "2097632843",
    "age": "19",
    "has_official_account": "null",
    "current_status": "读书",
    "review_channel": "bilibili",
    "friend_qq_number": "0000",
    "playtime": "1-2",
    "technical_direction": "生存",
    "self_introduction": "我是来炸",
    "reason": "我喜欢与人一起快乐的玩耍我的世界。"
}
with requests.post("http://127.0.0.1:8080/questionaire_upload", json=post_data) as response:
    if response.status_code == 200:
        print(response.json())
