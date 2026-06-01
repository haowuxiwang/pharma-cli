# stats-cli 快速开始指南

## 一分钟安装

```bash
# 1. 安装 stats-cli
cd D:/learn/claudecode/stats-cli
pip install -e .

# 2. 安装 SKILL.md（让 Claude Code 自动发现）
bash install-skill.sh

# 3. 验证安装
stats-cli --version
```

---

## 常用命令速查

### 描述性统计
```bash
stats-cli descriptive -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4
stats-cli descriptive -f data.csv -c "Column1"
```

### 正态性检验
```bash
stats-cli normality -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4
stats-cli normality -f data.csv -c "measurement"
```

### 过程能力分析
```bash
stats-cli capability -v 10.2 -v 10.5 -v 10.1 --usl 11.0 --lsl 9.0
stats-cli capability -f data.csv -c "measurement" --usl 11.0 --lsl 9.0
```

### 控制图
```bash
stats-cli control-chart imr -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4
stats-cli control-chart xbar -f data.csv -c "measurement" --subgroup-size 5
```

### t 检验
```bash
stats-cli ttest one_sample -v 10.2 -v 10.5 -v 10.1 --mu 10.0
stats-cli ttest two_sample -v 10.2 -v 10.5 -v2 11.3 -v2 11.5
stats-cli ttest paired -v 10.2 -v 10.5 -v2 10.8 -v2 10.9
```

### ANOVA
```bash
stats-cli anova one_way -g '[10.2,10.5,10.1]' -g '[11.3,11.5,11.1]'
```

### 回归分析
```bash
stats-cli regression --x 1 --x 2 --x 3 --y 2 --y 4 --y 6 --type linear
```

### 相关分析
```bash
stats-cli correlation --x 1 --x 2 --x 3 --y 2 --y 4 --y 6 --method pearson
```

### 异常值检测
```bash
stats-cli outlier -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 15.0 --method grubbs
```

### 趋势分析
```bash
stats-cli trend -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4 --test-type cusum --target 10.3
```

### 实验设计
```bash
stats-cli doe full_factorial -f '{"name":"Temp","levels":3}' -f '{"name":"Time","levels":2}'
```

---

## 图表生成

在任何命令前加 `--plot` 即可生成图表：

```bash
# 控制图
stats-cli --plot control-chart imr -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4

# 正态性检验图
stats-cli --plot normality -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4

# 过程能力图
stats-cli --plot capability -v 10.2 -v 10.5 -v 10.1 --usl 11.0 --lsl 9.0
```

图表以 base64 PNG 格式返回，可在 JSON 输出的 `plot` 字段中找到。

---

## 在 Claude Code 中使用

### 自动触发

只需用自然语言描述需求，Claude Code 会自动调用 stats-cli：

```
用户：帮我分析这个 CSV 文件的过程能力
Claude Code：[自动调用 stats-cli capability -f data.csv --usl 11.0 --lsl 9.0]
```

**触发关键词**：
- 统计分析
- 控制图
- 过程能力
- t 检验
- ANOVA
- 回归分析
- DOE
- 正态性检验
- 异常值检测
- 趋势分析

### 手动调用

```bash
# 在 Claude Code 终端中
stats-cli descriptive -v 10.2 -v 10.5 -v 10.1
```

---

## 文件输入格式

### CSV 文件
```csv
measurement
10.2
10.5
10.1
10.3
10.4
```

使用：`stats-cli descriptive -f data.csv -c "measurement"`

### TXT 文件
```
10.2
10.5
10.1
10.3
10.4
```

使用：`stats-cli descriptive -f data.txt`

### JSON 文件
```json
{"values": [10.2, 10.5, 10.1, 10.3, 10.4]}
```

使用：`stats-cli descriptive -f data.json`

---

## 常见问题

### R 未找到
```bash
# 设置环境变量
export RSCRIPT_PATH="D:\R-4.6.0\bin\Rscript.exe"
```

### R 包未安装
```r
# 在 R 中运行
install.packages(c("jsonlite", "qcc", "nortest", "car", "MASS", "base64enc"), 
                 repos="https://cloud.r-project.org")
```

### SKILL.md 未加载
```bash
# 检查文件位置
ls -la ~/.claude/skills/data-analysis/stats-cli/SKILL.md

# 重新安装
bash install-skill.sh
```

---

## 测试结果

- **测试用例**：95 个
- **通过率**：100%
- **代码覆盖率**：88%
- **测试时间**：11.50 秒

运行测试：
```bash
cd D:/learn/claudecode/stats-cli
python -m pytest tests/ -v
```

---

## 更多信息

- [README.md](README.md) - 完整文档
- [TEST_REPORT.md](TEST_REPORT.md) - 测试报告
- [CLAUDE_CODE_INTEGRATION.md](CLAUDE_CODE_INTEGRATION.md) - Claude Code 集成指南

---

**版本**: 0.2.0
**最后更新**: 2026-06-01
