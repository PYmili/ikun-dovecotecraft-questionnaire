import os
import json
import time
import random
import string

from . import send

generatedCodesJson = os.path.join(os.getcwd(), "generated_codes.json")


class VerificationCodeService:
    def __init__(self, code_length=6, valid_duration=1800):
        """
        初始化验证码服务类
        :param code_length: 验证码长度，默认为6位
        :param valid_duration: 验证码有效时间（单位：秒），默认为60秒
        """
        self.code_length = code_length
        self.valid_duration = valid_duration

        # 发送历史缓存
        self.generated_codes = {}
        if os.path.isfile(generatedCodesJson) is False:
            with open(generatedCodesJson, "w+", encoding="utf-8") as wfp:
                wfp.write("{}")
        
        with open(generatedCodesJson, mode="r", encoding="utf-8") as rfp:
            self.generated_codes = json.loads(rfp.read())

    def generate_code(self) -> str:
        """生成随机验证码"""
        chars = string.digits + string.ascii_letters
        return ''.join(random.choice(chars) for _ in range(self.code_length))

    def send_code(self, to_email_adder: str) -> bool:
        """
        生成并发送验证码到指定电话号码
        
        :params
            to_email_adder str: 要发送至的邮件地址
        :return bool
        """
        code = self.generate_code()
        self.generated_codes[to_email_adder] = {"code": code, "timestamp": int(time.time())}

        # 发送邮件如果成功则保存。
        send_result = send.sendEmailVerufucationCode(to_email_adder, code)
        if send_result is True:
            with open(generatedCodesJson, mode="w+", encoding="utf-8") as wfp:
                wfp.write(json.dumps(self.generated_codes, indent=4))
        
        return send_result

    def verify_code(self, email_adder: str, provided_code: str) -> tuple:
        """
        验证提供的验证码是否正确

        :params
            email_adder str: 电子邮件地址
            provided_code str: 需要验证的码
        """
        if email_adder not in self.generated_codes.keys():
            return False, "验证码错误！"
        
        stored_code_info = self.generated_codes[email_adder]
        now = int(time.time())
        if now - stored_code_info["timestamp"] > self.valid_duration:
            return False, "验证码已过期！"

        if provided_code == stored_code_info["code"]:
            return True, "验证码正确！"
        else:
            return False, "验证码错误！"
