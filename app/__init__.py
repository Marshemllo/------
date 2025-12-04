"""
Flask 应用初始化文件
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

# 初始化数据库扩展
db = SQLAlchemy()


def create_app(config_name='default'):
    """
    应用工厂函数
    :param config_name: 配置名称 (development, production, testing)
    :return: Flask 应用实例
    """
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    
    # 注册蓝图/路由
    from app.views import main_bp
    app.register_blueprint(main_bp)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app
