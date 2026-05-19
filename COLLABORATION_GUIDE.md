# 团队协作指南

欢迎加入 Group 19 机器学习与金融项目！本指南将帮助你快速上手项目协作。

## 📋 快速开始步骤

### ⭐ **使用 GitHub Codespace（在线开发）**

#### 为什么用 Codespace？

✅ **无需安装** - 无需安装 Git、Python 等软件  
✅ **环境一致** - 所有团队成员环境完全相同，避免"在我电脑上能用"  
✅ **随时随地** - 只要有浏览器，在任何地方开发  
✅ **自动保存** - 代码自动保存到 GitHub，不用担心丢失  
✅ **团队协作** - 快速分享和审查代码  
✅ **学生免费** - Imperial 学生有免费使用额度  

#### 5 步快速开始

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
│   Clone / Download ZIP           │
│                                  │
│ Codespaces  ← 点这里！           │
│   [Create codespace on main]     │
└──────────────────────────────────┘
```

**3️⃣ 等待加载**

稍等片刻（通常 30 秒左右），浏览器会打开一个完整的 VS Code 编辑器！

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

## 🎨 Codespace 界面简介

打开后你会看到这样的界面：

```
┌──────────────────────────────────────┐
│ File    Edit    View   ...           │ ← 菜单栏
├──────┬───────────────────────────────┤
│      │                               │
│ 文件 │  代码编辑区                    │
│ 浏览 │  (点击文件即可编辑)           │
│ 器   │                               │
│      │                               │
├──────┼───────────────────────────────┤
│          终端 (输入命令)              │ ← 在这里运行 git 命令
└──────────────────────────────────────┘
```

---

## 🌳 分支工作流（Git Flow）

### 分支命名规则

```
main              # 主分支（生产环境，只有最稳定的代码）
├── develop       # 开发分支（测试分支）
│   ├── feature/user-authentication    # 新功能
│   ├── bugfix/data-preprocessing      # bug 修复
│   └── docs/update-readme              # 文档更新
```

### 创建功能分支

在 Codespace 底部的终端中运行：

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
# docs/add-examples
```

---

## 📝 代码提交流程（5 步）

### Step 1: 编写代码

在左边的文件浏览器中找到文件，点击打开编辑：

- 例如：双击 `src/preprocessing.py` 打开
- 编辑代码
- Codespace 会自动保存 ✓

### Step 2: 查看修改

在终端中输入：

```bash
git status
```

你会看到修改了哪些文件

### Step 3: 提交更改

```bash
# 添加所有修改的文件
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

### Step 4: 推送代码到 GitHub

```bash
git push origin feature/your-feature-name
```

### Step 5: 验证推送成功

打开 GitHub 仓库，你应该看到你的分支和最新的代码 ✓

---

## 🔄 创建 Pull Request (PR)

### 什么是 PR？

PR (Pull Request) 是让其他人审查你的代码，然后合并到 develop 分支的方式。

### 创建 PR 的步骤

1. **访问仓库**：https://github.com/lzr-cn/Group-19-Machine-Learning-and-Finance

2. **GitHub 会自动提示你**：
   - 你推送代码后，GitHub 首页会出现一个黄色提示框
   - 上面有你的分支名和 "Compare & pull request" 按钮
   - 点击这个按钮 ✓

3. **或者手动创建 PR**：
   - 点击 **"Pull requests"** 标签
   - 点击 **"New pull request"** 按钮
   - 选择：
     - **Base branch**: `develop`（目标分支）
     - **Compare branch**: `feature/your-feature-name`（你的分支）
   - 点击 **"Create pull request"**

4. **填写 PR 信息**：

```markdown
## 📝 描述
简要描述你做了什么和为什么做这个改动

示例：
- 添加了股票价格预测模型
- 实现了 Random Forest 算法
- 包含 10+ 个单元测试

## 🔗 相关 Issue
关闭 #issue-number（如果有的话）

## ✅ 检查清单
- [x] 我的代码遵循项目代码风格
- [x] 我进行了自我审查
- [x] 我添加了必要的测试
- [x] 我更新了相关文档
- [x] 我的更改不会产生新的警告
```

5. **点击 "Create pull request"** ✓

---

## 👥 Code Review 流程

### 作为代码作者（你）

1. **创建 PR 后等待审查**
   - 其他团队成员会审查你的代码
   - 在 PR 下方可以看到评论

2. **如果有反馈**
   - 阅读审查意见
   - 在 Codespace 中修改代码
   - 提交新的更改（会自动出现在 PR 中）

3. **回应反馈**

```bash
# 修改文件后
git add .
git commit -m "refactor: address review comments"
git push origin feature/your-feature-name
# PR 会自动更新！
```

### 作为审查者（审查别人的代码）

1. 在 PR 中查看代码改动
2. 检查代码质量、逻辑、测试
3. 写下你的意见
4. 点击 "Approve" 表示同意，或 "Request changes" 要求修改

---

## 🔀 合并到 develop

当 PR 获批后：

1. **点击 "Merge pull request" 按钮**
2. **选择合并方式**（通常选 "Create a merge commit"）
3. **点击 "Confirm merge"**
4. **分支会自动删除** ✓

之后：

```bash
# 更新你本地的 develop 分支（可选）
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
├── README.md                     # 项目说明
├── CONTRIBUTING.md               # 贡献指南
├── COLLABORATION_GUIDE.md        # 这个文件！
├── requirements.txt              # 依赖列表
├── .gitignore                    # Git 忽略规则
└── .github/
    └── workflows/
        └── ci.yml                # 自动化测试
```

---

## 👨‍💻 常见任务

### 任务 1：添加新功能

**步骤：**

```bash
# 1. 创建功能分支
git checkout -b feature/my-feature

# 2. 在编辑器中添加代码
#    - 打开 src/ 下的文件编辑

# 3. 在 tests/ 中添加对应测试

# 4. 运行测试确保通过
pytest tests/ -v

# 5. 提交和推送
git add .
git commit -m "feat: add my new feature"
git push origin feature/my-feature

# 6. 在 GitHub 创建 PR（等待审查）
```

### 任务 2：修复 Bug

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

### 任务 3：更新文档

```bash
# 1. 创建文档分支
git checkout -b docs/update-readme

# 2. 编辑 .md 文件（用编辑器）

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
# ✅ 好的例子：
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

# ❌ 不好的例子：
def calc_sr(r,rf=0.02):
    e=r-rf
    return np.mean(e)/np.std(e)
```

### 提交信息规范

好的提交信息应该：
- 简洁明了（第一行不超过 50 字）
- 说明做了什么，而不是怎么做

```
# ✅ 好的例子
feat(preprocessing): add stock price normalization
fix(models): resolve overfitting in random forest
docs(readme): update installation steps
test(preprocessing): add unit tests for normalization
refactor(utils): simplify financial metrics calculation

# ❌ 不好的例子
update code
fix bug
changes
modify file
```

---

## 🧪 测试指南

### 为什么要写测试？

- ✅ 确保代码按预期工作
- ✅ 防止后续改动破坏现有功能
- ✅ 让其他人更容易审查代码

### 运行所有测试

在终端中输入：

```bash
pytest tests/ -v
```

**输出示例：**

```
tests/test_preprocessing.py::TestDataPreprocessor::test_handle_missing_values PASSED [ 20%]
tests/test_preprocessing.py::TestDataPreprocessor::test_normalize_data PASSED [ 40%]
...
======================== 5 passed in 0.32s ==========================
```

### 运行特定测试

```bash
pytest tests/test_preprocessing.py::TestDataPreprocessor::test_handle_missing_values -v
```

### 添加新测试

编辑 `tests/test_preprocessing.py`，添加：

```python
def test_my_new_feature(self):
    """Test my new feature."""
    # 设置测试数据
    data = pd.DataFrame({'A': [1, 2, 3]})
    
    # 执行函数
    result = process_data(data)
    
    # 验证结果
    assert result.shape == (3, 1)
    assert not result.isnull().any().any()
```

---

## 📞 常见问题

### Q1: 我应该从哪个分支创建功能分支？
**A:** 从 `develop` 分支创建。`develop` 是所有功能集合的地方。

### Q2: 多久需要推送一次代码？
**A:** 推荐每做完一个小功能就提交一次（频繁小提交比偶尔大提交更好）。

### Q3: PR 一定要等别人审查吗？
**A:** 是的。这样可以：
- 提高代码质量
- 学习别人的想法
- 防止 bug

### Q4: 测试失败了怎么办？
**A:** 
```bash
# 1. 看失败信息
pytest tests/ -v

# 2. 修改你的代码
# 3. 再运行一次测试
pytest tests/ -v

# 4. 修复到通过为止
```

### Q5: 如何同步最新的 develop 分支代码？
在终端中：
```bash
git fetch origin
git rebase origin/develop
```

### Q6: 我不小心在 main 分支上修改了代码，怎么办？
```bash
# 1. 创建备份分支
git branch backup

# 2. 重置 main 到远程版本
git reset --hard origin/main

# 3. 从备份中恢复你的改动
# 问项目管理员帮忙
```

### Q7: Codespace 会自动关闭吗？
**A:** 是的，30 分钟不操作会自动关闭。但你的代码已经保存到 GitHub 了，再次打开仓库可以继续编辑。

### Q8: 如何重新打开之前的 Codespace？
在仓库页面，点 **Code** → **Codespaces** → 选择你之前的 Codespace

---

## 🎯 团队协作最佳实践

✅ **推荐做法：**
- ✓ 每个功能创建独立分支
- ✓ 经常提交（每做完一小块功能就提交）
- ✓ 写清楚的提交信息
- ✓ 创建 PR 前先本地测试
- ✓ 积极参与代码审查
- ✓ 及时响应反馈

❌ **避免做法：**
- ✗ 直接 push 到 `main` 或 `develop`
- ✗ 一次提交大量代码
- ✗ 提交信息含糊不清（如 "update"、"fix"）
- ✗ 忽视失败的测试
- ✗ 合并前没经过代码审查
- ✗ 提交密钥、密码等敏感信息

---

## 📚 有用的资源

- [GitHub Codespace 官方文档](https://docs.github.com/en/codespaces)
- [Git 官方文档](https://git-scm.com/doc)
- [GitHub Flow 指南](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [PEP 8 Python 风格指南](https://www.python.org/dev/peps/pep-0008/)

---

## 🚀 开始协作！

### 对于每个新成员：

1. **访问仓库**：https://github.com/lzr-cn/Group-19-Machine-Learning-and-Finance

2. **创建 Codespace**：Code → Codespaces → Create codespace on main

3. **安装依赖**：
```bash
pip install -r requirements.txt
```

4. **验证环境**：
```bash
pytest tests/ -v
```

5. **阅读项目文档**：README.md

6. **创建功能分支开始开发**：
```bash
git checkout -b feature/your-task
```

7. **编写代码 → 提交 → 创建 PR → 等待审查 → 合并**

### 工作流总结：

```
1. 创建分支
2. 编写代码 + 写测试
3. 本地测试通过
4. 提交和推送
5. 创建 PR
6. 代码审查
7. 修改反馈（如需要）
8. 合并到 develop
9. 继续下一个功能
```

---

**祝你们协作愉快！** 🎉

有任何问题，随时在 GitHub Issues 中提出！
