# Workflow Orchestration Guide

## What are Workflows?

Workflows are reusable, multi-step task sequences that Alpha can execute automatically. Create a workflow once and run it whenever needed - manually, on a schedule, or triggered by events.

## Quick Start

### List Workflows
```bash
alpha workflow list
```

### Run a Workflow
```bash
alpha workflow run "Git Sync and Test"
alpha workflow run "Backup Files" source_dir=/important backup_dir=/backups
```

### Create a Workflow
```bash
alpha workflow create
```
Follow the interactive prompts to define your workflow.

### View Workflow Details
```bash
alpha workflow show "Git Sync and Test"
```

### Check Execution History
```bash
alpha workflow history "Backup Files"
```

## Built-in Templates

Alpha includes 5 ready-to-use workflow templates:

1. **Git Sync and Test** - Pull latest code and run tests
2. **Backup Files** - Backup directories with automatic cleanup
3. **Monitor and Alert** - Check system metrics (CPU, memory, disk)
4. **Deploy Pipeline** - Complete CI/CD: pull, test, build, deploy
5. **Data Processing Pipeline** - Fetch, transform, analyze, store data

## Parameters

Workflows support parameters for customization:

```bash
workflow run "Deploy Pipeline" branch=feature/new-ui environment=staging
```

## Scheduling

Schedule workflows to run automatically:

```bash
workflow schedule "Backup Files" "0 2 * * *"  # Daily at 2 AM
```

## Import/Export

Share workflows between systems:

```bash
workflow export "My Workflow" --file my-workflow.yaml
workflow import my-workflow.yaml
```

## Workflow Structure

Workflows consist of:
- **Steps**: Ordered actions (tool calls, commands)
- **Parameters**: Customizable variables
- **Triggers**: When to execute (manual, scheduled, event-based)
- **Error Handling**: Retry, fallback, or abort strategies
- **Outputs**: Results from workflow execution

## Creating Custom Workflows

### Interactive Creation
```bash
workflow create --interactive
```

### From Repeated Tasks
Alpha's proactive intelligence can detect repeated task patterns and suggest creating workflows automatically.

### Manual Definition
Create a YAML file with your workflow definition and import it:

```yaml
name: "My Custom Workflow"
version: "1.0.0"
description: "Workflow description"
tags: ["custom", "automation"]
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

## Best Practices

1. **Name workflows descriptively** - Use clear, memorable names
2. **Add tags** - Organize workflows with tags for easy searching
3. **Set appropriate error handling** - Use retry for transient failures, abort for critical errors
4. **Test before scheduling** - Run workflows manually before setting up automatic execution
5. **Review execution history** - Monitor workflow performance and troubleshoot issues

## Troubleshooting

### Workflow fails to execute
- Check execution history: `workflow history <name>`
- Verify parameters are correct
- Review error messages in the output

### Cannot find workflow
- List all workflows: `workflow list`
- Search by tags: `workflow list --tags deployment`

### Want to modify a workflow
- Export it: `workflow export <name>`
- Edit the YAML file
- Import updated version: `workflow import <file>`

## Next Steps

- Create your first workflow with `workflow create`
- Explore built-in templates with `workflow list`
- Check out [Advanced Workflow Features](workflow_advanced.md) for complex scenarios

---

For technical details, see the [Workflow Architecture Documentation](../internal/req_6_2_workflow_orchestration.md).
