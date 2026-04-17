# Solon AI - Git 工作流规范

> 本文档是团队 Git 协作的唯一标准，所有成员必须严格遵守。

---

## 一、分支结构

```
main（生产分支）
  │
  └── develop（开发主分支）
        │
        ├── feature/模块名-功能名    （功能开发）
        ├── fix/模块名-bug描述       （Bug修复）
        ├── hotfix/紧急问题描述      （生产紧急修复）
        └── refactor/模块名-内容     （重构）

  release/v1.0.0（发布分支，从 develop 拉取）
```

### 分支说明

| 分支 | 用途 | 谁可以合并 | 保护规则 |
|------|------|-----------|---------|
| `main` | 生产环境，只放稳定版本 | **仅 goodperson** | PR + 审核 + CI通过 |
| `develop` | 开发主分支，所有功能汇总 | **对应组长审核后合并** | PR + 审核 + CI通过 |
| `feature/*` | 功能开发 | 开发者自己管理 | 无保护 |
| `fix/*` | Bug修复 | 开发者自己管理 | 无保护 |
| `hotfix/*` | 生产紧急修复 | **仅 goodperson** | 无保护 |
| `release/*` | 版本发布 | **仅 goodperson** | 无保护 |

---

## 二、分支命名规范

### 格式

```
类型/模块名-功能描述
```

### 示例

```bash
# ✅ 正确
feature/wallet-connect          # 钱包连接功能
feature/ai-intent-agent         # AI意图理解Agent
feature/blockchain-jupiter-swap # Jupiter交易集成
fix/dashboard-asset-display     # 修复Dashboard资产显示
refactor/api-error-handling     # 重构API错误处理

# ❌ 错误
feature/test                    # 太模糊
my-branch                       # 没有类型前缀
feature/修改了一些东西           # 不要用中文
Feature/wallet                  # 类型要小写
```

### 模块名对照表

| 模块名 | 对应目录 | 说明 |
|--------|---------|------|
| `wallet` | apps/web, apps/api | 钱包接入相关 |
| `dashboard` | apps/web | 资产总览/诊断页面 |
| `strategy` | apps/web, apps/api | 策略生成/执行 |
| `risk` | apps/web, apps/api | 风控审计 |
| `chat` | apps/web, apps/api | AI对话 |
| `ai` | services/ai-agents | AI智能体 |
| `blockchain` | services/blockchain | 区块链交互 |
| `api` | apps/api | 后端API通用 |
| `web` | apps/web | 前端通用 |
| `infra` | .github, docker | 基础设施 |

---

## 三、日常开发流程

### 1. 开始开发新功能

```bash
# 1. 切换到 develop 并拉取最新代码
git checkout develop
git pull origin develop

# 2. 创建功能分支
git checkout -b feature/ai-intent-agent

# 3. 开发...写代码...

# 4. 提交代码（可以多次提交）
git add .
git commit -m "feat(ai): 实现意图理解Agent基础框架"

# 5. 推送到远程
git push origin feature/ai-intent-agent

# 6. 去 GitHub 创建 Pull Request（见第五节）
```

### 2. 开发过程中同步 develop 最新代码

```bash
# 当 develop 有其他人的新代码合并时，需要同步
git checkout develop
git pull origin develop
git checkout feature/ai-intent-agent
git merge develop

# 如果有冲突，解决冲突后：
git add .
git commit -m "merge: 合并develop最新代码"
```

### 3. 修复 Bug

```bash
git checkout develop
git pull origin develop
git checkout -b fix/dashboard-asset-display
# 修复...
git add .
git commit -m "fix(dashboard): 修复资产列表显示为0的问题"
git push origin fix/dashboard-asset-display
# 去 GitHub 创建 PR
```

### 4. 生产紧急修复（Hotfix）

```bash
# 从 main 拉取
git checkout main
git pull origin main
git checkout -b hotfix/fix-wallet-crash

# 修复...
git add .
git commit -m "hotfix: 修复钱包连接崩溃问题"
git push origin hotfix/fix-wallet-crash

# 创建 PR → 合并到 main
# 然后再创建 PR → 合并到 develop��保持同步）
```

---

## 四、Commit 提交规范

### 格式

```
类型(范围): 描述

[可选] 详细说明

[可选] 关联Issue: #123
```

### 类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(wallet): 实现Phantom钱包连接` |
| `fix` | Bug修复 | `fix(api): 修复资产查询接口超时` |
| `docs` | 文档更新 | `docs: 更新API接口文档` |
| `style` | 代码格式（不影响功能） | `style(web): 统一缩进为2空格` |
| `refactor` | 重构（不是新功能也不是修Bug） | `refactor(ai): 重构Agent基类` |
| `test` | 测试相关 | `test(api): 添加资产查询单元测试` |
| `chore` | 构建/工具/依赖 | `chore: 升级Next.js到14.2` |
| `perf` | 性能优化 | `perf(blockchain): 优化RPC批量请求` |

### 范围对照

| 范围 | 说明 |
|------|------|
| `wallet` | 钱包相关 |
| `dashboard` | 资产总览 |
| `strategy` | 策略相关 |
| `risk` | 风控相关 |
| `chat` | AI对话 |
| `ai` | AI智能体服务 |
| `blockchain` | 区块链服务 |
| `api` | 后端API |
| `web` | 前端通用 |

### 提交示例

```bash
# ✅ 正确
git commit -m "feat(wallet): 实现Phantom钱包连接和断开功能"
git commit -m "fix(api): 修复JWT Token过期未刷新的问题"
git commit -m "docs: 添加AI Agent接口文档"
git commit -m "refactor(ai): 将Agent基类提取到common模块"
git commit -m "chore: 添加eslint规则，禁止unused imports"

# ❌ 错误
git commit -m "更新代码"           # 没有类型，描述太模糊
git commit -m "fix bug"           # 没有范围，描述不清
git commit -m "feat: 改了一些东西"  # 描述无意义
git commit -m "。。。"             # ???
```

### 自动校验

项目已配置 **Commitlint**，不符合规范的提交会被自动拒绝：

```bash
$ git commit -m "更新代码"
⧗   input: 更新代码
✖   subject may not be empty [subject-empty]
✖   type may not be empty [type-empty]
✖   Found 2 problems, 0 warnings

# 提交被拒绝，必须按规范重新写
```

---

## 五、Pull Request 规范

### 创建 PR 的步骤

1. 推送你的分支到远程

```bash
git push origin feature/你的分支名
```

2. 打开 GitHub 仓库页面，点击 **Pull requests** → **New pull request**

3. 设置：
   - **base**: `develop`（合并到哪个分支）
   - **compare**: `feature/你的分支名`（你的分支）

4. 填写 PR 信息（见下方模板）

5. 右侧 **Reviewers** 栏选择你的组长

6. 点击 **Create pull request**

### PR 标题规范

```
类型(范围): 简短描述
```

示例：
```
feat(wallet): 实现Phantom和Solflare钱包连接
fix(api): 修复资产查询接口在无代币时返回500
refactor(ai): 重构IntentAgent，支持多轮对话
```

### PR 描述模板

```markdown
## 改了什么
- 实现了 xxx 功能
- 修复了 xxx 问题

## 怎么测试
- [ ] 步骤1：打开 xxx 页面
- [ ] 步骤2：点击 xxx 按钮
- [ ] 预期结果：xxx

## 截图（如果有UI改动）
贴截图

## 关联
- 关联 Issue: #123
- 依赖 PR: #456
```

### PR 审核规则

| 合并目标 | 审核者 | 最少审核人数 |
|---------|--------|------------|
| `develop` | 对应组长 | 1人 |
| `main` | goodperson | 1人 |

#### 谁审核谁的 PR

| 你的分支改了哪里 | 找谁审核 |
|----------------|---------|
| `services/ai-agents/**` | **kwok**（AI组长） |
| `services/blockchain/**` | **Arha**（区块链组长） |
| `apps/web/**` + `apps/api/**` | **Arha**（区块链/后端组长）或 **kwok** |
| 跨模块改动 | **goodperson** |
| 文档、配置、基础设施 | **goodperson** |

#### 审核标准

审核者需要检查：
- [ ] 代码逻辑是否正确
- [ ] 是否符合代码规范（ESLint/Black通过）
- [ ] 是否有明显的安全问题
- [ ] 命名是否清晰
- [ ] 是否影响其他模块

#### 审核流程

```
提交 PR
  → 自动运行 CI 检查（ESLint、Black、Build）
  → CI 通过后，组长审核代码
  → 审核通过：Approve → 合并
  → 审核不通过：Request Changes → 修改后重新提交
```

---

## 六、代码冲突处理

### 什么时候会冲突

当你和其他人修改了**同一个文件的同一个位置**时，合并就会冲突。

### 如何解决

```bash
# 1. 先拉取 develop 最新代码
git checkout develop
git pull origin develop

# 2. 回到你的分支，合并 develop
git checkout feature/你的分支名
git merge develop

# 3. 如果有冲突，Git 会提示：
# CONFLICT (content): Merge conflict in xxx.tsx

# 4. 打开冲突文件，你会看到：
<<<<<< HEAD
你的代码
=======
别人的代码
>>>>>> develop

# 5. 手动选择保留哪个（或合并两者），删除冲突标记

# 6. 提交
git add .
git commit -m "merge: 解决与develop的合并冲突"
git push origin feature/你的分支名
```

### 避免冲突的建议

1. **频繁同步 develop**：每天开始工作前先 pull develop 合并到自己分支
2. **小步提交**：不要攒太多代码一次性提交
3. **各做各的模块**：按分工表来，不要改别人模块的代码
4. **及时沟通**：如果需要改公共文件，先在群里说一声

---

## 七、Git 常用命令速查

### 每日工作流

```bash
# 早上开始工作
git checkout develop
git pull origin develop
git checkout feature/我的功能
git merge develop

# 写代码...

# 提交
git add .
git commit -m "feat(模块): 做了什么"
git push origin feature/我的功能
```

### 常用命令

```bash
# 查看状态
git status

# 查看所有分支
git branch -a

# 创建并切换分支
git checkout -b feature/新功能

# 切换分支
git checkout develop

# 拉取最新代码
git pull origin develop

# 查看提交历史
git log --oneline -10

# 暂存当前修改（临时切换分支时用）
git stash
git stash pop

# 撤销未提交的修改
git checkout -- 文件名

# 撤销最后一次提交（保留代码）
git reset --soft HEAD~1
```

### 危险命令（⚠️ 谨慎使用）

```bash
# 以下命令会丢失代码，除非你确定要这么做，否则别用！

git reset --hard HEAD~1    # 丢弃最后一次提交和代码
git push --force           # 强制推送（可能覆盖别人代码）
git clean -fd              # 删除所有未跟踪文件
```

---

## 八、版本发布流程

```
1. develop 上所有功能开发完成、测试通过

2. 从 develop 创建 release 分支
   git checkout develop
   git checkout -b release/v1.0.0

3. 在 release 分支上做最后的测试和修复

4. 创建 PR: release/v1.0.0 → main
   goodperson 审核并合并

5. 在 main 上打 Tag
   git tag v1.0.0
   git push origin v1.0.0

6. 把 main 合并回 develop（保持同步）
   git checkout develop
   git merge main
   git push origin develop
```

---

## 九、常见问题

### Q: 我提交时被 Commitlint 拒绝了怎么办？
A: 按照第四节的格式重新写提交信息，例如 `feat(wallet): 实现钱包连接`

### Q: 我提交时被 ESLint 拒绝了怎么办？
A: 运行 `npm run lint:fix` 自动修复，然后重新提交

### Q: 我不小心提交到了 develop 怎么办？
A: 如果还没 push，运行 `git reset --soft HEAD~1` 撤销提交。如果已经 push 了，联系 goodperson 处理

### Q: PR 的 CI 检查失败了怎么办？
A: 点击失败的检查项查看错误详情，在自己分支修复后重新 push，CI 会自动重新运行

### Q: 和别人的代码冲突了怎么办？
A: 按照第六节的步骤解决冲突。如果不确定怎么处理，找对应组长帮忙

### Q: 我可以直接改别人模块的代码吗？
A: 不建议。如果确实需要，先在群里���对方沟通，或者让对方提供接口

---

## 十、Git 环境配置

### 首次 Clone 项目

```bash
# 1. 克隆仓库
git clone https://github.com/goodperson888/SolonAI.git
cd SolonAI

# 2. 安装依赖（会自动配置 Git Hooks）
npm install

# 3. 安装 Python 工具（后端/AI开发者）
pip3 install black isort flake8

# 4. 切换到 develop 分支
git checkout develop

# 5. 创建你的功能分支开始开发
git checkout -b feature/你的功能名
```

### 配置 Git 用户信息

```bash
# 设置你的名字和邮箱（用你的 GitHub 账号信息）
git config user.name "你的名字"
git config user.email "你的邮箱"
```

### 推荐的 VS Code 插件

- **GitLens** - 查看代码提交历史
- **Git Graph** - 可视化分支图
- **ESLint** - 实时代码检查
- **Prettier** - 自动格式化
- **Python** - Python开发支持
