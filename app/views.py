"""
路由和业务逻辑处理
"""
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from app.database import verify_user, create_user, get_user_by_username

# 创建蓝图
main_bp = Blueprint('main', __name__)


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@main_bp.route('/')
def index():
    """首页/登录页"""
    # 如果已登录，直接跳转到后台
    if 'user_id' in session:
        return redirect(url_for('main.admin'))
    return render_template('index.html')


@main_bp.route('/admin')
@login_required
def admin():
    """后台管理主页 - 需要登录"""
    return render_template('layout.html')


@main_bp.route('/sentiment')
@login_required
def sentiment():
    """舆情分析页面"""
    return render_template('sentiment.html')


@main_bp.route('/data_collect')
@login_required
def data_collect():
    """数据采集管理页面"""
    return render_template('data_collect.html')


@main_bp.route('/login', methods=['POST'])
def login():
    """登录处理 - 验证数据库中的用户"""
    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'code': 1, 'msg': '请输入用户名和密码'})
    
    # 从数据库验证用户
    user = verify_user(username, password)
    if user:
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        return jsonify({'code': 0, 'msg': '登录成功'})
    
    return jsonify({'code': 1, 'msg': '用户名或密码错误'})


@main_bp.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('main.index'))


@main_bp.route('/api/users', methods=['GET'])
def get_users():
    """获取用户列表 API"""
    from app.models import User
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    pagination = User.query.paginate(page=page, per_page=limit, error_out=False)
    users = [user.to_dict() for user in pagination.items]
    
    return jsonify({
        'code': 0,
        'msg': 'success',
        'count': pagination.total,
        'data': users
    })


# ==================== 舆情分析 API ====================

@main_bp.route('/api/crawl', methods=['POST'])
@login_required
def start_crawl():
    """启动爬取任务"""
    from datetime import datetime
    from app import db
    from app.models import SearchResult, CrawlTask
    from app.crawler import SearchCrawler, SentimentAnalyzer
    
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    engine = data.get('engine', 'bing')  # baidu/bing/all
    pages = data.get('pages', 1)
    
    if not keyword:
        return jsonify({'code': 1, 'msg': '请输入搜索关键词'})
    
    if pages > 5:
        pages = 5  # 限制最大页数
    
    try:
        # 创建任务记录
        task = CrawlTask(keyword=keyword, engine=engine, pages=pages, status='running')
        db.session.add(task)
        db.session.commit()
        
        # 执行爬取
        crawler = SearchCrawler()
        analyzer = SentimentAnalyzer()
        results = crawler.search(keyword, engine=engine, pages=pages)
        
        # 保存结果并分析情感
        saved_count = 0
        for item in results:
            # 情感分析
            text = item['title'] + ' ' + item['abstract']
            sentiment_result = analyzer.analyze(text)
            
            result = SearchResult(
                keyword=keyword,
                title=item['title'],
                link=item['link'],
                abstract=item['abstract'],
                source=item['source'],
                engine=item['engine'],
                sentiment=sentiment_result['sentiment'],
                sentiment_score=sentiment_result['score']
            )
            db.session.add(result)
            saved_count += 1
        
        # 更新任务状态
        task.status = 'completed'
        task.result_count = saved_count
        task.completed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': f'爬取完成，共获取 {saved_count} 条结果',
            'data': {'task_id': task.id, 'count': saved_count}
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'msg': f'爬取失败: {str(e)}'})


@main_bp.route('/api/search_results', methods=['GET'])
@login_required
def get_search_results():
    """获取舆情数据列表"""
    from app.models import SearchResult
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    keyword = request.args.get('keyword', '')
    sentiment = request.args.get('sentiment', '')
    
    query = SearchResult.query
    
    if keyword:
        query = query.filter(SearchResult.keyword.like(f'%{keyword}%'))
    if sentiment:
        query = query.filter(SearchResult.sentiment == sentiment)
    
    query = query.order_by(SearchResult.crawl_time.desc())
    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    
    return jsonify({
        'code': 0,
        'msg': 'success',
        'count': pagination.total,
        'data': [r.to_dict() for r in pagination.items]
    })


@main_bp.route('/api/sentiment_stats', methods=['GET'])
@login_required
def get_sentiment_stats():
    """获取情感统计数据"""
    from app import db
    from app.models import SearchResult
    from sqlalchemy import func
    
    keyword = request.args.get('keyword', '')
    
    query = db.session.query(
        SearchResult.sentiment,
        func.count(SearchResult.id).label('count')
    )
    
    if keyword:
        query = query.filter(SearchResult.keyword.like(f'%{keyword}%'))
    
    stats = query.group_by(SearchResult.sentiment).all()
    
    result = {'positive': 0, 'negative': 0, 'neutral': 0}
    for sentiment, count in stats:
        if sentiment in result:
            result[sentiment] = count
    
    total = sum(result.values())
    
    return jsonify({
        'code': 0,
        'data': {
            'stats': result,
            'total': total
        }
    })


@main_bp.route('/api/crawl_tasks', methods=['GET'])
@login_required
def get_crawl_tasks():
    """获取爬取任务列表"""
    from app.models import CrawlTask
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    pagination = CrawlTask.query.order_by(CrawlTask.created_at.desc()).paginate(
        page=page, per_page=limit, error_out=False
    )
    
    return jsonify({
        'code': 0,
        'msg': 'success',
        'count': pagination.total,
        'data': [t.to_dict() for t in pagination.items]
    })


# ==================== 数据采集管理 API ====================

# 存储采集任务进度
collect_tasks = {}

@main_bp.route('/api/collect/start', methods=['POST'])
@login_required
def start_collect():
    """启动数据采集任务"""
    import uuid
    import threading
    from app import db
    from app.models import CollectedData
    from app.crawler import SearchCrawler
    
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    engine = data.get('engine', 'bing')
    pages = data.get('pages', 1)
    
    if not keyword:
        return jsonify({'code': 1, 'msg': '请输入采集关键词'})
    
    # 生成任务ID
    task_id = str(uuid.uuid4())[:8]
    
    # 初始化任务状态
    collect_tasks[task_id] = {
        'status': 'running',
        'progress': 0,
        'message': '正在初始化...',
        'keyword': keyword,
        'engine': engine,
        'pages': pages
    }
    
    # 在后台线程执行采集
    def do_collect():
        try:
            from app import create_app
            app = create_app('development')
            
            with app.app_context():
                collect_tasks[task_id]['progress'] = 10
                collect_tasks[task_id]['message'] = '正在连接搜索引擎...'
                
                crawler = SearchCrawler()
                
                collect_tasks[task_id]['progress'] = 20
                collect_tasks[task_id]['message'] = f'正在搜索"{keyword}"...'
                
                results = crawler.search(keyword, engine=engine, pages=pages)
                
                collect_tasks[task_id]['progress'] = 60
                collect_tasks[task_id]['message'] = f'已获取 {len(results)} 条结果，正在处理...'
                
                # 保存到临时表
                for i, item in enumerate(results):
                    # 尝试提取封面图片
                    cover = extract_cover_from_url(item.get('link', ''))
                    
                    collected = CollectedData(
                        task_id=task_id,
                        keyword=keyword,
                        title=item.get('title', ''),
                        link=item.get('link', ''),
                        cover=cover,
                        source=item.get('source', ''),
                        abstract=item.get('abstract', ''),
                        deep_crawled=False,
                        is_saved=False
                    )
                    db.session.add(collected)
                    
                    # 更新进度
                    progress = 60 + int((i + 1) / len(results) * 35)
                    collect_tasks[task_id]['progress'] = progress
                    collect_tasks[task_id]['message'] = f'正在保存数据 ({i+1}/{len(results)})...'
                
                db.session.commit()
                
                collect_tasks[task_id]['progress'] = 100
                collect_tasks[task_id]['message'] = f'采集完成，共 {len(results)} 条数据'
                collect_tasks[task_id]['status'] = 'completed'
                
        except Exception as e:
            collect_tasks[task_id]['status'] = 'failed'
            collect_tasks[task_id]['message'] = str(e)
    
    thread = threading.Thread(target=do_collect)
    thread.start()
    
    return jsonify({
        'code': 0,
        'msg': '采集任务已启动',
        'data': {'task_id': task_id}
    })


def extract_cover_from_url(url):
    """从URL提取可能的封面图片"""
    # 简单的封面提取逻辑，可以后续扩展
    if not url:
        return None
    # 返回一个基于域名的占位图或None
    return None


@main_bp.route('/api/collect/progress/<task_id>')
@login_required
def get_collect_progress(task_id):
    """获取采集进度"""
    if task_id not in collect_tasks:
        return jsonify({'code': 1, 'msg': '任务不存在'})
    
    task = collect_tasks[task_id]
    return jsonify({
        'code': 0,
        'data': {
            'status': task['status'],
            'progress': task['progress'],
            'message': task['message']
        }
    })


@main_bp.route('/api/collect/data/<task_id>')
@login_required
def get_collect_data(task_id):
    """获取采集的数据列表"""
    from app.models import CollectedData
    
    data = CollectedData.query.filter_by(task_id=task_id).order_by(CollectedData.id.asc()).all()
    
    return jsonify({
        'code': 0,
        'data': [d.to_dict() for d in data]
    })


@main_bp.route('/api/collect/deep/<int:data_id>', methods=['POST'])
@login_required
def deep_collect(data_id):
    """深度采集单条数据"""
    import requests
    from bs4 import BeautifulSoup
    from app import db
    from app.models import CollectedData
    
    data = CollectedData.query.get(data_id)
    if not data:
        return jsonify({'code': 1, 'msg': '数据不存在'})
    
    if data.deep_crawled:
        return jsonify({'code': 1, 'msg': '已经深度采集过了'})
    
    try:
        # 请求原始页面
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        }
        response = requests.get(data.link, headers=headers, timeout=10)
        response.encoding = response.apparent_encoding or 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取正文内容
        content = ''
        # 尝试多种选择器
        content_selectors = ['article', '.article-content', '.content', '.post-content', '#content', 'main', '.main-content']
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                content = elem.get_text(strip=True, separator='\n')
                break
        
        if not content:
            # 提取body中的所有p标签
            paragraphs = soup.select('p')
            content = '\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
        
        # 提取封面图片
        cover = None
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image:
            cover = og_image.get('content')
        else:
            # 尝试找第一张大图
            imgs = soup.select('img[src]')
            for img in imgs:
                src = img.get('src', '')
                if src and not 'logo' in src.lower() and not 'icon' in src.lower():
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        from urllib.parse import urlparse
                        parsed = urlparse(data.link)
                        src = f"{parsed.scheme}://{parsed.netloc}{src}"
                    cover = src
                    break
        
        # 提取发布时间
        publish_time = None
        time_selectors = ['time', '.time', '.date', '.publish-time', 'meta[property="article:published_time"]']
        for selector in time_selectors:
            elem = soup.select_one(selector)
            if elem:
                publish_time = elem.get('datetime') or elem.get('content') or elem.get_text(strip=True)
                break
        
        # 提取作者
        author = None
        author_selectors = ['.author', '.writer', 'meta[name="author"]', '.byline']
        for selector in author_selectors:
            elem = soup.select_one(selector)
            if elem:
                author = elem.get('content') or elem.get_text(strip=True)
                break
        
        # 更新数据
        data.content = content[:5000] if content else ''  # 限制长度
        data.cover = cover or data.cover
        data.publish_time = publish_time
        data.author = author
        data.deep_crawled = True
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '深度采集成功',
            'data': {
                'content': data.content[:200] + '...' if len(data.content) > 200 else data.content,
                'cover': data.cover,
                'publish_time': data.publish_time,
                'author': data.author
            }
        })
        
    except Exception as e:
        return jsonify({'code': 1, 'msg': f'深度采集失败: {str(e)}'})


@main_bp.route('/api/collect/save', methods=['POST'])
@login_required
def save_collect_data():
    """保存采集数据到正式数据库"""
    from app import db
    from app.models import CollectedData, ArticleData
    from app.crawler import SentimentAnalyzer
    
    data = request.get_json()
    ids = data.get('ids', [])
    
    if not ids:
        return jsonify({'code': 1, 'msg': '请选择要保存的数据'})
    
    analyzer = SentimentAnalyzer()
    saved_count = 0
    
    try:
        for data_id in ids:
            collected = CollectedData.query.get(data_id)
            if collected and not collected.is_saved:
                # 情感分析
                text = (collected.title or '') + ' ' + (collected.abstract or '')
                sentiment_result = analyzer.analyze(text)
                
                # 创建正式数据
                article = ArticleData(
                    keyword=collected.keyword,
                    title=collected.title,
                    link=collected.link,
                    cover=collected.cover,
                    source=collected.source,
                    abstract=collected.abstract,
                    content=collected.content,
                    publish_time=collected.publish_time,
                    author=collected.author,
                    sentiment=sentiment_result['sentiment'],
                    sentiment_score=sentiment_result['score']
                )
                db.session.add(article)
                
                # 标记已保存
                collected.is_saved = True
                saved_count += 1
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': f'成功保存 {saved_count} 条数据',
            'data': {'saved_count': saved_count}
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'msg': f'保存失败: {str(e)}'})
