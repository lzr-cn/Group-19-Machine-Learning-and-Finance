# 团队协作指南

欢迎加入 Group 19 机器学习与金融项目！本指南将帮助你快速上手项目协作。

## 📋 快速开始步骤

### ⭐ **推荐方式：使用 GitHub Codespace（在线开发）**

#### 优势
✅ 无需安装任何软件  
✅ 所有团队成员环境一致  
✅ 随时随地在浏览器中开发  
✅ 自动保存代码  
✅ 学生免费使用  

#### 步骤

**1️⃣ 打开仓库**

访问：https://github.com/lzr-cn/Group-19-Machine-Learning-and-Finance

**2️⃣ 创建 Codespace**

- 点击绿色的 **"Code"** 按钮
- 选择 **"Codespaces"** 标签
- 点击 **"Create codespace on main"**

```
┌──────────────────────────────────┐
│ Code ▼                           │
├──────────────────────────────────┤
│ Local                            │
│   Clone                          │
│   Download ZIP                   │
│                                  │
│ Codespaces  ← 点这里！           │
│   [Create codespace on main]     │
└──────────────────────────────────┘
```

**3️⃣ 等待加载**

稍等片刻，浏览器会打开一个完整的 VS Code 编辑器！

**4️⃣ 安装依赖**

在底部的终端中输入：

```bash
pip install -r requirements.txt
```

**5️⃣ 验证安装**

```bash
pytest tests/ -v
```

如果所有测试都通过 ✓，恭喜！你已经准备好开发了！

---

## 🖥️ 备选方案：本地开发（需要配置）

如果你想在本地电脑上开发，按照以下步骤：

### 前置要求

安装以下软件（如果还没有）：

1. **Git**：https://git-scm.com
   - Windows 用户：下载 exe 文件，按默认选项安装
   - Mac 用户：运行 `brew install git`

2. **Python 3.8+**：https://www.python.org
   - 下载后按默认选项安装
   - 记得勾选 "Add Python to PATH"

### 本地开发步骤

**1️⃣ 打开终端**

- **Windows**：按 `Win + R`，输入 `cmd`
- **Mac**：按 `Cmd + Space`，输入 `terminal`
- **Linux**：打开你的终端应用

**2️⃣ 克隆仓库**

```bash
git clone https://github.com/lzr-cn/Group-19-Machine-Learning-and-Finance.git
cd Group-19-Machine-Learning-and-Finance
```

**3️⃣ 创建虚拟环境**

```bash
# Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

看到 `(venv)` 前缀说明虚拟环境激活成功

**4️⃣ 安装依赖**

```bash
pip install -r requirements.txt
```

**5️⃣ 验证安装**

```bash
pytest tests/ -v
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

在 Codespace 或本地终端中运行：

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

在编辑器中编辑文件：
- 例如：`src/preprocessing.py`
- Codespace 会自动保存

### Step 2: 查看修改

在终端中输入：

```bash
git status
git diff
```

### Step 3: 提交更改

```bash
# 添加文件到暂存区
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

### Step 4: 推送代码

```bash
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

根据反馈修改代码后：

```bash
git add .
git commit -m "refactor: address review comments"
git push origin feature/your-feature-name
```

PR 会自动更新！

---

## 🔀 合并到 develop

PR 获批后：

1. 点击 **"Squash and merge"** 或 **"Create a merge commit"**
2. 分支会自动删除
3. 本地更新（Codespace 会自动同步）：

```bash
git checkout develop
git pull origin develop
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

**在 Codespace 或本地终端中：**

```bash
# 1. 创建功能分支
git checkout -b feature/my-feature

# 2. 在 src/ 中添加代码（用编辑器编辑文件）

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

# 2. 修改代码（用编辑器）

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

在终端中输入：

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

在 Codespace 或终端中：

```bash
git fetch origin
git rebase origin/develop
```

### Q3: 我提交了但还没 push，可以修改提交吗？
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

### Q6: Codespace 多久会自动关闭？
**A:** 30 分钟不活动会自动关闭。再次访问仓库可以恢复。

### Q7: Codespace 有免费额度吗？
**A:** 是的，GitHub 学生账户有免费额度。超过需要付费。

### Q8: 在 Codespace 中怎么打开编辑器编辑文件？
**A:** 左边有文件浏览器，直接点击文件即可打开编辑。

---

## 🎯 团队协作最佳实践

✅ **DO:**
- ✓ 经常提交小的、有意义的更改
- ✓ 写清楚的 commit 信息
- ✓ 在 push 前运行测试
- ✓ 及时响应 code review 反馈
- ✓ 保持分支最新（定期从 develop rebase）
- ✓ 使用 PR 模板提供清晰的描述
- ✓ 使用 Codespace 保持环境一致

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
- [GitHub Codespace 文档](https://docs.github.com/en/codespaces)

---

## 🚀 开始协作！

### 对于新成员：

1. 访问仓库：https://github.com/lzr-cn/Group-19-Machine-Learning-and-Finance
2. 创建 Codespace（推荐！）或本地克隆
3. 安装依赖：`pip install -r requirements.txt`
4. 运行测试：`pytest tests/ -v`
5. 阅读 README.md 了解项目
6. 等待任务分配
7. 创建功能分支开始开发

### 对于任务管理：

1. 每个团队成员分配一个功能分支
2. 进行开发和提交
3. 创建 PR 并请求审查
4. 合并到 develop
5. 定期合并到 main（发布时）

**祝你们协作愉快！** 🎉
