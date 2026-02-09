# 🚲 Bilibili E-Bike New Standard Comment Analysis (B站电动车新国标评论分析)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Kimi AI](https://img.shields.io/badge/AI-Kimi%20Powered-purple)
![Labeling](https://img.shields.io/badge/Labeling-Human%20in%20the%20loop-green)

本项目旨在构建一个关于 B 站“电动车新国标”评论的高质量情感分析数据集。为了解决传统人工标注效率低、成本高的问题，本项目采用 Kimi 大模型 (Moonshot AI) 对海量评论数据进行自动化预标注，极大简化了人工标注的工作流。

## 🚀 项目亮点

* AI 驱动提效: 利用 `kimi_labeling.py` 脚本调用 Kimi API，自动完成情感倾向判断与观点分类，大幅减少人工阅读和打标的时间。
* 人机协作 (Human-in-the-loop): 人工只需对 Kimi 的预标注结果进行校验和微调，专注于处理反讽、隐喻等 AI 难以识别的复杂语料。
* 标准化流程: 结合详细的 [标注标准 (standard.md)](./standard.md)，确保 AI 预标注与人工校验的一致性。

## 📂 项目结构

```text
cxy_ai_project/
├── kimi_labeling.py                            # Kimi 自动化预标注脚本
├── standard.md                                 # 数据标注标准规范
├── B站电动车新国标评论数据集标注.csv           # 原始/汇总数据集
└── B站电动车新国标评论数据集标注.xlsx - *.csv  # 经 AI 预处理后分发给各成员的校验文件
🛠️ 工作流 (Workflow)
数据获取: 采集 B 站相关视频评论。

AI 预标注: 运行 kimi_labeling.py，让 Kimi 初步生成标签（支持/反对/中立）。

人工校验: 标注人员打开分配的 .csv 文件，检查 AI 标注结果。

结果准确 -> 直接保留 ✅

结果错误 -> 修正标签 ✏️

数据合并: 汇总所有校验后的数据，生成最终的高质量数据集。

📝 标注标准
请参考 standard.md，其中定义了 AI 和人工需共同遵守的分类准则，特别是针对“阴阳怪气”评论的判定逻辑。
