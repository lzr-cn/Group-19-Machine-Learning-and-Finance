# 团队协作指南

欢迎加入 Group 19 机器学习与金融项目！本指南将帮助你快速上手项目协作。

## 📋 快速开始步骤

### 1️⃣ **克隆仓库**

```bash
git clone https://github.com/lzr-cn/Group-19-Machine-Learning-and-Finance.git
cd Group-19-Machine-Learning-and-Finance
```

### 2️⃣ **设置本地环境**

```bash
# 创建虚拟环境（推荐使用 Python 3.8+）
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3️⃣ **验证安装**

```bash
# 运行测试
pytest tests/ -v

# 应该看到所有测试通过 ✓
```

---

## 🌳 分支工作流（Git Flow）

### 分支命名规则

```
main              # 主分支（生产环境）
├── develop       # 开发分支
│   ├── feature/user-authentication    # 新功能
│   ├── bugfix/data-preprocessing      # bug 修复
│   └── docs/update-readme              # 文档更新
```

### 创建功能分支

```bash
# 1. 更新本地 develop 分支
git checkout develop
git pull origin develop

# 2. 创建功能分支（从 develop 分支创建）
git checkout -b feature/your-feature-name

# 示例功能分支名：
# feature/stock-price-prediction
# feature/portfolio-optimization
# feature/risk-analysis
# bugfix/handle-missing-values
```

---

## 📝 代码提交流程

### Step 1: 修改代码

```bash
# 编辑文件...
# 例如：src/preprocessing.py

# 查看修改
git status
git diff
```

### Step 2: 提交更改

```bash
# 添加文件到暂存区
git add src/preprocessing.py

# 或添加所有修改
git add .

# 提交（使用有意义的提交信息）
git commit -m "feat: add stock price normalization function"

# 提交信息格式示例：
# feat: 添加新功能
# fix: 修复 bug
# docs: 更新文档
# refactor: 重构代码
# test: 添加测试
```

### Step 3: 推送代码

```bash
# 推送到远程分支
git push origin feature/your-feature-name
```

---

## 🔄 创建 Pull Request (PR)

### 在 GitHub 上创建 PR

1. 访问仓库：https://github.com/lzr-cn/Group-19-Machine-Learning-and-Finance
2. 点击 **"Pull requests"** 标签
3. 点击 **"New pull request"** 按钮
4. 选择：
   - **Base branch**: `develop`（通常是这个）
   - **Compare branch**: `feature/your-feature-name`
5. 填写 PR 信息：

```markdown
## 📝 描述
简要描述你做了什么和为什么做这个改动

## 🔗 相关 Issue
关闭 #issue-number（如果有的话）

## ✅ 检查清单
- [ ] 我的代码遵循项目代码风格
- [ ] 我进行了自我审查
- [ ] 我添加了必要的测试
- [ ] 我更新了相关文档
- [ ] 我的更改不会产生新的警告

## 📸 截图（如适用）
如有 UI 更改，请添加截图
```

6. 点击 **"Create pull request"**

---

## 👥 Code Review 流程

### 审查者检查清单

- ✅ 代码质量和风格
- ✅ 是否有逻辑错误
- ✅ 测试覆盖率
- ✅ 文档更新
- ✅ 性能考虑

### 回应反馈

```bash
# 根据反馈修改代码
# 提交新的更改
git add .
git commit -m "refactor: address review comments"
git push origin feature/your-feature-name

# PR 会自动更新！
```

---

## 🔀 合并到 develop

PR 获批后：

1. 点击 **"Squash and merge"** 或 **"Create a merge commit"**
2. 分支会自动删除
3. 本地更新：

```bash
# 切换到 develop
git checkout develop

# 拉取最新更改
git pull origin develop

# 删除本地功能分支
git branch -d feature/your-feature-name
```

---

## 📦 项目文件结构说明

```
Group-19-Machine-Learning-and-Finance/
├── src/                          # 源代码
│   ├── __init__.py
│   ├── preprocessing.py          # 数据预处理
│   ├── models.py                 # 机器学习模型
│   └── utils.py                  # 工具函数
│
├── tests/                        # 测试文件
│   ├── __init__.py
│   └── test_preprocessing.py     # 预处理测试
│
├── notebooks/                    # Jupyter 笔记本（分析用）
│   └── example_analysis.ipynb
│
├── data/                         # 数据文件
│   ├── raw/                      # 原始数据
│   └── processed/                # 处理后数据
│
├── results/                      # 结果和输出
│   ├── models/                   # 模型文件
│   └── visualizations/           # 图表
│
├── docs/                         # 文档
├── README.md
├── CONTRIBUTING.md
├── requirements.txt
├── .gitignore
└── .github/
    └── workflows/
        └── ci.yml                # 自动化测试
```

---

## 👨‍💻 常见任务

### 添加新功能

```bash
# 1. 创建功能分支
git checkout -b feature/my-feature

# 2. 在 src/ 中添加代码

# 3. 在 tests/ 中添加对应测试

# 4. 运行测试确保通过
pytest tests/ -v

# 5. 提交和推送
git add .
git commit -m "feat: add my new feature"
git push origin feature/my-feature

# 6. 在 GitHub 创建 PR
```

### 修复 Bug

```bash
# 1. 创建 bugfix 分支
git checkout -b bugfix/bug-name

# 2. 修改代码

# 3. 添加测试验证修复

# 4. 提交和推送
git add .
git commit -m "fix: resolve bug in data processing"
git push origin bugfix/bug-name

# 5. 创建 PR
```

### 更新文档

```bash
# 1. 创建文档分支
git checkout -b docs/update-readme

# 2. 编辑 .md 文件

# 3. 提交和推送
git add .
git commit -m "docs: update installation instructions"
git push origin docs/update-readme

# 5. 创建 PR
```

---

## ✅ 代码规范

### Python 风格指南

遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/)

```python
# 好的例子
def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """
    Calculate Sharpe ratio.
    
    Args:
        returns (np.ndarray): Return series
        risk_free_rate (float): Risk-free rate
    
    Returns:
        float: Sharpe ratio
    """
    excess_returns = returns - risk_free_rate
    return np.mean(excess_returns) / np.std(excess_returns)
```

### 提交信息规范

```
<type>(<scope>): <subject>

<body>

<footer>

示例：
feat(preprocessing): add stock price normalization
fix(models): resolve overfitting in random forest
docs(readme): update installation steps
test(preprocessing): add unit tests for normalization
```

---

## 🧪 测试指南

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行特定测试

```bash
pytest tests/test_preprocessing.py::TestDataPreprocessor::test_handle_missing_values -v
```

### 查看测试覆盖率

```bash
pytest tests/ --cov=src --cov-report=html
# 打开 htmlcov/index.html
```

### 添加新测试

```python
# tests/test_models.py
import pytest
from src.models import FinancialPredictor

class TestFinancialPredictor:
    def test_model_training(self):
        """Test model training."""
        predictor = FinancialPredictor(model_type='linear')
        # 你的测试代码...
        assert True
```

---

## 📞 常见问题

### Q1: 我应该从哪个分支创建功能分支？
**A:** 从 `develop` 分支创建（除非明确指定）。

### Q2: 如何同步最新的 develop 分支？
```bash
git fetch origin
git rebase origin/develop
```

### Q3: 我在功能分支上提交了但还没 push，可以修改提交吗？
```bash
# 修改最后一次提交
git commit --amend

# 强制推送（仅在未 merge 前）
git push origin feature/my-feature --force
```

### Q4: 如何撤销已推送的提交？
```bash
# 创建反向提交
git revert <commit-hash>

# 或重置（谨慎使用！）
git reset --hard <commit-hash>
git push origin branch-name --force
```

### Q5: 如何解决合并冲突？
```bash
# 1. 更新本地分支
git pull origin develop

# 2. 修复冲突文件
# 3. 添加文件
git add .

# 4. 完成合并
git commit -m "Merge develop into feature branch"
git push origin feature/my-feature
```

---

## 🎯 团队协作最佳实践

✅ **DO:**
- ✓ 经常提交小的、有意义的更改
- ✓ 写清楚的 commit 信息
- ✓ 在 push 前运行测试
- ✓ 及时响应 code review 反馈
- ✓ 保持分支最新（定期从 develop rebase）
- ✓ 使用 PR 模板提供清晰的描述

❌ **DON'T:**
- ✗ 直接 push 到 `main` 或 `develop`
- ✗ 提交大的、复杂的更改
- ✗ 忽视失败的测试
- ✗ 合并到 main 之前没有 PR 审查
- ✗ 在共享分支上使用 force push
- ✗ 提交敏感信息（密钥、密码等）

---

## 📚 有用的资源

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub Flow 指南](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [PEP 8 Python 风格指南](https://www.python.org/dev/peps/pep-0008/)

---

## 🚀 开始协作！

1. 每个团队成员克隆仓库
2. 创建自己的功能分支
3. 进行开发和提交
4. 创建 PR 并请求审查
5. 合并到 develop
6. 定期合并到 main（发布时）

**祝你们协作愉快！** 🎉
