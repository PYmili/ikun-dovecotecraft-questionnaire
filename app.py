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
from VerificationCode import VerificationCodeService, EmailEvent

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
    noPassedSecondReviewInformations = []
    white_manager = MinecraftWhitelistManager()
    for user in white_manager.get_all_usernames():
        white_result = white_manager.get_data_by_username(user)
        if not white_result:
            continue
        if white_result['passed_second_review'] == "No":
            noPassedSecondReviewInformations.append(white_result)
        userInformations.append(white_result)
    white_manager.close_connection()
    return render_template(
        "UserInformation.html",
        userInformations=userInformations,
        noPassedSecondReviewInformations=noPassedSecondReviewInformations
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
        result['content'] = "未填写email地址或验证码"
        return result
    vcs = VerificationCodeService()
    verify_bool, verify_content = vcs.verify_code(email_adder=email, provided_code=verificationCode)
    if verify_bool is False:
        result['content'] = verify_content
        return result
    
    manager = MinecraftWhitelistManager()
    if manager.is_email_registered(email) is True:
        manager.close_connection()
        result['content'] = "邮箱已注册过！"
        return result
    if manager.get_data_by_username(username=request.json.get("username")):
        manager.close_connection()
        result["content"] = "用户已注册，请勿重复提交！"
        return result
    manager.close_connection()
    
    questions = json.loads(request.json.get("questions"))
    QUESTIONS = get_questions()
    save_questions = {}
    if questions:
        count = 1
        for question_value in questions.values():
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
    if reason_result != "通过":
        result['content'] = reason_result
        return result

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
        "reviewed_by": "暂未通过审核",
        "audit_code": AuditCode
    }
    manager = MinecraftWhitelistManager()
    insert_result = manager.insert_data(MinecraftUserData)
    manager.close_connection()
    if insert_result is False:
        result['content'] = "添加错误！"
        return result
    
    result["code"] = 200
    result["content"] = "通过 AI 审核，后续管理员会进行白名单给予，注意你的邮箱信息，耐心等待！"

    # 邮件提醒管理员
    email_event = EmailEvent()
    email_event.setSubject(f"用户：{request.json.get('username')}，通过验证。")
    email_event.setContent(
        content_html=f"""
        <html>
        <body>
            <p>用户名：{request.json.get('username')}</p>
            <p>游戏名：{request.json.get('username')}</p>
            <p>已为您生成一个随机邀请码：{AuditCode}</p>
            <p><a href="https://question.pymili-blog.icu/user_information">请您进行二次审核（点击跳转）</a></p>
        </body>
        </html>
        """
    )
    send_result = email_event.send()
    if send_result is False:
        logger.error("发送邮件提醒失败！")
        
    return result


@app.route("/passed_second_review", methods=["POST"])
def passed_second_review():
    """
    给予用户二次审核通过
    """
    result = {
        "code": 400,
        "content": "参数错误！"
    }
    if not all([request.json, request.cookies]):
        result['content'] = "参数缺失"
        return result
    
    username = request.json.get("username")
    if not username:
        result['content'] = "管理员信息错误！"
        return result
    
    reviewer_name = request.cookies.get("username")
    if not reviewer_name:
        result['content'] = "cookies错误，非法操作！"
        return result
    
    manager = MinecraftWhitelistManager()
    get_result = manager.get_data_by_username(username)
    if not get_result:
        manager.close_connection()
        result['content'] = "用户不存在！"
        return result
    
    modify_result = manager.modify_passed_second_review_status_by_username(username, "Yes")
    manager.close_connection()
    if not modify_result:
        result['content'] = "服务器错误！"
        return result
    
    manager = MinecraftWhitelistManager()
    reviewer_result = manager.add_reviewer_name(username=username, reviewer_name=reviewer_name)
    if reviewer_result is False:
        result['content'] = "给予成功，但添加审核人名称错误！"
        return result
    manager.close_connection()
    
    manager = MinecraftWhitelistManager()
    get_by_result = manager.get_data_by_username(username)
    manager.close_connection()
    if not get_by_result:
        result['content'] = "数据错误！"
        return result
    
    email_event = EmailEvent()
    email_event.setSubject("您已通过二次审核！")
    email_event.setContent(content_html=f"""
    <html>
    <body>
        <h1>您已通过本服审核，请按照如下步骤进入服务器</h1>
        <ul>
            <li>
                1.添加服务器群。（进群问题审核号码请按规填写）
                <br>服务器交流群:850393979
                <br>审核号码:{get_by_result['audit_code']}
                <br>随后审核群可自行退出。群号请自觉保密，禁止外泄。
            </li>
            <li>2.获取白名单。</li>
            <p>请私聊群主发送您的游戏ID及主要用于进入游戏的版本（JE/BE),若您两个版本皆有账号，请分别将ID发送并注明对应版本。</p>
            <hr>
            <p>不要一直催，服主在现实很忙，有自己更重要的事情做。12h以内一定给你。</p>
            <p>入群请关注群公告，群文件。尤其是服务器规则，请务必熟识。</p>
        </ul>
    <body>
    </html>
    """)
    if email_event.send(receivers=[get_by_result['email']]) is False:
        result['content'] = "发送邮件失败！"
        return result

    result['code'] = 200
    result['content'] = "给予成功！"
    return result


@app.route("/not_passed_second_review", methods=["POST"])
def not_passed_second_review():
    """不通过二次审核"""
    result = {
        "code": 400,
        "content": "参数错误！"
    }
    if not all([request.json, request.cookies]):
        return result
    
    username = request.json.get("username")
    admin_name = request.cookies.get("username")
    if not all([username, admin_name]):
        result['content'] = "用户名或管理员名称错误！"
        return result
    
    manager = MinecraftWhitelistManager()
    email = manager.get_data_by_username(username)['email']

    if username not in manager.get_all_usernames():
        result['content'] = "用户不存在！"
        return result
    
    delete_result = manager.delete_user_by_identifier(username)
    if delete_result is False:
        result['content'] = "失败！"
        return result
    manager.close_connection()
    
    email_event = EmailEvent()
    email_event.setSubject("鸽子窝，二审未通过。")
    email_event.setContent(content_html=f"""
    <html>
        <body>
            <h1 style="color: red;">二审未通过！</h1>
            <p>您的二次审核被：<admin style="color: blue;">{admin_name}</admin> 驳回。</p>
            <p>可以重新填写问卷，请认真仔细填写问卷！</p>
        </body>
    </html>
    """)
    send_result = email_event.send(receivers=[email])
    if send_result is False:
        result['code'] = 200
        result['content'] = "用户已删除，但邮件发送失败！"
        return result
    
    result["code"] = 200
    result["content"] = "成功！"
    return result


if __name__ in "__main__":
    app.run(
        host="0.0.0.0",
        port="8888",
        debug=True
    )