# 安装热门技能指南

## 📦 使用现有的 npx skills 工具

系统已经集成了 `npx skills` 工具，可以直接从 GitHub 仓库安装技能。

## 🚀 快速开始

### 1. 查看已安装的技能

```bash
npx skills list
```

### 2. 搜索技能

```bash
# 交互式搜索
npx skills find

# 按关键词搜索
npx skills find react
npx skills find pdf
```

### 3. 安装热门技能包

#### 从 Vercel Labs（官方推荐）

```bash
# 安装所有技能
npx skills add vercel-labs/agent-skills --all

# 或者选择性安装特定技能
npx skills add vercel-labs/agent-skills --skill pr-review
npx skills add vercel-labs/agent-skills --skill commit
npx skills add vercel-labs/agent-skills --skill web-design
```

#### 从 Anthropic（Claude 官方）

```bash
npx skills add anthropics/skills --all
```

#### 从其他流行仓库

```bash
# 示例：安装其他GitHub上的技能包
npx skills add <owner/repo> --all
```

## 📋 推荐的热门技能类别

### 开发相关
- `pr-review` - 代码审查
- `commit` - 提交信息生成
- `debug` - 调试助手
- `test` - 测试生成

### 设计相关
- `web-design` - Web设计
- `ui-design` - UI设计
- `frontend-design` - 前端设计

### 文档处理
- `pdf` - PDF处理
- `markdown` - Markdown处理
- `documentation` - 文档生成

### 数据分析
- `data-analysis` - 数据分析
- `visualization` - 数据可视化
- `sql` - SQL查询

## 🎯 一键安装推荐技能

```bash
# 方案1：安装 Vercel Labs 全套技能（推荐）
npx skills add vercel-labs/agent-skills --all -y

# 方案2：安装 Anthropic 官方技能
npx skills add anthropics/skills --all -y

# 方案3：安装特定技能（按需选择）
npx skills add vercel-labs/agent-skills --skill pr-review commit web-design -y
```

## 📂 技能安装位置

- **项目级别**（默认）：`skills/`
- **全局级别**：`~/.alpha/skills/` (使用 `-g` 参数)

**推荐使用项目级别**，这样技能会被 git 跟踪，环境迁移时不会丢失。

## 🔄 技能管理

### 查看已安装技能

```bash
# 项目级别
npx skills list

# 全局级别
npx skills list -g
```

### 更新技能

```bash
# 检查更新
npx skills check

# 更新所有技能
npx skills update
```

### 删除技能

```bash
# 交互式删除
npx skills remove

# 删除特定技能
npx skills remove web-design

# 删除所有技能
npx skills remove --all -y
```

## 💡 在 Alpha 中使用技能

安装技能后，Alpha 会自动：
1. **按需加载**：只在需要时加载相关技能
2. **智能匹配**：根据查询内容自动匹配最合适的技能
3. **上下文增强**：将技能知识注入到 LLM 上下文中

### 查看技能状态

在 Alpha CLI 中输入：
```
skills
```

### 触发技能使用

直接提出任务型请求，系统会自动匹配技能：
```
You: 帮我审查这个 Pull Request
You: 生成一个提交信息
You: 设计一个登录页面
```

## 📖 创建自己的技能

```bash
# 初始化新技能
npx skills init my-custom-skill

# 这会创建 my-custom-skill/SKILL.md 文件
# 编辑文件添加技能描述和指令
```

## 🔗 相关资源

- **Skills 市场**: https://skills.sh/
- **Vercel Labs 技能**: https://github.com/vercel-labs/agent-skills
- **Anthropic 技能**: https://github.com/anthropics/skills
- **技能开发文档**: [docs/manual/zh/skills_guide.md](../docs/manual/zh/skills_guide.md)

## ⚡ 快速示例

```bash
# 1. 查看当前技能
npx skills list

# 2. 安装推荐技能包
npx skills add vercel-labs/agent-skills --all -y

# 3. 启动 Alpha
./start.sh

# 4. 测试技能
> 帮我生成一个提交信息
> 审查我的代码
```

---

**注意**：技能会安装到 `skills/` 目录，该目录已从 `.gitignore` 中移除，会被 git 跟踪，确保环境迁移时技能不会丢失。
