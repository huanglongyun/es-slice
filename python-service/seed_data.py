"""
ES 测试数据初始化脚本
创建 3 个索引，每个插入约 100 条语料数据
"""
from elasticsearch import Elasticsearch
import random
import time

ES_HOST = "elasticsearch"
ES_PORT = 9200

es = Elasticsearch(f"http://{ES_HOST}:{ES_PORT}")

# ===================== 索引1: news_articles (新闻语料) =====================
INDEX_NEWS = "news_articles"
news_mapping = {
    "mappings": {
        "properties": {
            "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "content": {"type": "text"},
            "author": {"type": "keyword"},
            "category": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "source": {"type": "keyword"},
            "view_count": {"type": "integer"},
            "publish_date": {"type": "date", "format": "yyyy-MM-dd"},
            "status": {"type": "keyword"}
        }
    }
}

# ===================== 索引2: product_docs (产品文档) =====================
INDEX_PRODUCT = "product_docs"
product_mapping = {
    "mappings": {
        "properties": {
            "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "description": {"type": "text"},
            "category": {"type": "keyword"},
            "brand": {"type": "keyword"},
            "price": {"type": "float"},
            "stock": {"type": "integer"},
            "specs": {"type": "object", "enabled": False},
            "rating": {"type": "float"},
            "create_date": {"type": "date", "format": "yyyy-MM-dd"}
        }
    }
}

# ===================== 索引3: user_feedback (用户反馈) =====================
INDEX_FEEDBACK = "user_feedback"
feedback_mapping = {
    "mappings": {
        "properties": {
            "user_name": {"type": "keyword"},
            "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "content": {"type": "text"},
            "category": {"type": "keyword"},
            "sentiment": {"type": "keyword"},
            "rating": {"type": "integer"},
            "device": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "submit_date": {"type": "date", "format": "yyyy-MM-dd"},
            "resolved": {"type": "keyword"}
        }
    }
}

# ===================== 新闻数据生成 =====================
news_templates = [
    ("人工智能在医疗诊断中的突破性应用", "近年来，AI技术在医疗影像分析领域取得重大进展。深度学习模型在CT影像识别上的准确率已达到95%以上，特别是在肺结节检测、眼底病变识别等方面表现尤为突出。"),
    ("全球气候变化峰会达成新协议", "来自190多个国家的代表在最新一轮气候谈判中达成了具有里程碑意义的减排协议。各方承诺到2030年前将碳排放量减少45%，这是应对全球变暖的关键一步。"),
    ("新能源汽车市场持续高速增长", "据最新统计数据显示，今年第一季度新能源汽车销量同比增长68%，市场渗透率首次突破40%大关。比亚迪、特斯拉等头部企业竞争日趋白热化。"),
    ("5G技术推动智慧城市建设加速", "随着5G网络的全面覆盖，智慧城市建设进入快车道。从智能交通管理到远程医疗，从智慧路灯到环境监测，5G技术正在重塑城市生活的方方面面。"),
    ("区块链技术在供应链管理中的应用", "区块链技术凭借其去中心化、不可篡改的特性，在供应链领域找到了理想的应用场景。通过智能合约自动执行采购协议，大幅提升了供应链的透明度和效率。"),
    ("教育改革：双减政策实施效果评估", "实施一年的双减政策已初见成效，学生课外负担明显减轻。调查显示，超过70%的家长表示孩子有更多时间进行兴趣培养和体育锻炼，教育生态正在积极转变。"),
    ("量子计算取得里程碑式突破", "科研团队成功实现了100个量子比特的纠缠态操控，这标志着量子计算向实用化迈出了关键一步。该成果有望在密码学、药物研发等领域带来革命性变化。"),
    ("直播电商行业进入精细化运营时代", "随着行业增速放缓，直播电商正从野蛮生长转向精细化运营。头部主播开始重视供应链建设，品牌自播占比持续提升，行业生态正在重塑。"),
]

news_authors = ["张明", "李华", "王芳", "陈雷", "刘洋", "赵敏", "周杰", "吴萍"]
news_categories = ["科技", "社会", "经济", "教育", "健康", "体育", "文化", "娱乐"]
news_sources = ["新华社", "人民日报", "科技日报", "经济观察报", "南方周末", "澎湃新闻"]
news_tags_pool = ["前沿技术", "政策解读", "市场分析", "行业趋势", "深度报道", "独家", "评论", "数据报告"]

def gen_news_docs(n=100):
    docs = []
    for i in range(n):
        title = f"测试新闻_{i+1}: {random.choice(news_templates)[0]}"
        content = random.choice(news_templates)[1]
        docs.append({
            "_index": INDEX_NEWS,
            "_id": f"news_{i+1:04d}",
            "_source": {
                "title": title,
                "content": content + f"（第{i+1}期详细内容补充）",
                "author": random.choice(news_authors),
                "category": random.choice(news_categories),
                "tags": random.sample(news_tags_pool, k=random.randint(1, 3)),
                "source": random.choice(news_sources),
                "view_count": random.randint(100, 99999),
                "publish_date": f"202{random.randint(1,5)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "status": random.choice(["published", "draft", "reviewing"]),
            }
        })
    return docs

# ===================== 产品数据生成 =====================
brands = ["华为", "小米", "苹果", "三星", "OPPO", "vivo", "联想", "华硕"]
categories = ["智能手机", "笔记本电脑", "平板电脑", "智能手表", "耳机", "显示器", "键盘", "鼠标"]
product_names = [
    "旗舰版Pro Max", "青春版Lite", "商务版Elite", "游戏版Gaming",
    "标准版Standard", "增强版Enhanced", "迷你版Mini", "至尊版Ultra"
]

def gen_product_docs(n=100):
    docs = []
    for i in range(n):
        brand = random.choice(brands)
        cat = random.choice(categories)
        name = f"{brand} {random.choice(product_names)}"
        docs.append({
            "_index": INDEX_PRODUCT,
            "_id": f"prod_{i+1:04d}",
            "_source": {
                "name": name,
                "description": f"{name}是一款高性能{cat}产品，采用最新技术工艺打造，支持多种智能功能。无论是日常使用还是专业场景，都能带来卓越体验。",
                "category": cat,
                "brand": brand,
                "price": round(random.uniform(99, 9999), 2),
                "stock": random.randint(0, 5000),
                "specs": {
                    "color": random.choice(["黑色", "白色", "蓝色", "红色"]),
                    "weight": f"{random.uniform(100, 2000):.0f}g",
                    "warranty": f"{random.randint(1,3)}年"
                },
                "rating": round(random.uniform(3.0, 5.0), 1),
                "create_date": f"202{random.randint(3,6)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            }
        })
    return docs

# ===================== 反馈数据生成 =====================
feedback_templates = [
    ("界面操作不够流畅", "在使用过程中发现界面切换有明显的卡顿感，特别是在数据加载较多的时候，希望能够优化性能表现。"),
    ("功能很实用但缺少导出选项", "整体体验不错，功能设计合理。但现在只能在线查看数据，如果能增加导出Excel的功能就更好了。"),
    ("客服响应速度太慢", "提交工单后等了三天才收到回复，效率太低了。建议增加在线客服功能，提高问题处理速度。"),
    ("新版本更新后出现了兼容性问题", "自从更新到最新版本后，在Windows系统上频繁闪退，之前的老版本反而更稳定。请尽快修复。"),
    ("搜索功能的准确度有待提高", "搜索结果经常不相关，关键词匹配度较差。建议优化搜索算法，支持模糊搜索和同义词匹配。"),
    ("产品设计美观大方", "新版的UI设计很漂亮，配色方案很舒服，操作流程也很清晰。继续保持这样的设计水准！"),
    ("希望能增加多语言支持", "目前只有中文界面，海外团队使用不太方便。希望能尽快支持英文和日文界面。"),
    ("数据安全性的担忧", "最近发现系统有一些未知的登录尝试记录，建议加强账户安全防护措施，比如增加双因素认证。"),
]

feedback_users = ["张三", "李四", "王五", "赵六", "孙七", "周八", "吴九", "郑十"]
feedback_categories = ["功能建议", "性能问题", "Bug报告", "用户体验", "安全相关", "兼容性", "其他"]
sentiments = ["positive", "negative", "neutral"]
devices = ["iOS", "Android", "Windows", "macOS", "Web"]
feedback_tags = ["紧急", "已跟进", "待确认", "已知问题", "新需求", "高优先级"]

def gen_feedback_docs(n=100):
    docs = []
    for i in range(n):
        title, content = random.choice(feedback_templates)
        docs.append({
            "_index": INDEX_FEEDBACK,
            "_id": f"fb_{i+1:04d}",
            "_source": {
                "user_name": random.choice(feedback_users),
                "title": title,
                "content": content + f"（第{i+1}次提交）",
                "category": random.choice(feedback_categories),
                "sentiment": random.choice(sentiments),
                "rating": random.randint(1, 5),
                "device": random.choice(devices),
                "tags": random.sample(feedback_tags, k=random.randint(1, 3)),
                "submit_date": f"202{random.randint(4,6)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "resolved": random.choice(["是", "否"]),
            }
        })
    return docs

# ===================== 执行 =====================
def main():
    print("等待 ES 就绪...")
    for _ in range(30):
        try:
            if es.ping():
                break
        except Exception:
            pass
        time.sleep(2)
    else:
        print("ES 连接失败")
        return

    print("ES 已连接")

    # 创建索引
    for idx_name, mapping in [
        (INDEX_NEWS, news_mapping),
        (INDEX_PRODUCT, product_mapping),
        (INDEX_FEEDBACK, feedback_mapping),
    ]:
        if es.indices.exists(index=idx_name):
            es.indices.delete(index=idx_name)
        es.indices.create(index=idx_name, body=mapping)
        print(f"索引 {idx_name} 已创建")

    # 批量插入数据
    from elasticsearch.helpers import bulk

    all_docs = gen_news_docs(100) + gen_product_docs(100) + gen_feedback_docs(100)
    success, errors = bulk(es, all_docs, raise_on_error=False)
    print(f"已插入 {success} 条文档，错误 {len(errors) if isinstance(errors, list) else errors} 条")

    # 验证
    for idx in [INDEX_NEWS, INDEX_PRODUCT, INDEX_FEEDBACK]:
        es.indices.refresh(index=idx)
        count = es.count(index=idx)["count"]
        print(f"  {idx}: {count} 条")

    print("初始化完成！")

if __name__ == "__main__":
    main()
