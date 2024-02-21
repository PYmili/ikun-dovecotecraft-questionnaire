// main.js

// 显示加载消息和禁用鼠标事件
function showLoadingMessage() {
    var overlay = document.createElement('div');
    overlay.id = 'overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    overlay.style.zIndex = '9999';
    overlay.style.cursor = 'wait'; // 显示等待光标
    document.body.appendChild(overlay);

    // 禁止页面滚动
    document.body.style.overflow = 'hidden';

    var loadingMessage = document.getElementById('loading-message');
    loadingMessage.style.display = 'block';
}

// 隐藏加载消息和启用鼠标事件
function hideLoadingMessage() {
    var loadingMessage = document.getElementById('loading-message');
    // 启用页面滚动
    document.body.style.overflow = 'auto';
    loadingMessage.style.display = 'none';

    var overlay = document.getElementById('overlay');
    if (overlay) {
        document.body.removeChild(overlay);
    }
}

// 获取表单提交按钮
const submitButton = document.getElementById('submit_button');


// 监听提交按钮点击事件
submitButton.addEventListener('click', function(event) {
    // 阻止表单默认提交行为
    event.preventDefault();

    showLoadingMessage()
    // 获取表单中的值
    const username = document.getElementById('username').value;
    const gameName = document.getElementById('game_name').value;
    const qqNumber = document.getElementById('qq_number').value;
    const friendQQNumber = document.getElementById('friend_qq_number').value;
    const reviewChannel = document.getElementById('review_channel').value;
    const age = document.getElementById('age').value;
    const email = document.getElementById('email').value;
    const verificationCode = document.getElementById('verify_code').value;
    const hasOfficialAccount = document.querySelector('input[name="has_official_account"]:checked').value;
    const currentStatus = document.querySelector('input[name="current_status"]:checked').value;
    const technicalDirection = document.getElementById('technical_direction').value;
    const playtime = document.getElementById('playtime').value;
    const selfIntroduction = document.getElementById('self_introduction').value;
    const reason = document.getElementById('reason').value;
    const questions = document.querySelectorAll('[id^="question"]');

    // 在这里执行提交操作，例如将获取到的值发送到服务器等
    console.log('用户名:', username);
    console.log('游戏名:', gameName);
    console.log('用户QQ:', qqNumber);
    console.log('朋友QQ:', friendQQNumber);
    console.log('通过渠道:', reviewChannel);
    console.log('年龄:', age);
    console.log('邮箱:', email);
    console.log('验证码:', verificationCode);
    console.log('是否有正版账号:', hasOfficialAccount);
    console.log('当前状态:', currentStatus);
    console.log('擅长领域:', technicalDirection);
    console.log('游戏时长:', playtime);
    console.log('自我介绍:', selfIntroduction);
    console.log('申请理由:', reason);

    // 将 NodeList 转换为数组
    const questionArray = Array.from(questions);

    // 创建一个对象来存储问题
    const questionObject = {};

    // 遍历数组，将问题写入对象
    questionArray.forEach((question, index) => {
        const questionId = question.id;
        const questionValue = question.value;
        questionObject[questionId] = questionValue;
        console.log(questionId);
    });

    // 将问题对象转换为 JSON
    const questionsJSON = JSON.stringify(questionObject);

    // 打印 JSON
    console.log(questionsJSON);


    // 编写注册功能
    // 构建 POST 请求的参数
    var params = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            username: username,
            gameName: gameName,
            qqNumber: qqNumber,
            friendQQNumber: friendQQNumber,
            reviewChannel: reviewChannel,
            age: age,
            email: email,
            verificationCode: verificationCode,
            hasOfficialAccount: hasOfficialAccount,
            currentStatus: currentStatus,
            technicalDirection: technicalDirection,
            playtime: playtime,
            selfIntroduction: selfIntroduction,
            reason: reason,
            questions: questionsJSON
        })
    };

    // 发送 POST 请求
    fetch('/questionaire_upload', params)
        .then(response => {
                // 隐藏加载中消息
                hideLoadingMessage()
            if (response.ok) {
                return response.json();
            }
            throw new Error('Failed to send verification code');
        })
        .then(data => {
            alert(data['content']);
        })
        .catch(error => {
            alert('请求失败！请联系管理员！');
        });
});


var timer; // 定时器
function sendVerificationCode() {
    // 获取用户输入的邮箱地址
    var email = document.getElementById('email').value;

    if (email === "") {
        alert("请输入地址！");
        return;
    }

    // 获取发送验证码按钮元素
    var sendButton = document.getElementById('send_verification_code');

    // 禁用发送按钮（改变其样式和行为）
    sendButton.style.pointerEvents = 'none'; // 阻止点击事件
    sendButton.classList.add('disabled'); // 添加禁用样式

    // 设置倒计时时间（单位：秒）
    var countDownSeconds = 60;

    // 更新按钮文字为倒计时
    sendButton.textContent = countDownSeconds + '秒后重新发送';

    // 启动定时器，每秒更新倒计时时间
    timer = setInterval(function() {
        countDownSeconds--;
        sendButton.textContent = countDownSeconds + '秒后重新发送';

        // 如果倒计时结束，恢复发送按钮状态
        if (countDownSeconds <= 0) {
            clearInterval(timer);
            sendButton.style.pointerEvents = 'auto'; // 恢复点击事件
            sendButton.classList.remove('disabled'); // 移除禁用样式
            sendButton.textContent = '发送验证码';
        }
    }, 1000);

    // 构建 POST 请求的参数
    var params = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: email })
    };

    // 发送 POST 请求
    fetch('/send_verification_code', params)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Failed to send verification code');
        })
        .then(data => {
            alert(data['content']);
        })
        .catch(error => {
            console.error('Error sending verification code:', error);
            alert('验证码发送失败，请稍后重试');
        });
}