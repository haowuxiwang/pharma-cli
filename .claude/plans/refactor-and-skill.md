# 飞书 Aily Skill 打包计划

## 当前状态

| 项目 | 状态 |
|------|------|
| SKILL.md 格式 | ✅ YAML frontmatter 正确 |
| Git 未提交文件 | ⚠️ 12 个修改 + 33 个新文件 |
| 磁盘整洁度 | ⚠️ 有临时文件需清理 |
| .gitignore | ✅ 已排除 docs/ excel/ |

## 执行计划

### Step 1: 清理临时文件

删除以下文件/目录：
- `test_arima.R`, `test_arima.json`, `test_data.csv`（根目录临时测试文件）
- `__pycache__/`（3 个目录）
- `.coverage`, `htmlcov/`, `.pytest_cache/`
- `pharma_cli.egg-info/`, `output/`

### Step 2: 提交所有更改

```bash
git add -A
git commit -m "feat: complete CLI refactoring and skill integration

- 26 commands fully implemented
- Real data testing with 6 Excel files
- SKILL.md with decision trees and workflows
- 171 tests, 60% coverage
- Dirty data handling (NaN, Inf, encoding, multi-sheet)"
```

### Step 3: 打包 Skill 文件

打包结构：
```
stats-cli.skill (zip)
├── SKILL.md              # 根目录，包含 YAML frontmatter
├── README.md
├── LICENSE
├── setup.py
├── requirements-test.txt
├── cli/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py
│   ├── r_engine.py
│   ├── data_cleaner.py
│   ├── validators.py
│   ├── charts.py
│   ├── reports.py
│   └── commands/
│       ├── __init__.py
│       ├── utils.py
│       ├── descriptive.py
│       ├── ... (26 个命令)
│       └── explore.py
└── r_scripts/
    ├── descriptive.R
    ├── ... (23 个 R 脚本)
    └── timeseries.R
```

排除项：
- `docs/`, `excel/`（测试产物）
- `__pycache__/`, `.git/`, `.coverage`, `htmlcov/`
- `tests/`（测试代码不需要分发）
- `.claude/`（Claude 配置）
- 临时文件

打包命令：
```bash
cd D:\learn\claudecode\pharma-cli
zip -r stats-cli.skill \
  SKILL.md \
  README.md \
  LICENSE \
  setup.py \
  requirements-test.txt \
  cli/ \
  r_scripts/ \
  -x "*.pyc" -x "__pycache__/*" -x ".git/*"
```

注意：SKILL.md 需要复制到根目录
