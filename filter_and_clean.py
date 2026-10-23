# -*- coding: utf-8 -*-
"""岗位定向过滤 + 清洗，生成最终数据集 jobs_final.csv。"""
import csv, re
from collections import Counter

KEEP = ['数据','大数据','数仓','数据库','算法','ai','人工智能','机器学习','深度学习',
        '大模型','nlp','自然语言','计算机视觉','图像','语音','开发','软件','工程师',
        'python','java','后端','前端','爬虫','运维','测试','bi','etl','sql','架构',
        '挖掘','分析','可视化','治理','平台','标注','采集','建模','仓库','模型']
DROP = ['会计','出纳','财务','销售','市场','行政','人事','客服','司机','保安','店长',
        '服务员','前台','采购','营运','运营','店长','收银','仓管','物流专员','经理助理']

SKILLS = {
    "hadoop","spark","hive","hbase","flink","kafka","zookeeper","hdfs","yarn","mapreduce",
    "storm","etl","数据仓库","数据湖","数仓","离线","实时","流计算","批处理",
    "java","python","scala","sql","shell","linux",
    "mysql","oracle","postgresql","redis","mongodb","达梦","gaussdb",
    "数据分析","数据挖掘","数据建模","建模","机器学习","深度学习","人工智能","算法",
    "预测","画像","推荐","nlp","自然语言","计算机视觉","pytorch","tensorflow",
    "数据工程","数据治理","数据质量","数据可视化","bi","tableau","数据平台","数据架构",
    "数据模型","数据清洗","数据采集","爬虫","元数据","数据中台",
    "分布式","微服务","docker","kubernetes","k8s","spring","springboot","mybatis",
    "后端","接口","api","restful","架构","设计模式","jvm","多线程","高并发","性能调优",
    "软件工程","编码","调试",
}

def parse_salary(s):
    if not s or "面议" in s:
        return None, None
    s = s.strip().replace("，", "").replace("·", "-")
    is_year = "年" in s
    def to_yuan(p):
        m = re.search(r"(\d+(?:\.\d+)?)\s*(万|千|k|K)?", p)
        if not m: return None
        v = float(m.group(1)); u = (m.group(2) or "").lower()
        if u == "万": v *= 10000
        elif u in ("千","k"): v *= 1000
        return int(v)
    parts = re.split(r"[-~—]", s)
    if len(parts) >= 2 and to_yuan(parts[0]) and to_yuan(parts[1]):
        lo, hi = to_yuan(parts[0]), to_yuan(parts[1])
    else:
        lo = hi = to_yuan(parts[0])
    if lo and hi and is_year: lo, hi = lo//12, hi//12
    return lo, hi

def classify(t):
    t = t.lower()
    if "标注" in t or "采集" in t: return "数据标注/采集"
    if "架构" in t or "治理" in t or "数仓" in t or "仓库" in t: return "数据架构/仓库"
    if "分析" in t: return "数据分析"
    if "算法" in t or "ai" in t or "人工智能" in t or "机器学习" in t or "深度学习" in t or "大模型" in t: return "AI/算法"
    if "大数据" in t: return "大数据开发"
    if "开发" in t or "工程师" in t or "python" in t or "java" in t or "后端" in t or "前端" in t: return "开发工程师"
    return "其他"

rows = list(csv.reader(open("jobs_51job.csv", encoding="utf-8-sig")))
data = rows[1:]

final, skill_c = [], Counter()
for r in data:
    t = r[0].lower()
    if any(k in t for k in DROP): continue
    if not any(k in t for k in KEEP): continue
    lo, hi = parse_salary(r[4])
    tags = [x.strip() for x in r[5].split("|") if x.strip()]
    skills = [x for x in tags if x.lower() in SKILLS or x in SKILLS]
    cat = classify(t)
    skill_c.update(skills)
    final.append([t, r[1], r[2], r[3], r[4], lo, hi, "|".join(skills), cat])

with open("jobs_final.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["title","company","city","area","salary_raw","salary_min","salary_max","skills","category"])
    w.writerows(final)

print(f"最终数据集：{len(final)} 条大数据岗位")
print(f"城市分布：{dict(Counter(r[2] for r in final))}")
print(f"薪资有效：{sum(1 for r in final if r[5] and r[6])} 条")
print(f"\n【岗位类型】")
for c, n in Counter(r[8] for r in final).most_common():
    print(f"  {c:16s} {n}")
print(f"\n【技能 Top 15】")
for s, n in skill_c.most_common(15):
    print(f"  {s:14s} {n}")
print("\n已保存 jobs_final.csv")
