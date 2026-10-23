# -*- coding: utf-8 -*-
"""
51job 川渝大数据岗位采集（agent-browser 浏览器自动化）
成都(090200) 21 页 + 重庆 31 页，预计 1000+ 条。
"""
import subprocess, json, time, os, csv
from datetime import datetime

NODE = "C:/Users/22397/.workbuddy/binaries/node/versions/22.22.2"
AB = os.path.join(NODE, "node_modules/agent-browser/bin/agent-browser-win32-x64.exe")
ENV = dict(os.environ, PATH=NODE + os.pathsep + os.environ.get("PATH", ""))

def ab(args):
    r = subprocess.run([AB] + args, capture_output=True, text=True, encoding="utf-8", env=ENV, timeout=90)
    return r.stdout.strip()

def ev(js):
    out = ab(["eval", js]).strip()
    try:
        obj = json.loads(out)
        if isinstance(obj, str):   # 输出是带外层引号的 JSON 字符串，需二次解析
            obj = json.loads(obj)
        return obj
    except Exception:
        return out

EXTRACT_JS = """JSON.stringify((function(){var items=document.querySelectorAll('.joblist-item');var out=[];items.forEach(function(it){function q(sel){var el=it.querySelector(sel);return el?el.textContent.trim():'';}var tags=[];it.querySelectorAll('.joblist-item-tags .tags [title]').forEach(function(t){tags.push(t.getAttribute('title'));});var dcs=[];it.querySelectorAll('.comp .bc .dc').forEach(function(d){dcs.push(d.textContent.trim());});out.push({title:q('.jname'),salary:q('.sal'),area:q('.area'),tags:tags,company:q('.cname'),info:dcs});});return {count:out.length, jobs:out};})())"""

def goto_page(n):
    js = ("JSON.stringify((function(){var lis=document.querySelectorAll('.el-pager li.number');var ok=null;"
          "lis.forEach(function(li){if(li.textContent.trim()==='%d'){li.click();ok=1;}});return {ok:ok};})())") % n
    ev(js)
    time.sleep(2.2)

def pages_info():
    js = "JSON.stringify((function(){var last=document.querySelector('.el-pagination li.number:last-of-type');return {pages:last?parseInt(last.textContent.trim()):1};})())"
    return ev(js).get("pages", 1)

def collect(pages, city):
    jobs = []
    for p in range(1, pages + 1):
        d = ev(EXTRACT_JS)
        batch = d.get("jobs", [])
        for j in batch:
            j["city"] = city
        jobs.extend(batch)
        print(f"  [{city}] 第 {p}/{pages} 页，拿到 {len(batch)} 条，累计 {len(jobs)}")
        if p < pages:
            goto_page(p + 1)
    return jobs

all_jobs = []

# ===== 成都 =====
ab(["open", "https://we.51job.com/pc/search?keyword=%E5%A4%A7%E6%95%B0%E6%8D%AE&searchType=2&jobArea=090200"])
time.sleep(1)
ab(["wait", "--load", "load"])
time.sleep(2.5)
cd_pages = pages_info()
print(f"成都大数据岗位：{cd_pages} 页")
all_jobs += collect(cd_pages, "成都")

# ===== 重庆 =====
ev("JSON.stringify((function(){var links=document.querySelectorAll('a.ch');links.forEach(function(a){if((a.textContent||'').trim()==='重庆')a.click();});return 1;})())")
time.sleep(2.5)
cq_pages = pages_info()
print(f"重庆大数据岗位：{cq_pages} 页")
all_jobs += collect(cq_pages, "重庆")

# ===== 去重 + 落盘 =====
seen = set()
uniq = []
for j in all_jobs:
    key = (j["title"], j["company"])
    if key not in seen:
        seen.add(key)
        uniq.append(j)

with open("jobs_51job.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["title", "company", "city", "area", "salary_raw", "tags", "info", "collected_at"])
    for j in uniq:
        w.writerow([j["title"], j["company"], j["city"], j["area"], j["salary"],
                    "|".join(j["tags"]), "|".join(j["info"]),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

print(f"\n完成：采集 {len(all_jobs)} 条，去重后 {len(uniq)} 条，已保存 jobs_51job.csv")
