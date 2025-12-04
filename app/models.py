"""
数据库模型定义
"""
from datetime import datetime
from app import db


class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(20), default='user')  # admin, user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SystemLog(db.Model):
    """系统日志模型"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('logs', lazy='dynamic'))
    
    def __repr__(self):
        return f'<SystemLog {self.action}>'


class SearchResult(db.Model):
    """搜索结果/舆情数据模型"""
    __tablename__ = 'search_results'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200), nullable=False, index=True)  # 搜索关键词
    title = db.Column(db.String(500), nullable=False)  # 标题
    link = db.Column(db.String(1000), nullable=True)  # 链接
    abstract = db.Column(db.Text, nullable=True)  # 摘要
    source = db.Column(db.String(200), nullable=True)  # 来源
    engine = db.Column(db.String(20), nullable=True)  # 搜索引擎
    sentiment = db.Column(db.String(20), default='neutral')  # 情感: positive/negative/neutral
    sentiment_score = db.Column(db.Integer, default=0)  # 情感分数
    crawl_time = db.Column(db.DateTime, default=datetime.utcnow)  # 爬取时间
    
    def __repr__(self):
        return f'<SearchResult {self.title[:20]}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'keyword': self.keyword,
            'title': self.title,
            'link': self.link,
            'abstract': self.abstract,
            'source': self.source,
            'engine': self.engine,
            'sentiment': self.sentiment,
            'sentiment_score': self.sentiment_score,
            'crawl_time': self.crawl_time.strftime('%Y-%m-%d %H:%M:%S') if self.crawl_time else None
        }


class CrawlTask(db.Model):
    """爬取任务模型"""
    __tablename__ = 'crawl_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200), nullable=False)  # 关键词
    engine = db.Column(db.String(20), default='all')  # 搜索引擎
    pages = db.Column(db.Integer, default=1)  # 爬取页数
    status = db.Column(db.String(20), default='pending')  # pending/running/completed/failed
    result_count = db.Column(db.Integer, default=0)  # 结果数量
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    error_msg = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<CrawlTask {self.keyword}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'keyword': self.keyword,
            'engine': self.engine,
            'pages': self.pages,
            'status': self.status,
            'result_count': self.result_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'error_msg': self.error_msg
        }


class CollectedData(db.Model):
    """采集数据临时存储模型 - 用于橱窗展示"""
    __tablename__ = 'collected_data'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(50), nullable=False, index=True)  # 任务批次ID
    keyword = db.Column(db.String(200), nullable=False)  # 搜索关键词
    title = db.Column(db.String(500), nullable=False)  # 标题
    link = db.Column(db.String(1000), nullable=True)  # 原始链接
    cover = db.Column(db.String(1000), nullable=True)  # 封面图片URL
    source = db.Column(db.String(200), nullable=True)  # 来源
    abstract = db.Column(db.Text, nullable=True)  # 摘要
    content = db.Column(db.Text, nullable=True)  # 深度采集的正文内容
    publish_time = db.Column(db.String(100), nullable=True)  # 发布时间
    author = db.Column(db.String(100), nullable=True)  # 作者
    deep_crawled = db.Column(db.Boolean, default=False)  # 是否已深度采集
    is_saved = db.Column(db.Boolean, default=False)  # 是否已保存到数据库
    crawl_time = db.Column(db.DateTime, default=datetime.utcnow)  # 采集时间
    
    def __repr__(self):
        return f'<CollectedData {self.title[:20]}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'keyword': self.keyword,
            'title': self.title,
            'link': self.link,
            'cover': self.cover,
            'source': self.source,
            'abstract': self.abstract,
            'content': self.content,
            'publish_time': self.publish_time,
            'author': self.author,
            'deep_crawled': self.deep_crawled,
            'is_saved': self.is_saved,
            'crawl_time': self.crawl_time.strftime('%Y-%m-%d %H:%M:%S') if self.crawl_time else None
        }


class ArticleData(db.Model):
    """文章数据正式存储模型 - 用户确认保存的数据"""
    __tablename__ = 'article_data'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200), nullable=False, index=True)  # 关键词
    title = db.Column(db.String(500), nullable=False)  # 标题
    link = db.Column(db.String(1000), nullable=True)  # 原始链接
    cover = db.Column(db.String(1000), nullable=True)  # 封面图片
    source = db.Column(db.String(200), nullable=True)  # 来源
    abstract = db.Column(db.Text, nullable=True)  # 摘要
    content = db.Column(db.Text, nullable=True)  # 正文内容
    publish_time = db.Column(db.String(100), nullable=True)  # 发布时间
    author = db.Column(db.String(100), nullable=True)  # 作者
    sentiment = db.Column(db.String(20), default='neutral')  # 情感分析结果
    sentiment_score = db.Column(db.Integer, default=0)  # 情感分数
    tags = db.Column(db.String(500), nullable=True)  # 标签，逗号分隔
    category = db.Column(db.String(100), nullable=True)  # 分类
    status = db.Column(db.String(20), default='active')  # active/archived/deleted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ArticleData {self.title[:20]}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'keyword': self.keyword,
            'title': self.title,
            'link': self.link,
            'cover': self.cover,
            'source': self.source,
            'abstract': self.abstract,
            'content': self.content,
            'publish_time': self.publish_time,
            'author': self.author,
            'sentiment': self.sentiment,
            'sentiment_score': self.sentiment_score,
            'tags': self.tags,
            'category': self.category,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
