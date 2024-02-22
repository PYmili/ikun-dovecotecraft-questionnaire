import os
import json

from flask import Flask
from flask import request
from flask import redirect
from flask import make_response
from flask import render_template
from loguru import logger

import questionaire_gpt
from methods import CreateKey
from SQLiteMethods import MinecraftWhitelistManager, AdminDataManager
from VerificationCode import VerificationCodeService

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
    )
QUESTION_JSON_PATH = os.path.join(os.getcwd(), "questions.json")


def GPT_Event(problem: str, reply: str) -> str:
    gpt = questionaire_gpt.GPT()
    gpt.addMessage(
        f"{problem}\n用户回答：{reply}"
    )
    gpt_reslut = gpt.run()
    logger.info("GPT: " + gpt_reslut)
    if len(gpt_reslut) == 0:
        return "gpt错误，请与管理员联系！"

    return gpt_reslut


def get_questions() -> dict:
    result = {}
    if os.path.isfile(QUESTION_JSON_PATH) is True:
        with open(QUESTION_JSON_PATH, "r", encoding="utf-8") as rfp:
            count = 1
            for question in json.loads(rfp.read())['questions']:
                result[count] = question
                count += 1
    return result


@app.route("/questionnaire", methods=["GET"])
def questionnaire():
    """
    问卷主页
    """
    return render_template(
        "questionnaire.html",
        questions=get_questions()
    )


@app.route("/user_information")
def user_information():
    if not request.cookies:
        return redirect("/login")
    
    key = request.cookies.get("key")
    username = request.cookies.get("username")
    if not all([key, username]):
        return redirect("/login")
    
    manager = AdminDataManager()
    by_username_result = manager.get_user_data_by_username(username)
    manager.close_connection()
    if not by_username_result:
        return redirect("/login")
    
    if key != by_username_result['key']:
        return redirect("/login")
    
    userInformations = []
    noGetWhiteListInformations = []
    white_manager = MinecraftWhitelistManager()
    for user in white_manager.get_all_usernames():
        white_result = white_manager.get_data_by_username(user)
        if not white_result:
            continue
        if white_result['whitelisted'] == "No":
            noGetWhiteListInformations.append(white_result)
        userInformations.append(white_result)
    white_manager.close_connection()

    return render_template(
        "UserInformation.html",
        userInformations=userInformations,
        noGetWhiteListInformations=noGetWhiteListInformations
    )


@app.route("/login")
def login():
    """
    管理员登录界面
    """
    return render_template(
        "login.html"
    )


@app.route("/login_api", methods=["POST"])
def login_api() -> dict:
    """
    登录api
    """
    result = {"code": 400, "content": "参数错误！"}
    if not request.json:
        return result
    
    username = request.json.get("username")
    password = request.json.get("password")
    if not all([username, password]):
        result['content'] = "用户名或密码未填写！"
        return result
    
    manager = AdminDataManager()
    by_username_result = manager.get_user_data_by_username(username)
    manager.close_connection()  # 释放manager罢免占用问题。
    if not by_username_result:
        result['content'] = "用户不存在！"
        return result
    
    if password != by_username_result['password']:
        result['content'] = "密码错误！"
        return result
    
    manager = AdminDataManager()
    by_username_result['key'] = CreateKey()
    update_key_reuslt = manager.update_user_key_by_username(username, by_username_result['key'])
    if not update_key_reuslt:
        result["content"] = "更新key失败！"
        manager.close_connection()
        return result
    manager.close_connection()

    # 设置cookie，有效期为30分钟, httponly: 是否允许js获取cookie
    result['code'] = 200
    result['content'] = "登录成功！"
    resp = make_response(result)
    resp.set_cookie(
        "username",
        by_username_result['username'],
        httponly=False,
        max_age=1800
    )
    resp.set_cookie(
        "key",
        by_username_result['key'],
        httponly=False,
        max_age=1800
    )
    return resp


@app.route("/send_verification_code", methods=["POST"])
def sendVerificationCode():
    """
    发送邮箱验证码
    """
    result = {
        "code": 400,
        "content": "参数残缺！"
    }
    if not request.json:
        return result

    email = request.json.get("email")
    if not email:
        return result
    
    vcs = VerificationCodeService()
    send_result = vcs.send_code(to_email_adder=email)

    if send_result is False:
        result['content'] = "发送失败！"
        return result
    
    result['code'] = 200
    result["content"] = "发送成功！"
    return result


@app.route("/questionaire_upload", methods=["POST"])
def questionaire_upload():
    """
    上传数据api
    """
    result = {
        "code": 400,
        "content": "参数错误！"
    }
    if not request.json:
        return result
    
    email = request.json.get("email")
    verificationCode = request.json.get("verificationCode")
    if not all([email, verificationCode]):
        result['content'] = "未填写email"
        return result
    vcs = VerificationCodeService()
    verify_bool, verify_content = vcs.verify_code(email_adder=email, provided_code=verificationCode)
    if verify_bool is False:
        result['content'] = verify_content
        return result
    manager = MinecraftWhitelistManager()
    if manager.is_email_registered(email) is True:
        result['content'] = "邮箱已注册过！"
        return result
    manager.close_connection()
    
    questions = json.loads(request.json.get("questions"))
    QUESTIONS = get_questions()
    save_questions = {}
    if questions:
        count = 1
        for question_key, question_value in questions.items():
            question_result = GPT_Event(
                QUESTIONS[count], f"用户：" + question_value
            )
            if question_result != "通过":
                result["content"] = f"问题：{QUESTIONS[count]}\n未通过原因：" + question_result
                return result
            
            save_questions[QUESTIONS[count]] = question_value
            count += 1
    
    self_introduction = request.json.get("selfIntroduction")
    reason = request.json.get("reason")
    if not all([self_introduction, reason]):
        result['content'] = "请填写自我介绍、理由。"
        return result
    
    self_introduction_result = GPT_Event("这是用户的自我介绍，你查看是否合法：", self_introduction)
    reason_result = GPT_Event("这是用户的进入服务器的理由：", reason)
    if self_introduction_result != "通过":
        result["content"] = self_introduction_result
        return result
    if reason_result != "通过 AI 审核，后续管理员会进行白名单给予，请耐心等待！":
        result['content'] = reason_result
        return result

    MinecraftUserData = {
        "username": request.json.get("username"),
        "game_name": request.json.get("gameName"),
        "qq_number": request.json.get("qqNumber"),
        "has_official_account": request.json.get("hasOfficialAccount"),
        "current_status": request.json.get("currentStatus"),
        "review_channel": request.json.get("reviewChannel"),
        "friend_qq_number": request.json.get("friendQQNumber"),
        "playtime": request.json.get("playtime"),
        "technical_direction": request.json.get("technicalDirection"),
        "email": email,
        "questionnaire_answers": ";".join([key+"用户回答："+value for key, value in save_questions.items()])
    }
    manager = MinecraftWhitelistManager()
    insert_result = manager.insert_data(MinecraftUserData)
    manager.close_connection()
    if insert_result is False:
        result['content'] = "添加错误！"
        return result
    
    result["code"] = 200
    result["content"] = reason_result
    return result


@app.route("/give_whitelist", methods=["POST"])
def give_whitelist():
    """
    给予用户白名单
    """
    result = {
        "code": 400,
        "content": "参数错误！"
    }
    if not request.json:
        return result
    
    username = request.json.get("username")
    if not username:
        return result
    
    manager = MinecraftWhitelistManager()
    get_result = manager.get_data_by_username(username)
    if not get_result:
        manager.close_connection()
        result['content'] = "用户不存在！"
        return result
    
    modify_result = manager.modify_whitelisted_status_by_username(username, "Yes")
    manager.close_connection()
    if not modify_result:
        result['content'] = "服务器错误！"
        return result
    
    result['code'] = 200
    result['content'] = "给予成功！"
    return result


if __name__ in "__main__":
    app.run(
        host="0.0.0.0",
        port="8888",
        debug=True
    )