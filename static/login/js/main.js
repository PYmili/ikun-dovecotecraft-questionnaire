document.addEventListener('DOMContentLoaded', function() {
    // 获取表单元素
    var usernameInput = document.getElementById('username');
    var passwordInput = document.getElementById('password');
    var loginButton = document.querySelector('.btn');

    // 登录按钮点击事件
    loginButton.addEventListener('click', function(e) {
        e.preventDefault(); // 阻止表单默认提交

        // 验证用户名和密码是否为空
        if (usernameInput.value.trim() === '' || passwordInput.value.trim() === '') {
            alert('请输入用户名和密码！');
            return;
        }

        // 登录请求
        simulateLogin(usernameInput.value, passwordInput.value);
    });

    function simulateLogin(username, password) {
        // 向服务器发送AJAX请求的代码
        console.log('user name:', username, '\npassword:', password);
        
         // 构建 POST 请求的参数
        var params = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: username, password: password })
        };

        // 发送 POST 请求
        fetch('/login_api', params)
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('登录接口错误！');
            })
            .then(data => {
                alert(data['content']);
                window.location.href = "/user_information";
            })
            .catch(error => {
                console.error('登录错误:', error);
                alert('登录失败！');
            });
    }
});