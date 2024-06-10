document.addEventListener("DOMContentLoaded", function() {
    // 默认显示第一个部分
    var defaultSection = document.querySelector('section');
    defaultSection.style.display = 'block';

    // 隐藏其他部分
    var sections = document.querySelectorAll('section');
    for (var i = 1; i < sections.length; i++) {
        sections[i].style.display = 'none';
    }

    // 获取所有用户信息卡片
    var userInfos = document.querySelectorAll('.user-card');

    // 为每个用户信息卡片添加点击事件监听器
    userInfos.forEach(function(userInfo) {
        userInfo.addEventListener('click', function() {
            var additionalInfo = this.querySelector('.additional-info');
            additionalInfo.classList.toggle('visible');
        });
    });

    // 获取所有菜单项
    var menuItems = document.querySelectorAll('.menu ul li a');

    // 为每个菜单项添加点击事件监听器
    menuItems.forEach(function(item) {
        item.addEventListener('click', function(event) {
            // 阻止默认链接行为
            event.preventDefault();

            // 获取目标部分的ID
            var targetId = this.getAttribute('href').substr(1);

            // 隐藏所有部分
            sections.forEach(function(section) {
                section.style.display = 'none';
            });

            // 显示目标部分
            var targetSection = document.getElementById(targetId);
            targetSection.style.display = 'block';
        });
    });
});

function handleReview(username, apiEndpoint) {
    fetch(apiEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // 处理响应
        location.reload(true);
        alert(data['content']);
    })
    .catch(error => {
        console.error('There was a problem with your fetch operation:', error);
    });
}