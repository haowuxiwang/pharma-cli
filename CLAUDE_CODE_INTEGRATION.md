# Claude Code 集成指南

本指南说明如何在 Claude Code 中加载和使用 pharma-cli。

---

## 一、安装 pharma-cli

### 方式 1：从源码安装（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/pharma-cli.git
cd pharma-cli

# 2. 安装 Python 包
pip install -e .

# 3. 验证安装
pharma-cli --version
```

### 方式 2：从 PyPI 安装（如果已发布）

```bash
pip install pharma-cli
```

---

## 二、安装 SKILL.md

SKILL.md 让 Claude Code 能自动发现和使用 pharma-cli。

### 方式 1：使用安装脚本（推荐）

```bash
cd D:/learn/claudecode/pharma-cli
bash install-skill.sh
```

**输出**：
```
Installing pharma-cli SKILL.md...
SKILL.md installed to: C:\Users\YourName\.claude\skills\data-analysis\pharma-cli

To use pharma-cli with Claude Code:
1. Install pharma-cli: pip install -e .
2. Open Claude Code in any project
3. Ask for statistical analysis (e.g., '帮我做统计分析')

Done!
```

### 方式 2：手动安装

```bash
# 1. 创建目录
mkdir -p ~/.claude/skills/data-analysis/pharma-cli

# 2. 复制 SKILL.md
cp skills/pharma-cli/SKILL.md ~/.claude/skills/data-analysis/pharma-cli/

# 3. 验证安装
ls -la ~/.claude/skills/data-analysis/pharma-cli/
# 应该看到：SKILL.md
```

### 方式 3：Windows 手动安装

```powershell
# 1. 创建目录
mkdir "$env:USERPROFILE\.claude\skills\data-analysis\pharma-cli" -Force

# 2. 复制 SKILL.md
Copy-Item "skills\pharma-cli\SKILL.md" "$env:USERPROFILE\.claude\skills\data-analysis\pharma-cli\"

# 3. 验证安装
ls "$env:USERPROFILE\.claude\skills\data-analysis\pharma-cli\"
```

---

## 三、验证安装

### 3.1 验证 CLI 安装

```bash
# 检查版本
pharma-cli --version
# 输出：pharma-cli, version 0.2.0

# 测试基本功能
pharma-cli descriptive -v 10.2 -v 10.5 -v 10.1
```

### 3.2 验证 SKILL.md 安装

```bash
# 检查文件是否存在
ls -la ~/.claude/skills/data-analysis/pharma-cli/SKILL.md

# 查看文件内容
cat ~/.claude/skills/data-analysis/pharma-cli/SKILL.md
```

---

## 四、在 Claude Code 中使用

### 4.1 自动触发（推荐）

Claude Code 会根据你的问题自动加载 pharma-cli 技能。只需用自然语言描述你的需求：

**示例对话**：

```
用户：帮我分析这个 CSV 文件的过程能力

Claude Code：
1. 自动发现 pharma-cli 技能
2. 加载 SKILL.md 内容
3. 调用 pharma-cli capability -f data.csv --usl 11.0 --lsl 9.0
4. 解析 JSON 结果
5. 用自然语言解释分析结果
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

### 4.2 手动调用 CLI

如果不想用 SKILL.md，也可以直接在 Claude Code 中调用 CLI：

```bash
# 在 Claude Code 终端中运行
pharma-cli descriptive -v 10.2 -v 10.5 -v 10.1

# 或者使用 python -m
python -m cli descriptive -v 10.2 -v 10.5 -v 10.1
```

### 4.3 使用图表生成

```bash
# 生成控制图
pharma-cli --plot control-chart imr -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4

# 生成正态性检验图
pharma-cli --plot normality -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4

# 生成过程能力图
pharma-cli --plot capability -v 10.2 -v 10.5 -v 10.1 --usl 11.0 --lsl 9.0
```

---

## 五、使用场景示例

### 5.1 数据质量检查

**用户问题**：
```
帮我检查这个数据集的质量，看看有没有异常值
```

**Claude Code 会自动**：
1. 调用 `pharma-cli descriptive` 获取描述性统计
2. 调用 `pharma-cli normality` 检查正态性
3. 调用 `pharma-cli outlier` 检测异常值
4. 综合分析结果，给出建议

### 5.2 过程能力研究

**用户问题**：
```
分析这批产品的过程能力，规格限是 USL=11.0, LSL=9.0
```

**Claude Code 会自动**：
1. 调用 `pharma-cli descriptive` 获取基本统计
2. 调用 `pharma-cli normality` 验证正态性假设
3. 调用 `pharma-cli capability --usl 11.0 --lsl 9.0` 计算能力指数
4. 解释 Cp, Cpk 含义，给出改进建议

### 5.3 SPC 监控

**用户问题**：
```
画一个 I-MR 控制图，看看过程是否稳定
```

**Claude Code 会自动**：
1. 调用 `pharma-cli --plot control-chart imr -f data.csv`
2. 生成控制图（base64 PNG）
3. 解析 Western Electric 规则违反情况
4. 评估过程稳定性

### 5.4 假设检验

**用户问题**：
```
比较两组数据是否有显著差异
```

**Claude Code 会自动**：
1. 询问是独立样本还是配对样本
2. 调用 `pharma-cli ttest two_sample` 或 `pharma-cli ttest paired`
3. 解释 t 统计量和 p 值
4. 给出统计结论

---

## 六、高级用法

### 6.1 文件输入

```bash
# 从 CSV 文件读取
pharma-cli descriptive -f data.csv -c "Column1"

# 从 TXT 文件读取（每行一个值）
pharma-cli normality -f data.txt

# 从 JSON 文件读取
pharma-cli capability -f data.json --usl 11.0 --lsl 9.0
```

### 6.2 批量分析

```bash
# 分析多个数据集
for file in data*.csv; do
    echo "Analyzing $file..."
    pharma-cli descriptive -f "$file" -c "measurement"
done
```

### 6.3 生成报告

```bash
# 生成完整的分析报告
pharma-cli descriptive -f data.csv -c "measurement" > report.json
pharma-cli normality -f data.csv -c "measurement" >> report.json
pharma-cli capability -f data.csv -c "measurement" --usl 11.0 --lsl 9.0 >> report.json
```

---

## 七、故障排除

### 7.1 R 未找到

**错误**：
```
RuntimeError: Rscript not found. Install R or set RSCRIPT_PATH environment variable.
```

**解决方案**：
```bash
# 方式 1：设置环境变量
export RSCRIPT_PATH="D:\R-4.6.0\bin\Rscript.exe"

# 方式 2：添加 R 到 PATH
# Windows: 系统属性 → 环境变量 → Path → 添加 R 的 bin 目录
```

### 7.2 R 包未安装

**错误**：
```
Error in library(jsonlite) : there is no package called 'jsonlite'
```

**解决方案**：
```r
# 在 R 中运行
install.packages(c("jsonlite", "qcc", "nortest", "car", "MASS", "base64enc"), 
                 repos="https://cloud.r-project.org")
```

### 7.3 SKILL.md 未加载

**问题**：Claude Code 没有自动加载 pharma-cli 技能

**解决方案**：
1. 检查 SKILL.md 是否在正确位置：
   ```bash
   ls -la ~/.claude/skills/data-analysis/pharma-cli/SKILL.md
   ```

2. 检查文件权限：
   ```bash
   chmod 644 ~/.claude/skills/data-analysis/pharma-cli/SKILL.md
   ```

3. 重启 Claude Code

### 7.4 图表生成失败

**错误**：
```
Error: package 'base64enc' not found
```

**解决方案**：
```r
# 在 R 中运行
install.packages("base64enc", repos="https://cloud.r-project.org")
```

---

## 八、配置选项

### 8.1 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `RSCRIPT_PATH` | R 脚本路径 | 自动检测 |

### 8.2 CLI 选项

| 选项 | 说明 |
|------|------|
| `--version` | 显示版本 |
| `--plot` | 生成图表（base64 PNG） |
| `--help` | 显示帮助 |

---

## 九、示例代码

### 9.1 Python 调用示例

```python
import subprocess
import json

def run_pharma_cli(command, args):
    """运行 pharma-cli 命令"""
    cmd = ['pharma-cli', command] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {result.stderr}")
    return json.loads(result.stdout)

# 示例：描述性统计
data = run_pharma_cli('descriptive', ['-v', '10.2', '-v', '10.5', '-v', '10.1'])
print(f"Mean: {data['mean']}, Std: {data['std']}")

# 示例：过程能力分析
cap = run_pharma_cli('capability', ['-v', '10.2', '-v', '10.5', '-v', '10.1', 
                                     '--usl', '11.0', '--lsl', '9.0'])
print(f"Cpk: {cap['cpk']}, Rating: {cap['rating']}")
```

### 9.2 Shell 脚本示例

```bash
#!/bin/bash
# 批量分析脚本

DATA_DIR="./data"
REPORT_DIR="./reports"

mkdir -p "$REPORT_DIR"

for file in "$DATA_DIR"/*.csv; do
    filename=$(basename "$file" .csv)
    echo "Analyzing $filename..."
    
    # 生成报告
    pharma-cli descriptive -f "$file" -c "measurement" > "$REPORT_DIR/${filename}_desc.json"
    pharma-cli normality -f "$file" -c "measurement" > "$REPORT_DIR/${filename}_norm.json"
    pharma-cli capability -f "$file" -c "measurement" --usl 11.0 --lsl 9.0 > "$REPORT_DIR/${filename}_cap.json"
    
    echo "Reports generated for $filename"
done

echo "All analyses complete!"
```

---

## 十、最佳实践

### 10.1 数据准备

1. **清理数据**：移除空值和异常值
2. **验证格式**：确保 CSV 文件有正确的列名
3. **检查范围**：确保数据在合理范围内

### 10.2 分析流程

1. **先做描述性统计**：了解数据基本特征
2. **检查正态性**：验证统计假设
3. **选择合适的检验方法**：根据数据特性选择
4. **解释结果**：用业务语言解释统计结果

### 10.3 结果解读

1. **不要只看 p 值**：结合效应大小和置信区间
2. **考虑实际意义**：统计显著 ≠ 实际重要
3. **报告完整结果**：包括假设、方法、结论

---

## 十一、参考资源

### 11.1 pharma-cli 文档

- [README.md](README.md) - 项目概述
- [TEST_REPORT.md](TEST_REPORT.md) - 测试报告
- [skills/pharma-cli/SKILL.md](skills/pharma-cli/SKILL.md) - Claude Code 技能定义

### 11.2 统计学资源

- [NIST Handbook](https://www.itl.nist.gov/div898/handbook/) - 统计方法手册
- [SPC Reference](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc31.htm) - SPC 参考

### 11.3 Claude Code 文档

- [Claude Code Skills](https://docs.anthropic.com/claude-code/skills) - 技能系统文档
- [Claude Code MCP](https://docs.anthropic.com/claude-code/mcp) - MCP 集成文档

---

## 十二、支持与反馈

### 12.1 问题报告

如果遇到问题，请提供：
1. 错误信息
2. 输入数据
3. 预期结果
4. 实际结果

### 12.2 功能建议

欢迎提出新功能建议：
1. 新的统计方法
2. 更好的可视化
3. 性能优化
4. 文档改进

---

**文档版本**: 1.0
**最后更新**: 2026-06-01
**维护者**: Claude Code
