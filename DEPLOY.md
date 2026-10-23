# 部署到 GitHub Pages（3 步）

## 1. 建仓库并上传

1. 在 GitHub 新建一个**公开（Public）**仓库，例如 `bigdata-job-analysis`；
2. 把本目录（作品集仓库）里的所有文件 push 上去：

```bash
cd 作品集仓库
git init
git add .
git commit -m "init: 大数据岗位招聘数据分析作品集"
git branch -M main
git remote add origin https://github.com/你的用户名/bigdata-job-analysis.git
git push -u origin main
```

## 2. 开启 Pages

1. 打开仓库页面 → **Settings** → 左侧 **Pages**；
2. **Source** 选 `Deploy from a branch`；
3. **Branch** 选 `main`，目录选 `/ (root)`，点 Save。

## 3. 访问

约 1 分钟后访问：

```
https://你的用户名.github.io/bigdata-job-analysis/
```

- 首页是 `index.html`（项目概览）
- 完整报告是 `report.html`（页面内可互相跳转）

---

## 说明

- **index.html / report.html 已内嵌全部图片**（base64），无需单独传图，任何设备打开都完整显示；
- **README.md** 是 GitHub 仓库首页（在仓库页面展示，非 Pages 网站），它的图片和 mermaid 由 GitHub 自动渲染；
- 4 张图表 PNG + `flow.png` 保留作为项目产物，README.md 引用它们；
- 四个 `.py` 脚本（采集/过滤清洗/可视化/requests+bs4 框架）与两份 CSV（原始 524 条 / 最终 399 条）是项目的完整源码和数据，供面试官查看。

## 常见问题

- **打开显示 404**：检查 Pages 的 Branch 是否选对、是否 push 成功；
- **想改首页内容**：改 `作品集仓库` 目录里的源文件后，重新运行 `md2html.py` 生成 HTML 再替换；
- **仓库是私有的**：Pages 只有付费的 GitHub Pro 才能开启，免费账号请用公开仓库。
