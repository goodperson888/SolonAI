# 代码规范与工具配置

## 概述

项目使用自动化工具确保代码质量和一致性。提交代码时会自动运行检查，不符合规范的代码无法提交。

## 1. 前端代码规范

### ESLint
配置文件：`apps/web/.eslintrc.js`

核心规则：
- TypeScript 严格模式
- React Hooks 规则
- 未使用变量报错（`_` 前缀除外）
- `any` 类型警告
- 禁止 `console.log`（`console.warn` 和 `console.error` 除外）

```bash
# 检查
cd apps/web && npm run lint

# 自动修复
cd apps/web && npm run lint:fix
```

### Prettier
配置文件：`apps/web/.prettierrc`

格式规则：
- 无分号
- 单引号
- 100 字符宽度
- 尾随逗号（ES5）
- Tailwind class 自动排序

```bash
# 格式化
cd apps/web && npm run format

# 检查格式
cd apps/web && npm run format:check
```

### TypeScript
配置文件：`apps/web/tsconfig.json`

```bash
# 类型检查
cd apps/web && npm run type-check
```

## 2. Python 代码规范

### Black（格式化）
配置文件：`pyproject.toml`

格式规则：
- 100 字符宽度
- Python 3.11 目标版本

```bash
# 格式化
black apps/api/ services/

# 检查格式
black --check apps/api/ services/
```

### isort（import 排序）
配置文件：`pyproject.toml`

```bash
# 排序
isort apps/api/ services/

# 检查
isort --check-only apps/api/ services/
```

### Flake8（代码检查）
配置文件：`.flake8`

核心规则：
- 100 字符宽度
- 最大复杂度 10
- `__init__.py` 允许未使用的 import

```bash
# 检查
flake8 apps/api/ services/
```

### 安装 Python 开发工具

```bash
pip install -r requirements-dev.txt
```

## 3. Git Hooks

### 工作原理

使用 Husky + lint-staged，在 `git commit` 时自动运行检查：

```
git commit
  ↓
pre-commit hook → lint-staged
  ↓
  ├── 前端文件 (.ts/.tsx) → ESLint --fix → Prettier --write
  ├── 前端文件 (.json/.css/.md) → Prettier --write
  └── Python 文件 (.py) → Black → isort → Flake8
  ↓
commit-msg hook → Commitlint
  ↓
  └── 校验提交信息格式
  ↓
提交成功 ✅ 或 被拒绝 ❌
```

### 首次设置

```bash
# 安装依赖时会自动配置 Husky
npm install
```

如果 hooks 没有生效，手动初始化：

```bash
npx husky init
```

## 4. Commit 提交规范

### 格式

```
<type>(<scope>): <subject>
```

### 类型

| type | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | `feat(wallet): 添加钱包连接功能` |
| fix | Bug修复 | `fix(api): 修复资产查询超时` |
| docs | 文档更新 | `docs: 更新README` |
| style | 代码格式 | `style(web): 格式化代码` |
| refactor | 重构 | `refactor(agent): 重构策略生成逻辑` |
| perf | 性能优化 | `perf(rpc): 优化RPC请求缓存` |
| test | 测试 | `test(api): 添加资产查询测试` |
| chore | 构建/工具 | `chore: 更新依赖版本` |
| revert | 回退 | `revert: 回退钱包连接功能` |
| ci | CI/CD | `ci: 添加前端构建检查` |

### scope（可选）

常用 scope：
- `wallet` - 钱包相关
- `api` - 后端API
- `web` - 前端
- `agent` - AI智能体
- `rpc` - 区块链RPC
- `strategy` - 策略相关
- `risk` - 风控相关

### 错误示例（会被拒绝）

```bash
git commit -m "修复了一个bug"           # 缺少 type
git commit -m "FIX: something"         # type 必须小写
git commit -m "feat:"                  # subject 不能为空
git commit -m "feat(wallet): 这是一个非常非常非常非常非常非常非常非常非常长的提交信息"  # 超过72字符
```

## 5. CI/CD 检查

### GitHub Actions 工作流

每次 Push 或 PR 到 `main`/`develop` 分支时，自动运行以下检查：

| 检查项 | 说明 | 必须通过 |
|--------|------|---------|
| frontend-lint | ESLint + Prettier + TypeScript | ✅ |
| frontend-build | Next.js 构建 | ✅ |
| backend-lint | Black + isort + Flake8 | ✅ |
| commitlint | Commit 信息格式（仅PR） | ✅ |

### GitHub 仓库设置

需要在 GitHub 仓库中配置分支保护规则：

1. Settings → Branches → Add rule
2. 保护 `main` 分支：
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - 选择：`frontend-lint`、`backend-lint`、`commitlint`
   - ✅ Require branches to be up to date before merging
3. 保护 `develop` 分支：
   - ✅ Require status checks to pass before merging
   - 选择：`frontend-lint`、`backend-lint`

## 6. 编辑器配置

### VSCode（推荐）

项目已配置 `.vscode/settings.json` 和 `.vscode/extensions.json`。

推荐插件（打开项目时会自动提示安装）：
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- Python
- Black Formatter
- Flake8

配置效果：
- 保存文件时自动格式化
- 自动运行 ESLint 修复
- Python 文件使用 Black 格式化

### 其他编辑器

项目配置了 `.editorconfig`，支持大多数编辑器的基础格式设置。

## 7. 常见问题

### Q: 提交被拒绝了怎么办？

查看错误信息，通常是以下原因：
1. **ESLint 错误**: 运行 `npm run lint:fix` 自动修复
2. **Prettier 格式**: 运行 `npm run format` 格式化
3. **Black 格式**: 运行 `black .` 格式化
4. **Commit 信息格式**: 按照规范重新编写

### Q: 如何跳过 hooks？（不推荐）

```bash
git commit --no-verify -m "message"
```

注意：CI/CD 仍然会检查，不符合规范的代码无法合并到主分支。

### Q: 新增了 Python 文件但 Flake8 报错？

确保安装了开发依赖：

```bash
pip install -r requirements-dev.txt
```

### Q: VSCode 没有自动格式化？

1. 确认安装了推荐插件
2. 确认 `.vscode/settings.json` 存在
3. 重启 VSCode
