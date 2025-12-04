/**
 * 登录页面 JavaScript
 */
layui.use(['form', 'layer'], function() {
    var form = layui.form;
    var layer = layui.layer;
    var $ = layui.$;

    // 监听登录表单提交
    form.on('submit(login)', function(data) {
        var loadIndex = layer.load(1, {
            shade: [0.3, '#000']
        });

        $.ajax({
            url: '/login',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data.field),
            success: function(res) {
                layer.close(loadIndex);
                if (res.code === 0) {
                    layer.msg('登录成功', {
                        icon: 1,
                        time: 1500
                    }, function() {
                        window.location.href = '/admin';
                    });
                } else {
                    layer.msg(res.msg || '登录失败', { icon: 2 });
                }
            },
            error: function() {
                layer.close(loadIndex);
                layer.msg('网络错误，请稍后重试', { icon: 2 });
            }
        });

        return false; // 阻止表单默认提交
    });

    // 回车键提交
    $(document).keydown(function(e) {
        if (e.keyCode === 13) {
            $('button[lay-submit]').click();
        }
    });
});
