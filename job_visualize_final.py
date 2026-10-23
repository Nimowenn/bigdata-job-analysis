# -*- coding: utf-8 -*-
"""基于 jobs_final.csv（399 条大数据岗位）重新出 4 张可视化。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
import csv
from collections import Counter

rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
rcParams["axes.unicode_minus"] = False
C_MAIN, C_HIGH = "#2E6E9E", "#E07A3F"

rows = list(csv.reader(open("jobs_final.csv", encoding="utf-8-sig")))
data = rows[1:]

# 薪资中值
mids = []
for r in data:
    if r[5] and r[6]:
        mids.append((int(r[5]) + int(r[6])) / 2)

# 图1：薪资分布直方图（截断到 25000 元，覆盖主流）
fig, ax = plt.subplots(figsize=(8, 4.5))
valid = [m for m in mids if m <= 25000]
ax.hist(valid, bins=range(0, 26000, 2000), color=C_MAIN, edgecolor="white")
med = sorted(valid)[len(valid)//2]
ax.axvline(med, color=C_HIGH, linestyle="--", linewidth=1.5, label=f"中位数 {med:.0f} 元")
ax.set_xlabel("月薪（元）", fontsize=12)
ax.set_ylabel("岗位数量", fontsize=12)
ax.set_title(f"川渝大数据岗位薪资分布（{len(valid)} 条，超出 2.5 万未计）", fontsize=14)
ax.legend(); ax.grid(axis="y", color="#D9D9D9", linewidth=0.5)
fig.tight_layout(); fig.savefig("salary_dist.png", dpi=150); plt.close(fig)

# 图2：技能词频 Top 15
skills = Counter()
for r in data:
    for s in r[7].split("|"):
        if s:
            skills[s] += 1
top = skills.most_common(15)[::-1]
fig, ax = plt.subplots(figsize=(8, 6))
ax.barh([t[0] for t in top], [t[1] for t in top], color=C_MAIN, edgecolor="white")
for i, (k, v) in enumerate(top):
    ax.text(v + 0.3, i, str(v), va="center", fontsize=10)
ax.set_xlabel("出现次数", fontsize=12)
ax.set_title("大数据岗位技能要求 Top 15（399 条岗位）", fontsize=14)
ax.grid(axis="x", color="#D9D9D9", linewidth=0.5)
fig.tight_layout(); fig.savefig("skill_top.png", dpi=150); plt.close(fig)

# 图3：岗位类型分布
cats = Counter(r[8] for r in data)
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(cats.keys(), cats.values(), color=C_MAIN, edgecolor="white")
for i, (k, v) in enumerate(cats.items()):
    ax.text(i, v + 2, str(v), ha="center", fontsize=11)
ax.set_ylabel("岗位数量", fontsize=12)
ax.set_title("大数据岗位类型分布（399 条）", fontsize=14)
ax.grid(axis="y", color="#D9D9D9", linewidth=0.5)
fig.tight_layout(); fig.savefig("category_dist.png", dpi=150); plt.close(fig)

# 图4：成都 vs 重庆 岗位数 + 薪资箱线（双子图）
cd = [ (int(r[5])+int(r[6]))/2 for r in data if r[2]=="成都" and r[5] and r[6] ]
cq = [ (int(r[5])+int(r[6]))/2 for r in data if r[2]=="重庆" and r[5] and r[6] ]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
ncd, ncq = sum(1 for r in data if r[2]=="成都"), sum(1 for r in data if r[2]=="重庆")
ax1.bar(["成都", "重庆"], [ncd, ncq], color=[C_MAIN, C_HIGH], edgecolor="white")
for i, v in enumerate([ncd, ncq]):
    ax1.text(i, v + 2, str(v), ha="center", fontsize=12)
ax1.set_title("岗位数量对比", fontsize=13); ax1.grid(axis="y", color="#D9D9D9", linewidth=0.5)
bp = ax2.boxplot([cd, cq], tick_labels=["成都", "重庆"], patch_artist=True)
for patch, c in zip(bp["boxes"], [C_MAIN, C_HIGH]):
    patch.set_facecolor(c); patch.set_alpha(0.75)
for i, vals in enumerate([cd, cq], 1):
    ax2.text(i, sorted(vals)[len(vals)//2], f"中位 {sorted(vals)[len(vals)//2]:.0f}", ha="center", fontsize=10, va="bottom")
ax2.set_title("月薪分布对比", fontsize=13); ax2.grid(axis="y", color="#D9D9D9", linewidth=0.5)
fig.tight_layout(); fig.savefig("city_salary.png", dpi=150); plt.close(fig)

print("已生成 4 张图：salary_dist.png / skill_top.png / category_dist.png / city_salary.png")
