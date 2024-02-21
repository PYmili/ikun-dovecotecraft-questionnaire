import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

SENDER = 'mc2005wj@163.com'
IMAP_SMTP_CODE = "ROHNIVYQBGGMOVWG"

def sendEmailVerufucationCode(receiver: str, code: str) -> bool:
    """
    发送邮箱验证码
    :params
        receiver str: 要发送至的邮件
        code str: 验证码
    """
    # 创建一个带附件的MIMEMultipart对象
    msg = MIMEMultipart()
    msg['From'] = Header(SENDER)
    msg['To'] = Header(receiver)
    msg['Subject'] = Header("来自鸽子窝服务器的邮箱验证码", 'utf-8')  # 邮件主题，支持中文

    # 邮件正文内容
    text_content = f"这是你的邮箱验证码：{code}"
    html_content = f"<html><body><p>这是你的邮箱验证码：{code}</p></body></html>"

    # 将文本和HTML内容加入到MIME消息体中
    part1 = MIMEText(text_content, 'plain', 'utf-8')
    part2 = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(part1)
    msg.attach(part2)

    # 连接SMTP服务器并登录
    smtp_server = 'smtp.163.com'
    smtp_port = 465  # SSL端口，默认情况下网易要求使用SSL加密连接
    context = ssl.create_default_context()  # 加密上下文
    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
        server.login(SENDER, IMAP_SMTP_CODE)
        
        # 发送邮件
        server.sendmail(SENDER, receiver, msg.as_string())
        return True

    except Exception as e:
        return False

    finally:
        server.quit()


if __name__ in "__main__":
    result = sendEmailVerufucationCode("2097632843@qq.com", "hfihawef")
    if result:
        print("发送成功！")
    else:
        print("发送失败！")