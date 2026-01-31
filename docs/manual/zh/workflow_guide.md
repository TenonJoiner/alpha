# 工作流编排指南

## 什么是工作流？

工作流是可重复使用的多步骤任务序列，Alpha 可以自动执行。只需创建一次工作流，然后随时运行 - 手动运行、按计划运行或通过事件触发。

## 快速开始

### 列出工作流
```bash
alpha workflow list
```

### 运行工作流
```bash
alpha workflow run "Git Sync and Test"
alpha workflow run "Backup Files" source_dir=/important backup_dir=/backups
```

### 创建工作流
```bash
alpha workflow create
```
按照交互式提示定义您的工作流。

### 查看工作流详情
```bash
alpha workflow show "Git Sync and Test"
```

### 查看执行历史
```bash
alpha workflow history "Backup Files"
```

## 内置模板

Alpha 包含 5 个即用型工作流模板：

1. **Git Sync and Test** - 拉取最新代码并运行测试
2. **Backup Files** - 备份目录并自动清理旧备份
3. **Monitor and Alert** - 检查系统指标（CPU、内存、磁盘）
4. **Deploy Pipeline** - 完整 CI/CD：拉取、测试、构建、部署
5. **Data Processing Pipeline** - 获取、转换、分析、存储数据

## 参数

工作流支持参数化自定义：

```bash
workflow run "Deploy Pipeline" branch=feature/new-ui environment=staging
```

## 调度

设置工作流自动运行：

```bash
workflow schedule "Backup Files" "0 2 * * *"  # 每天凌晨 2 点
```

## 导入/导出

在系统间共享工作流：

```bash
workflow export "My Workflow" --file my-workflow.yaml
workflow import my-workflow.yaml
```

## 工作流结构

工作流包含：
- **步骤 (Steps)**: 有序的操作（工具调用、命令）
- **参数 (Parameters)**: 可自定义的变量
- **触发器 (Triggers)**: 何时执行（手动、计划、基于事件）
- **错误处理 (Error Handling)**: 重试、降级或中止策略
- **输出 (Outputs)**: 工作流执行的结果

## 创建自定义工作流

### 交互式创建
```bash
workflow create --interactive
```

### 从重复任务创建
Alpha 的主动智能可以检测重复的任务模式，并自动建议创建工作流。

### 手动定义
创建包含工作流定义的 YAML 文件并导入：

```yaml
name: "我的自定义工作流"
version: "1.0.0"
description: "工作流描述"
tags: ["自定义", "自动化"]
parameters:
  param_name:
    type: string
    default: "value"
steps:
  - id: step1
    tool: shell
    action: execute
    parameters:
      command: "echo Hello"
```

## 最佳实践

1. **使用描述性名称** - 使用清晰、易记的名称
2. **添加标签** - 使用标签组织工作流，便于搜索
3. **设置适当的错误处理** - 对瞬时故障使用重试，对关键错误使用中止
4. **调度前先测试** - 在设置自动执行之前手动运行工作流
5. **查看执行历史** - 监控工作流性能并排查问题

## 故障排除

### 工作流执行失败
- 检查执行历史：`workflow history <name>`
- 验证参数是否正确
- 查看输出中的错误消息

### 找不到工作流
- 列出所有工作流：`workflow list`
- 按标签搜索：`workflow list --tags deployment`

### 想要修改工作流
- 导出：`workflow export <name>`
- 编辑 YAML 文件
- 导入更新版本：`workflow import <file>`

## 下一步

- 使用 `workflow create` 创建您的第一个工作流
- 使用 `workflow list` 探索内置模板
- 查看[高级工作流功能](workflow_advanced.md)了解复杂场景

---

技术详情请参阅[工作流架构文档](../internal/req_6_2_workflow_orchestration.md)。
