"""
舆情数据抓取模块 - 爬取搜索引擎结果
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
import re
from urllib.parse import quote

class SearchCrawler:
    """搜索引擎爬虫"""
    
    def __init__(self, custom_headers=None):
        # 默认请求头 - 模拟真实浏览器
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 允许用户自定义请求头
        if custom_headers:
            self.headers.update(custom_headers)
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_baidu(self, keyword, pages=1):
        """
        爬取百度搜索结果
        :param keyword: 搜索关键词
        :param pages: 爬取页数
        :return: 搜索结果列表
        """
        results = []
        
        for page in range(pages):
            encoded_keyword = quote(keyword)
            url = f'https://www.baidu.com/s?wd={encoded_keyword}&pn={page * 10}'
            
            try:
                response = self.session.get(url, timeout=10)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 解析搜索结果
                    items = soup.select('.result.c-container')
                    for item in items:
                        try:
                            # 标题
                            title_elem = item.select_one('h3 a')
                            title = title_elem.get_text(strip=True) if title_elem else ''
                            link = title_elem.get('href', '') if title_elem else ''
                            
                            # 摘要
                            abstract_elem = item.select_one('.c-abstract') or item.select_one('.content-right_8Zs40')
                            abstract = abstract_elem.get_text(strip=True) if abstract_elem else ''
                            
                            # 来源
                            source_elem = item.select_one('.c-showurl') or item.select_one('.source_1Vdff')
                            source = source_elem.get_text(strip=True) if source_elem else ''
                            
                            if title:
                                results.append({
                                    'title': title,
                                    'link': link,
                                    'abstract': abstract,
                                    'source': source,
                                    'keyword': keyword,
                                    'engine': 'baidu',
                                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                        except Exception as e:
                            continue
                
                # 随机延时，避免被封
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f'爬取百度第{page+1}页失败: {e}')
                continue
        
        return results
    
    def search_bing(self, keyword, pages=1):
        """
        爬取必应搜索结果
        :param keyword: 搜索关键词
        :param pages: 爬取页数
        :return: 搜索结果列表
        """
        results = []
        
        # 简化请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        
        for page in range(pages):
            # URL编码关键词
            encoded_keyword = quote(keyword)
            url = f'https://cn.bing.com/search?q={encoded_keyword}&first={page * 10 + 1}'
            
            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 解析搜索结果 - 多种选择器兼容
                    items = soup.select('.b_algo')
                    
                    for item in items:
                        try:
                            # 标题和链接
                            title_elem = item.select_one('h2 a')
                            title = title_elem.get_text(strip=True) if title_elem else ''
                            link = title_elem.get('href', '') if title_elem else ''
                            
                            # 摘要 - 多种选择器
                            abstract_elem = (
                                item.select_one('.b_caption p') or 
                                item.select_one('.b_paractl') or
                                item.select_one('p')
                            )
                            abstract = abstract_elem.get_text(strip=True) if abstract_elem else ''
                            
                            # 来源
                            source_elem = item.select_one('cite') or item.select_one('.b_attribution cite')
                            source = source_elem.get_text(strip=True) if source_elem else ''
                            
                            # 清理来源URL
                            if source:
                                source = source.replace('https://', '').replace('http://', '').split('/')[0]
                            
                            if title:
                                results.append({
                                    'title': title,
                                    'link': link,
                                    'abstract': abstract,
                                    'source': source,
                                    'keyword': keyword,
                                    'engine': 'bing',
                                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                        except Exception as e:
                            continue
                    
                    # 如果没有找到结果，尝试其他选择器
                    if not results:
                        items = soup.select('li.b_algo, .b_ans')
                        for item in items:
                            try:
                                title_elem = item.select_one('h2 a, h3 a, a')
                                if title_elem:
                                    title = title_elem.get_text(strip=True)
                                    link = title_elem.get('href', '')
                                    if title and link.startswith('http'):
                                        results.append({
                                            'title': title,
                                            'link': link,
                                            'abstract': '',
                                            'source': '',
                                            'keyword': keyword,
                                            'engine': 'bing',
                                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        })
                            except:
                                continue
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f'爬取必应第{page+1}页失败: {e}')
                continue
        
        return results
    
    def search(self, keyword, engine='baidu', pages=1):
        """
        统一搜索接口
        :param keyword: 搜索关键词
        :param engine: 搜索引擎 (baidu/bing/all)
        :param pages: 爬取页数
        :return: 搜索结果列表
        """
        results = []
        
        if engine in ['baidu', 'all']:
            results.extend(self.search_baidu(keyword, pages))
        
        if engine in ['bing', 'all']:
            results.extend(self.search_bing(keyword, pages))
        
        return results


# 简单的情感分析
class SentimentAnalyzer:
    """简单情感分析器"""
    
    def __init__(self):
        # 正面词汇
        self.positive_words = [
            '好', '优秀', '成功', '增长', '提升', '突破', '创新', '领先',
            '喜欢', '满意', '推荐', '赞', '棒', '优质', '高效', '便捷',
            '安全', '稳定', '可靠', '专业', '权威', '正规', '合法'
        ]
        
        # 负面词汇
        self.negative_words = [
            '差', '失败', '下降', '问题', '风险', '危机', '投诉', '曝光',
            '骗', '假', '坑', '烂', '垃圾', '差评', '不满', '愤怒',
            '违法', '违规', '处罚', '罚款', '事故', '伤亡', '损失'
        ]
    
    def analyze(self, text):
        """
        分析文本情感
        :param text: 待分析文本
        :return: 情感结果 (positive/negative/neutral) 和分数
        """
        if not text:
            return {'sentiment': 'neutral', 'score': 0}
        
        positive_count = sum(1 for word in self.positive_words if word in text)
        negative_count = sum(1 for word in self.negative_words if word in text)
        
        score = positive_count - negative_count
        
        if score > 0:
            sentiment = 'positive'
        elif score < 0:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': score,
            'positive_count': positive_count,
            'negative_count': negative_count
        }


if __name__ == '__main__':
    # 测试爬虫
    crawler = SearchCrawler()
    results = crawler.search('Python', engine='bing', pages=1)
    
    print(f'共爬取 {len(results)} 条结果:')
    for r in results[:3]:
        print(f"- {r['title']}")
