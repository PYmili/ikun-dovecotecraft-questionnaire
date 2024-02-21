import os
import json

from flask import Flask
from flask import request
from flask import render_template
from loguru import logger

import questionaire_gpt
from SQLiteMethods import MinecraftWhitelistManager
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
    if questions:
        count = 1
        for question in questions.values():
            question_result = GPT_Event(
                QUESTIONS[count], f"用户：" + question
            )
            if question_result != "通过":
                result["content"] = f"问题：{QUESTIONS[count]}\n未通过原因：" + question_result
                return result
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
    if reason_result != "通过":
        result['content'] = reason_result
        return result

    MinecraftUserData = {
        "username": request.json.get("username"),
        "game_name": request.json.get("gameName"),
        "qq_number": request.json.get("qqNumber"),
        "age": request.json.get("age"),
        "has_official_account": request.json.get("hasOfficialAccount"),
        "current_status": request.json.get("currentStatus"),
        "review_channel": request.json.get("reviewChannel"),
        "friend_qq_number": request.json.get("friendQQNumber"),
        "playtime": request.json.get("playtime"),
        "technical_direction": request.json.get("technicalDirection"),
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


if __name__ in "__main__":
    app.run(
        host="0.0.0.0",
        port="8080",
        debug=True
    )