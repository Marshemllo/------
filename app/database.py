"""
数据库连接和操作的工具函数
"""
from app import db
from app.models import User, SystemLog
from werkzeug.security import generate_password_hash, check_password_hash


def init_db():
    """初始化数据库，创建所有表"""
    db.create_all()


def drop_db():
    """删除所有表"""
    db.drop_all()


def create_user(username, password, email=None, role='user'):
    """
    创建新用户
    :param username: 用户名
    :param password: 密码
    :param email: 邮箱
    :param role: 角色
    :return: User 对象或 None
    """
    try:
        hashed_password = generate_password_hash(password)
        user = User(
            username=username,
            password=hashed_password,
            email=email,
            role=role
        )
        db.session.add(user)
        db.session.commit()
        return user
    except Exception as e:
        db.session.rollback()
        print(f"创建用户失败: {e}")
        return None


def verify_user(username, password):
    """
    验证用户登录
    :param username: 用户名
    :param password: 密码
    :return: User 对象或 None
    """
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return user
    return None


def get_user_by_id(user_id):
    """根据ID获取用户"""
    return User.query.get(user_id)


def get_user_by_username(username):
    """根据用户名获取用户"""
    return User.query.filter_by(username=username).first()


def update_user(user_id, **kwargs):
    """
    更新用户信息
    :param user_id: 用户ID
    :param kwargs: 要更新的字段
    :return: 是否成功
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return False
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                if key == 'password':
                    value = generate_password_hash(value)
                setattr(user, key, value)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"更新用户失败: {e}")
        return False


def delete_user(user_id):
    """删除用户"""
    try:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"删除用户失败: {e}")
        return False


def add_system_log(action, description=None, user_id=None, ip_address=None):
    """
    添加系统日志
    :param action: 操作类型
    :param description: 描述
    :param user_id: 用户ID
    :param ip_address: IP地址
    """
    try:
        log = SystemLog(
            action=action,
            description=description,
            user_id=user_id,
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
        return log
    except Exception as e:
        db.session.rollback()
        print(f"添加日志失败: {e}")
        return None
