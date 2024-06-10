import sys
import os
import time
import json

from flask import Flask
from flask import request
from flask import redirect
from flask import make_response
from flask import render_template
from loguru import logger

from src import CreateKey
from src.ai import questionaire_ai
from src.database import MinecraftPlayerListManager, AdminDataManager
from src.VerificationCode import VerificationCodeService, EmailEvent

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
    )
QUESTION_JSON_PATH = os.path.join(os.getcwd(), "data", "json", "questions.json")


def AIEvent(problem: str, reply: str) -> str:
    """
    AI处理事件
    Params:
        problem: str
        reply: str
    :return str
    """
    gpt = questionaire_ai.GPT()
    gpt.addMessage(
        f"{problem}\n{reply}"
    )
    gpt_reslut = gpt.run()
    if not gpt_reslut:
        return "ai错误，请与管理员联系！"

    return gpt_reslut


def getQuestions() -> dict:
    """
    获取所有需要AI查看的问题
    :return dict
    """
    result = {}
    if os.path.isfile(QUESTION_JSON_PATH) is True:
        with open(QUESTION_JSON_PATH, "r", encoding="utf-8") as rfp:
            count = 1
            for question in json.loads(rfp.read())['questions']:
                result[count] = question
                count += 1
    return result


@app.route("/")
def index():
    return redirect("/questionnaire")


@app.route("/questionnaire", methods=["GET"])
def questionnaire():
    """
    问卷主页
    """
    return render_template(
        "questionnaire.html",
        questions=getQuestions()
    )


@app.route("/user_information")
def userInformation():
    """
    获取所有用户的信息
    """
    if not request.cookies:
        return redirect("/login")
    
    # 从cookies获取key, username两个关键数据
    key = request.cookies.get("key")
    username = request.cookies.get("username")
    if not all([key, username]):
        return redirect("/login")
    
    # 从数据库中查询数据
    manager = AdminDataManager()
    by_username_result = manager.get_user_data_by_username(username)
    manager.close_connection()
    if not by_username_result:
        return redirect("/login")
    if key != by_username_result['key']:
        return redirect("/login")
    
    # 整理数据并返回
    userInformations = []
    manager = MinecraftPlayerListManager()
    for user in manager.get_all_usernames():
        result = manager.get_data_by_username(user)
        if not result:
            continue
        userInformations.append(result)
    manager.close_connection()
    return render_template(
        "UserInformation.html",
        userInformations=userInformations
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
    
    # 通过用户名与密码进行登录
    username = request.json.get("username")
    password = request.json.get("password")
    if not all([username, password]):
        result['content'] = "用户名或密码未填写！"
        return result
    
    manager = AdminDataManager()
    by_username_result = manager.get_user_data_by_username(username)
    manager.close_connection()  # 释放manager
    if not by_username_result:
        result['content'] = "用户不存在！"
        return result
    if password != by_username_result['password']:
        result['content'] = "密码错误！"
        return result
    
    # 读取往期key数据，并进行更新
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

    # 获取需要发送的邮件地址
    email = request.json.get("email")
    if not email:
        return result
    
    # 发送验证码
    vcs = VerificationCodeService()
    send_result = vcs.send_code(to_email_adder=email)

    if send_result is False:
        result['content'] = "发送失败！"
        return result
    
    result['code'] = 200
    result["content"] = "发送成功！"
    return result


@app.route("/questionaire_upload", methods=["POST"])
def questionaireUpload():
    """
    上传问卷数据API
    """
    result = {
        "code": 400,
        "content": "参数错误！"
    }
    if not request.json:
        return result
    
    # 获取邮件和验证码
    email = request.json.get("email")
    verificationCode = request.json.get("verificationCode")
    if not all([email, verificationCode]):
        result['content'] = "未填写email地址或验证码"
        return result
    # 验证验证码是否合法
    vcs = VerificationCodeService()
    verify_bool, verify_content = vcs.verify_code(email_adder=email, provided_code=verificationCode)
    if verify_bool is False:
        result['content'] = verify_content
        return result
    
    # 用户及其邮件验证
    manager = MinecraftPlayerListManager()
    if manager.is_email_registered(email) is True:
        manager.close_connection()
        result['content'] = "邮箱已注册过！"
        return result
    if manager.get_data_by_username(username=request.json.get("username")):
        manager.close_connection()
        result["content"] = "用户已注册，请勿重复提交！"
        return result
    manager.close_connection()
    
    # 获取requests.json中所有问题
    questions = json.loads(request.json.get("questions"))
    if not questions:
        result["content"] = "服务器错误！"
        return result
    # 获取已设定的所有问题
    QUESTIONS = getQuestions()
    # 最后保存
    save_questions = {}
    count = 1   # 问题个数
    for question_value in questions.values():
        # 让AI去判断问题，并返回是否通过
        question_result = AIEvent(
            QUESTIONS[count], f"用户：" + question_value
        ).strip()
        logger.info("AI: " + question_result)
        # 如果不通过
        if question_result != "[通过]":
            result["content"] = f"问题：{QUESTIONS[count]}\n未通过原因：" + question_result
            return result
        # 保存
        save_questions[QUESTIONS[count]] = question_value
        count += 1
        time.sleep(1)
    
    # 自我介绍处理
    self_introduction = request.json.get("selfIntroduction")
    reason = request.json.get("reason")
    if not all([self_introduction, reason]):
        result['content'] = "请填写自我介绍、理由。"
        return result
    self_introduction_result = AIEvent("这是用户的自我介绍，你查看是否合法：", self_introduction)
    reason_result = AIEvent("这是用户的进入服务器的理由：", reason)
    if self_introduction_result != "[通过]":
        result["content"] = self_introduction_result
        return result
    if reason_result != "[通过]":
        result['content'] = reason_result
        return result

    # 生成邀请码并对数据录入数据库
    AuditCode = CreateKey(length=10)
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
        "questionnaire_answers": ";".join([key+"用户回答："+value for key, value in save_questions.items()]),
        "audit_code": AuditCode
    }
    manager = MinecraftPlayerListManager()
    insert_result = manager.insert_data(MinecraftUserData)
    manager.close_connection()
    if insert_result is False:
        result['content'] = "添加错误！"
        return result
    
    result["code"] = 200
    result["content"] = "通过 AI 审核，请注意你的邮箱信息，耐心等待管理员同意！"
    result["auditCode"] = AuditCode # 将邀请码添加到返回

    # 邮件提醒管理员
    email_event = EmailEvent()
    email_event.setSubject(f"用户：{request.json.get('username')}，通过AI验证。")
    email_event.setContent(
        content_html=f"""
        <html>
        <body>
            <p>用户名：{request.json.get('username')}</p>
            <p>游戏名：{request.json.get('username')}</p>
            <p>邀请码：{AuditCode}</p>
            <p><a href="https://question.pymili-blog.icu/user_information">查看用户信息（点击跳转）</a></p>
        </body>
        </html>
        """
    )
    send_result = email_event.send()
    if send_result is False:
        logger.error("发送邮件提醒失败！")
        
    return result


@app.route("/pass", methods=["POST"])
def passEvent():
    """
    给予用户通过API
    """
    result = {"code": 400}
    
    # 获取用户名和邀请码
    userName = request.json.get("user_name")
    auditCode = request.json.get("audit_code")
    if not all([userName, auditCode]):
        result['content'] = "用户信息错误！"
        logger.warning(result["content"])
        return result
    
    # 验证用户及邀请码
    manager = MinecraftPlayerListManager()
    get_result = manager.get_data_by_username(userName)
    if not get_result:
        manager.close_connection()
        result['content'] = "用户不存在！"
        logger.warning(result["content"])
        return result
    # 验证邀请码
    if get_result.get("audit_code") != auditCode:
        manager.close_connection()
        result["content"] = "审核码错误！"
        logger.warning("审核码错误！")
        return result
    
    # 发送邮件给用户邮箱
    email_event = EmailEvent()
    email_event.setSubject("您已通过AI审核！")
    email_event.setContent(content_html=f"""
    <html>
    <body>
        <h1>您已通过本服AI审核，请按照如下步骤进入服务器</h1>
        <ul>
            <li>
                1.添加服务器群。（进群问题审核号码请按规填写）
                <br>服务器交流群: 934996287
                <br>审核号码: {get_result['audit_code']}
                <br>随后审核群可自行退出。群号请自觉保密，禁止外泄。
            </li>
            <li>2.获取白名单。</li>
            <p>请私聊群主发送您的游戏ID及主要用于进入游戏的版本（JE/BE),若您两个版本皆有账号，请分别将ID发送并注明对应版本。</p>
            <hr>
            <p>不要一直催，服主在现实很忙，有自己更重要的事情做。12h以内一定给你。</p>
            <p>入群请关注群公告，群文件。尤其是服务器规则，请务必熟识。</p>
            <p>PYmili在此恭喜你，加入我们！</p>
        </ul>
    <body>
    </html>
    """)
    # 邮件是否发送成功
    if email_event.send(receivers=[get_result['email']]) is False:
        result['content'] = "发送邮件失败！"
        logger.warning(result["content"])
        return result
    
    logger.info(f"给予用户: {userName} 通过")
    result['code'] = 200
    result['content'] = "success"
    return result


if __name__ in "__main__":
    logger.add("log/app.log", rotation="500 MB", level="DEBUG")

    # 在控制台输出日志，添加以下配置：
    logger.add(sys.stdout, level="DEBUG")
    app.run(
        host="0.0.0.0",
        port="8888",
        debug=True
    )