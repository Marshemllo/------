"""
数据库初始化脚本 - 创建默认管理员账号
"""
from app import create_app, db
from app.database import create_user, get_user_by_username
from app.models import User, SystemLog, SearchResult, CrawlTask, CollectedData, ArticleData

def init_database():
    """初始化数据库并创建默认管理员"""
    app = create_app('development')
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print('[OK] Database tables created')
        
        # 检查是否已存在管理员账号
        admin = get_user_by_username('admin')
        if not admin:
            # 创建默认管理员账号
            user = create_user(
                username='admin',
                password='admin123',
                email='admin@example.com',
                role='admin'
            )
            if user:
                print('[OK] 默认管理员账号创建成功!')
                print('  用户名: admin')
                print('  密码: admin123')
            else:
                print('[FAIL] 创建管理员账号失败')
        else:
            print('[OK] 管理员账号已存在')
        
        print('\n数据库初始化完成!')

if __name__ == '__main__':
    init_database()
