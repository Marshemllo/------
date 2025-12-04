/**
 * 后台管理页面 JavaScript
 */
layui.use(['element', 'layer', 'util'], function() {
    var element = layui.element;
    var layer = layui.layer;
    var util = layui.util;
    var $ = layui.$;

    // 侧边栏导航点击事件
    $(document).on('click', '.layui-nav-tree dd a', function() {
        var url = $(this).data('url');
        var title = $(this).text().trim();
        
        if (url) {
            // 检查是否已存在该标签页
            var tabExists = false;
            $('.layui-tab-title li').each(function() {
                if ($(this).text().trim() === title) {
                    tabExists = true;
                    element.tabChange('content-tab', $(this).attr('lay-id'));
                    return false;
                }
            });

            // 如果不存在则新增标签页
            if (!tabExists) {
                element.tabAdd('content-tab', {
                    title: title,
                    content: '<iframe src="' + url + '" frameborder="0" style="width:100%;height:calc(100vh - 180px);"></iframe>',
                    id: new Date().getTime()
                });
                element.tabChange('content-tab', new Date().getTime());
            }
        }
    });

    // 固定块
    util.fixbar({
        bar1: true,
        click: function(type) {
            if (type === 'bar1') {
                layer.msg('返回顶部');
            }
        }
    });

    // 退出登录确认
    $(document).on('click', 'a[href*="logout"]', function(e) {
        e.preventDefault();
        var href = $(this).attr('href');
        
        layer.confirm('确定要退出登录吗？', {
            icon: 3,
            title: '提示'
        }, function(index) {
            layer.close(index);
            window.location.href = href;
        });
    });
});
