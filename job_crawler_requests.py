# -*- coding: utf-8 -*-
"""
============================================================================
招聘公告数据采集 —— requests + BeautifulSoup 真实可运行版
============================================================================
项目：大数据招聘岗位数据分析（求职项目）
真实数据源：四川公共招聘网 sc91.org.cn（省级官方平台，robots.txt 不存在，
默认允许抓取；已实测 check_robots 通过）

【技术选型说明（面试如实讲）】
本项目共有两套采集实现，按目标网站形态选型：
1. 结构化岗位接口（524 条数据）：51job 用浏览器自动化（强反爬），
   sc91 用 requests 直采 JSON 接口——见 job_crawler_51job.py / job_crawler.py；
2. 本脚本：requests + bs4 解析【静态 HTML】——采集 sc91 的招聘公告
   （列表页嵌详情链接 → 详情页提取标题/来源/时间/正文），
   完整演示 requests+bs4 的标准采集流程与爬虫合规规范。

【页面结构（已实测）】
列表页 /app/article/list/3018.shtml（高校毕业生城乡基层就业岗位，5369 篇）
    静态 HTML 里直接嵌着详情链接：<a href="/app/article/content/66523.shtml?...">
详情页 /app/article/content/{id}.shtml
    div.article-title      公告标题
    div.article            正文（含"发布来源：xxx  发布时间：2026-10-10 10:14"）

运行前安装依赖：
    pip install requests beautifulsoup4 lxml
============================================================================
"""

import csv
import re
import time
import random
from datetime import datetime
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup


# ============================ 配置区 ============================
BASE_URL = "https://www.sc91.org.cn"
LIST_URL = "https://www.sc91.org.cn/app/article/list/3018.shtml"  # 岗位公告栏目

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "zh-CN,zh;q=0.9",
}

DELAY = (2, 4)        # 每次请求间隔秒数（随机区间），控制采集频率
TIMEOUT = 15          # 单次请求超时（秒）
MAX_RETRY = 3         # 请求失败最大重试次数
MAX_ARTICLES = 10     # 采集公告篇数（教学演示取前 10 篇，可调大）
OUTPUT_CSV = "articles_sc91.csv"

FIELD_NAMES = [
    "article_id", "title", "source_org", "publish_date",
    "content_len", "content_preview", "source_url", "collected_at",
]


# ============================ 1. robots 协议检查 ============================
def check_robots(url: str) -> bool:
    """
    采集前读取 robots.txt，判断是否允许访问。
    注意：sc91 不存在 robots.txt（/robots.txt 返回的是 HTML 页面），
    解析失败时按"未声明限制"处理，但仍打印提示留痕。
    """
    rp = RobotFileParser()
    rp.set_url(urljoin(BASE_URL, "/robots.txt"))
    try:
        rp.read()
        ok = rp.can_fetch(HEADERS["User-Agent"], url)
        print(f"robots 检查：{'允许' if ok else '禁止'} 采集 {url}")
        return ok
    except Exception:
        print("提示：未能解析 robots.txt（该站未声明限制），默认允许并留痕。")
        return True


# ============================ 2. 请求页面（重试 + 退避） ============================
def fetch_page(url: str, session: requests.Session):
    """请求网页返回 HTML 文本；失败自动重试并指数退避，最终失败返回 None。"""
    for attempt in range(1, MAX_RETRY + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding   # 自动判编码，防中文乱码
            return resp.text
        except requests.RequestException as e:
            print(f"[重试 {attempt}/{MAX_RETRY}] 请求失败：{e}")
            time.sleep(DELAY[0] * attempt)
    return None


# ============================ 3. bs4 解析：列表页提取文章链接 ============================
def parse_article_links(html: str):
    """
    从列表页提取公告链接。真实结构（已实测）：链接不在 <a href> 里，
    而是嵌在 div.zp_li 的 onclick 属性中（window.open("...")），
    标题在 span.new_li、日期在 span.new_li1 —— 用 bs4 取属性 + 正则提取 URL。
    """
    soup = BeautifulSoup(html, "lxml")
    links = []
    seen = set()
    for item in soup.select("div.zp_li"):
        onclick = item.get("onclick", "")
        m = re.search(r'["\'](/app/article/content/[^"\']+)["\']', onclick)
        if not m:
            continue
        href = m.group(1).split("?")[0]
        if href in seen:                     # 列表页可能重复渲染，按链接去重
            continue
        seen.add(href)
        title_el = item.select_one("span.new_li")
        date_el = item.select_one("span.new_li1")
        links.append({
            "article_id": href.rstrip(".shtml").rsplit("/", 1)[-1],
            "title": title_el.get_text(strip=True) if title_el else "",
            "list_date": date_el.get_text(strip=True) if date_el else "",
            "source_url": urljoin(BASE_URL, href),
        })
    return links


# ============================ 4. bs4 解析：详情页提取公告字段 ============================
def parse_article(html: str, link: dict):
    """从详情页提取标题、发布来源、发布时间、正文预览。"""
    soup = BeautifulSoup(html, "lxml")
    article = soup.select_one("div.article")
    full_text = article.get_text(" ", strip=True) if article else ""

    title_el = soup.select_one(".article-title")
    title = title_el.get_text(strip=True) if title_el else link["title"]

    m_org = re.search(r"发布来源：([^\s]+)", full_text)
    m_date = re.search(r"发布时间：(20\d{2}-\d{2}-\d{2})", full_text)

    return {
        "article_id": link["article_id"],
        "title": title,
        "source_org": m_org.group(1) if m_org else "",
        "publish_date": m_date.group(1) if m_date else "",
        "content_len": len(full_text),
        "content_preview": full_text[:150],
        "source_url": link["source_url"],
    }


# ============================ 5. 保存 CSV ============================
def save_csv(jobs: list, path: str):
    """保存为 CSV，utf-8-sig 编码（带 BOM），Excel 双击打开不乱码。"""
    if not jobs:
        print("没有采集到数据，未生成文件。")
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELD_NAMES)
        writer.writeheader()
        writer.writerows(jobs)


# ============================ 主流程 ============================
def main():
    # 1) 采集前做合规检查
    if not check_robots(LIST_URL):
        print("警告：robots 限制采集，停止。")
        return

    session = requests.Session()

    # 2) 抓列表页，bs4 提取文章链接
    html = fetch_page(LIST_URL, session)
    if html is None:
        print("列表页请求失败，退出。")
        return
    links = parse_article_links(html)
    print(f"列表页解析出 {len(links)} 篇公告")

    # 3) 逐篇抓详情页（随机限速），bs4 提取字段
    articles = []
    for link in links[:MAX_ARTICLES]:
        detail = fetch_page(link["source_url"], session)
        if detail is None:
            print(f"  跳过（请求失败）：{link['title'][:30]}")
            continue
        art = parse_article(detail, link)
        art["collected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        articles.append(art)
        print(f"  已采集：{art['title'][:36]}（{art['publish_date']}）")
        time.sleep(random.uniform(*DELAY))       # 限速：每篇间隔 2~4 秒

    # 4) 落盘
    save_csv(articles, OUTPUT_CSV)
    print(f"采集完成，共 {len(articles)} 条，已保存到 {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
