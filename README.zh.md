# Alpha：由AI自己定义并实现的 AI 助手
通过 `cat make_alpha.md | claude --dangerously-skip-permissions` 命令构建

[English](README.md) | 简体中文

一个全天候运行的个人超级AI助手,帮助您完成各种任务。

## Alpha是什么?

Alpha是由先进AI模型驱动的智能个人助手。它可以:

- 💬 **自然对话** - 与您聊天并帮助处理日常任务
- 🔧 **执行任务** - 运行shell命令、管理文件、发送HTTP请求
- 📅 **定时任务** - 使用类似cron的方式设置自动化任务
- 🧮 **计算转换** - 解决数学问题和单位转换
- 🌐 **搜索网络** - 在线查找信息
- ⏰ **处理时间** - 处理日期、时间和时区
- 🤖 **多AI支持** - 可选择DeepSeek、Claude或GPT-4
- 🧠 **智能模型选择** - 自动任务分析和最优模型路由
- 🎯 **动态技能** - 通过可自动安装的技能扩展能力
- ⚡ **内置技能** - 3个预装技能即开即用(文本、JSON、数据处理)

## 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/alpha.git
cd alpha

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows系统: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 创建数据目录
mkdir -p data
```

### 2. 配置API密钥

选择一个AI提供商(推荐使用DeepSeek,性价比最高):

```bash
# 选项1: DeepSeek (推荐 - 性价比最高)
export DEEPSEEK_API_KEY="你的deepseek密钥"

# 选项2: Anthropic Claude
export ANTHROPIC_API_KEY="你的anthropic密钥"

# 选项3: OpenAI GPT
export OPENAI_API_KEY="你的openai密钥"
```

**获取API密钥:**
- DeepSeek: https://platform.deepseek.com/api_keys
- Anthropic: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/api-keys

### 3. 启动Alpha

```bash
# 快速启动
./start.sh

# 或手动启动
python -m alpha.interface.cli
```

## 使用示例

### 基本对话

```
You> 北京今天天气怎么样?
Alpha> 我来帮您查询北京今天的天气。
[显示天气信息]

You> 计算2500的15%是多少
Alpha> 结果是: 375.0

You> 这个目录里有什么文件?
Alpha> [列出当前目录的所有文件]
```

### 可用命令

与Alpha对话时,可以使用这些命令:

- `help` - 显示可用命令
- `status` - 查看Alpha的系统状态
- `clear` - 清除对话历史
- `exit` 或 `quit` - 退出Alpha

## AI提供商对比

Alpha支持三种AI提供商。根据您的需求选择:

| 特性 | DeepSeek | Claude | GPT-4 |
|------|----------|--------|-------|
| **成本** | 🏆 最优 | 良好 | 昂贵 |
| **速度** | 非常快 | 快 | 中等 |
| **中文支持** | 优秀 | 良好 | 一般 |
| **代码生成** | 非常好 | 优秀 | 非常好 |
| **推理能力** | 优秀 | 优秀 | 非常好 |
| **最适合** | 日常使用,成本敏感 | 复杂任务,编程 | 通用任务 |

### 价格对比

每百万tokens成本:

| 提供商 | 输入 | 输出 | **总计** |
|--------|------|------|----------|
| **DeepSeek** | $0.14 | $0.28 | **$0.42** 🏆 |
| Claude Sonnet | $3.00 | $15.00 | $18.00 |
| GPT-4 | $5.00 | $15.00 | $20.00 |

💡 **DeepSeek可为您节省40-50倍的API成本!**

### 切换提供商

编辑 `config.yaml`:

```yaml
llm:
  default_provider: "deepseek"  # 改为: anthropic, openai, 或 deepseek
```

## 可用工具

Alpha内置强大的工具:

| 工具 | 功能 | 使用示例 |
|------|------|----------|
| **Shell** | 执行终端命令 | `ls`, `git status`, `npm install` |
| **File** | 读写管理文件 | 创建、编辑、删除文件 |
| **HTTP** | 发送网络请求 | 调用API、下载内容 |
| **Search** | 搜索网络 | 在线查找信息 |
| **DateTime** | 处理日期时间 | 转换时区、计算时长 |
| **Calculator** | 数学和单位转换 | `sqrt(144)`, 10公里转英里 |

## 定时任务

让Alpha自动执行任务:

```
You> 安排一个任务,每天早上9点检查我的邮件
Alpha> 我会为您设置定时任务...
[创建cron计划: 0 9 * * *]
```

调度格式:
- **Cron表达式**: `0 9 * * *` (每天早上9点)
- **间隔**: 每30分钟、每2小时
- **一次性**: 指定的日期和时间

## 版本发布记录

### v0.4.0 (当前版本) - 智能多模型选择
**发布日期**: 2026-01-29

**新功能:**
- ✨ **智能模型选择** - 自动任务分析和最优模型路由
  - 支持deepseek-chat、deepseek-coder、deepseek-reasoner
  - 任务难度分析(简单、中等、复杂、专家级)
  - 基于任务特征自动匹配模型
  - 成本和性能优化
- 📊 **任务分析器** - 高级任务特征检测
  - 编程任务检测
  - 推理需求分析
  - 专家级主题识别
- 🎯 **智能模型路由** - 基于优先级的模型选择
  - deepseek-reasoner用于复杂推理和专家级任务
  - deepseek-coder用于编程任务
  - deepseek-chat用于一般对话

**文档:**
- [多模型选择指南](docs/manual/zh/model_selection.md)
- [模型选择配置](DEEPSEEK_MODELS.md)

### v0.3.1 - 内置技能
**发布日期**: 2026-01-29

**新功能:**
- ✨ **3个预装内置技能** - 即开即用
  - **text-processing** - 20+文本操作(大小写转换、提取邮箱/网址等)
  - **json-processor** - 8种JSON操作(解析、格式化、验证、提取、合并)
  - **data-analyzer** - 17种统计操作(均值、中位数、方差、分组等)
- ⚡ **自动预安装** - 启动时自动加载技能,无需配置
- 📦 **零依赖** - 纯Python实现,可离线工作
- 🔄 **视觉反馈** - 执行期间的加载动画和状态显示

**文档:**
- [内置技能参考](docs/BUILTIN_SKILLS.md)
- 所有操作的完整使用示例

### v0.3.0 - Agent技能系统
**发布日期**: 2026-01-29

**新功能:**
- ✨ **动态技能系统** - 按需扩展Alpha的能力
  - 自动发现和自动安装技能
  - 技能市场集成
  - 版本管理和依赖处理
- 🔍 **技能发现** - 搜索和浏览可用技能
- 📦 **技能管理** - 安装、更新和删除技能
- 🏪 **技能市场** - 访问社区贡献的技能
- 🎨 **CLI集成** - 新增`skills`和`search skill`命令

**架构:**
- AgentSkill基类用于创建自定义技能
- SkillRegistry用于生命周期管理
- SkillMarketplace用于发现
- SkillInstaller用于依赖处理
- SkillExecutor支持自动安装

**文档:**
- [Agent技能文档](docs/AGENT_SKILLS.md)
- [快速开始指南](docs/AGENT_SKILLS_QUICKSTART.md)
- [技能使用指南](docs/manual/zh/skills_guide.md)

### v0.2.0 - 任务调度与增强工具
**发布日期**: 2026-01-29

**新功能:**
- ✨ **任务调度器** - 支持cron表达式、间隔或一次性任务调度
- ✨ **HTTP工具** - 支持完整HTTP方法的API请求(GET, POST, PUT, DELETE)
- ✨ **日期时间工具** - 高级日期时间操作和时区支持
- ✨ **计算器工具** - 安全的数学计算和单位转换(长度、重量、温度、数据)
- 🔍 **增强搜索** - 通过DuckDuckGo API进行真实网络搜索
- 🎨 **更简洁界面** - 工具执行细节从聊天中隐藏(只显示结果)

**改进:**
- 支持多格式参数(JSON和YAML)
- 更好的错误处理和超时机制
- 改进的API配置和回退支持

### v0.1.1 - 多提供商支持
**发布日期**: 2026-01-29

**新功能:**
- ✨ **DeepSeek集成** - 性价比最高的AI提供商(便宜40-50倍)
- ✨ **多提供商系统** - 在DeepSeek、Claude和GPT-4之间轻松切换
- 🔧 **自定义API端点** - 支持自建或代理API

**改进:**
- 环境变量回退机制
- 改进的配置验证
- 更好的API错误提示

### v0.1.0 - 初始版本
**发布日期**: 2026-01-28

**核心功能:**
- 💬 交互式CLI聊天界面
- 🤖 AI驱动的任务执行
- 🔧 基础工具(Shell、File、Search)
- 🧠 对话记忆
- ⚡ 异步任务管理
- 📝 配置系统

## 故障排除

### "找不到模块"错误

确保您在虚拟环境中:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "API密钥未配置"错误

检查API密钥是否已设置:

```bash
# 检查哪些密钥已设置
echo $DEEPSEEK_API_KEY
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# 如果为空,导出您的密钥
export DEEPSEEK_API_KEY="您的密钥"
```

### 测试配置

```bash
# 检查API配置
./check_api_config.sh

# 测试DeepSeek连接
python test_deepseek.py
```

### 数据库错误

```bash
# 如果缺少数据目录,创建它
mkdir -p data

# 检查权限
ls -la data/
```

## 文档

### 用户指南
- [快速开始指南](docs/manual/zh/quickstart.md) - 5分钟上手
- [功能指南](docs/manual/zh/features.md) - 完整功能文档
- [模型选择指南](docs/manual/zh/model_selection.md) - 智能多模型选择
- [技能使用指南](docs/manual/zh/skills_guide.md) - 动态技能系统
- [API设置指南](docs/API_SETUP.md) - 配置AI提供商
- [工具使用指南](docs/TOOL_USAGE_GUIDE.md) - 如何使用各个工具

### 技术文档
- [Agent技能系统](docs/AGENT_SKILLS.md) - 技术文档
- [内置技能参考](docs/BUILTIN_SKILLS.md) - 预装技能
- [多模型选择](DEEPSEEK_MODELS.md) - DeepSeek模型配置

### API提供商指南
- [DeepSeek设置](docs/DEEPSEEK_GUIDE.md) - DeepSeek配置
- [Anthropic设置](docs/manual/zh/anthropic_config.md) - Claude配置

## 常见问题

**Q: 应该选择哪个AI提供商?**
A: 对于大多数用户,推荐使用DeepSeek,因为它性价比高且中文支持优秀。复杂编程任务可以使用Claude。

**Q: 可以在没有网络的情况下使用Alpha吗?**
A: Alpha需要网络连接来与AI提供商通信。部分工具(如计算器和日期时间)可以离线工作。

**Q: 我的数据安全吗?**
A: 所有对话都存储在本地的`data/alpha.db`中。API提供商(DeepSeek、Anthropic、OpenAI)会根据其隐私政策处理您的消息。

**Q: 可以安排重复性任务吗?**
A: 可以!使用cron表达式或基于间隔的调度。例如:"安排这个任务每周一上午10点运行"

**Q: 使用Alpha的成本是多少?**
A: Alpha本身是免费的。您只需支付API使用费用:
- DeepSeek: 每百万tokens约$0.42
- Claude: 每百万tokens约$18
- GPT-4: 每百万tokens约$20

## 获取帮助

- 📖 [文档](docs/)
- 🐛 [报告问题](https://github.com/yourusername/alpha/issues)
- 💬 [讨论区](https://github.com/yourusername/alpha/discussions)

## 许可证

MIT许可证 - 详见[LICENSE](LICENSE)文件

---

**当前版本**: v0.4.0
**状态**: 生产就绪
**默认AI提供商**: DeepSeek(性价比最高)
