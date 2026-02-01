# Alpha Workflow Automation Examples

Real-world workflow automation examples for Alpha AI Assistant.

---

## 📖 Introduction

Workflows allow you to automate complex multi-step tasks with Alpha. This guide provides ready-to-use examples you can adapt to your needs.

**Workflow Features**:
- 🔄 **Scheduled Execution** - Run workflows on cron schedules
- 📝 **YAML/JSON Format** - Easy to read and modify
- 🔗 **Step Chaining** - Chain multiple tools and actions
- 🎯 **Conditional Logic** - Execute steps based on conditions
- 🔁 **Loops & Iteration** - Process multiple items
- 🧠 **Proactive Suggestions** - Alpha suggests workflows based on patterns

---

## 🌅 Daily Automation Workflows

### 1. Morning Briefing

Get daily news, weather, and tasks summary every morning.

**File**: `workflows/morning-briefing.yaml`

```yaml
workflow:
  name: "morning-briefing"
  description: "Daily morning briefing with news and weather"
  version: "1.0"
  
  trigger:
    type: "schedule"
    cron: "0 8 * * *"  # 8:00 AM daily
  
  steps:
    - name: "greet"
      tool: "llm"
      params:
        prompt: "Generate a cheerful good morning greeting"
    
    - name: "get_news"
      tool: "search"
      params:
        query: "tech news today"
        max_results: 5
    
    - name: "get_weather"
      tool: "search"
      params:
        query: "weather today my location"
    
    - name: "summarize"
      tool: "llm"
      params:
        prompt: |
          Summarize the following information into a brief morning briefing:
          
          News: ${steps.get_news.result}
          Weather: ${steps.get_weather.result}
          
          Format as bullet points, keep it under 200 words.
    
    - name: "save_briefing"
      tool: "file"
      params:
        action: "write"
        path: "briefings/briefing_${date:YYYY-MM-DD}.txt"
        content: "${steps.summarize.result}"
```

**Usage**:
```bash
# Test manually first
You> Run workflow morning-briefing

# It will auto-run at 8 AM daily once saved
```

---

### 2. Evening Cleanup & Backup

Clean temporary files and backup important data every evening.

**File**: `workflows/evening-cleanup.yaml`

```yaml
workflow:
  name: "evening-cleanup"
  description: "Clean temp files and backup important data"
  version: "1.0"
  
  trigger:
    type: "schedule"
    cron: "0 22 * * *"  # 10:00 PM daily
  
  steps:
    - name: "check_disk_space"
      tool: "shell"
      params:
        command: "df -h /"
    
    - name: "clean_temp_files"
      tool: "shell"
      params:
        command: |
          find /tmp -type f -mtime +7 -delete
          find ~/Downloads -type f -mtime +30 -delete
      on_error: "continue"  # Don't fail workflow if cleanup fails
    
    - name: "backup_documents"
      tool: "shell"
      params:
        command: |
          tar -czf ~/backups/docs_$(date +%Y%m%d).tar.gz ~/Documents
      timeout: 300  # 5 minutes max
    
    - name: "verify_backup"
      tool: "shell"
      params:
        command: "ls -lh ~/backups/docs_$(date +%Y%m%d).tar.gz"
    
    - name: "report"
      tool: "llm"
      params:
        prompt: |
          Create a brief cleanup report:
          
          Disk space: ${steps.check_disk_space.result}
          Backup created: ${steps.verify_backup.result}
          
          Status: All tasks completed successfully.
```

---

## 💼 Work Productivity Workflows

### 3. Project Status Report Generator

Generate weekly project status reports from git commits and issues.

**File**: `workflows/weekly-status-report.yaml`

```yaml
workflow:
  name: "weekly-status-report"
  description: "Generate weekly project status report"
  version: "1.0"
  
  trigger:
    type: "schedule"
    cron: "0 17 * * 5"  # 5:00 PM every Friday
  
  variables:
    project_dir: "~/projects/my-project"
    report_dir: "~/reports"
  
  steps:
    - name: "get_git_commits"
      tool: "shell"
      params:
        command: |
          cd ${vars.project_dir}
          git log --since="1 week ago" --oneline --pretty=format:"%h - %s (%an)"
    
    - name: "get_git_stats"
      tool: "shell"
      params:
        command: |
          cd ${vars.project_dir}
          git diff --stat $(git log --since="1 week ago" --format="%H" | tail -1)^ HEAD
    
    - name: "count_tests"
      tool: "shell"
      params:
        command: |
          cd ${vars.project_dir}
          find tests -name "test_*.py" | wc -l
    
    - name: "generate_report"
      tool: "llm"
      params:
        prompt: |
          Generate a professional weekly project status report using this data:
          
          ## Git Commits This Week
          ${steps.get_git_commits.result}
          
          ## Code Changes
          ${steps.get_git_stats.result}
          
          ## Test Coverage
          Total tests: ${steps.count_tests.result}
          
          Format the report with:
          1. Executive Summary
          2. Key Accomplishments
          3. Code Metrics
          4. Next Week's Focus Areas
    
    - name: "save_report"
      tool: "file"
      params:
        action: "write"
        path: "${vars.report_dir}/status_week_${date:YYYY-WW}.md"
        content: |
          # Weekly Status Report - Week ${date:YYYY-WW}
          
          ${steps.generate_report.result}
```

---

### 4. Code Review Preparation

Prepare code review summaries before team meetings.

**File**: `workflows/code-review-prep.yaml`

```yaml
workflow:
  name: "code-review-prep"
  description: "Prepare code review summary for PR"
  version: "1.0"
  
  trigger:
    type: "manual"  # Run on-demand
  
  parameters:
    - name: "pr_number"
      type: "string"
      required: true
      description: "Pull request number"
  
  steps:
    - name: "get_pr_diff"
      tool: "shell"
      params:
        command: |
          gh pr diff ${params.pr_number} > /tmp/pr_${params.pr_number}.diff
    
    - name: "get_pr_info"
      tool: "shell"
      params:
        command: |
          gh pr view ${params.pr_number} --json title,body,author,files
    
    - name: "analyze_changes"
      tool: "llm"
      params:
        prompt: |
          Analyze this pull request and provide a code review summary:
          
          PR Info: ${steps.get_pr_info.result}
          
          Diff: ${steps.get_pr_diff.result}
          
          Provide:
          1. Summary of changes
          2. Files modified (with line counts)
          3. Potential issues or concerns
          4. Testing recommendations
          5. Review checklist
    
    - name: "save_review_notes"
      tool: "file"
      params:
        action: "write"
        path: "reviews/pr_${params.pr_number}_review.md"
        content: "${steps.analyze_changes.result}"
```

**Usage**:
```bash
You> Run workflow code-review-prep with pr_number=123
```

---

## 🔍 Monitoring & Alerts Workflows

### 5. System Health Check

Monitor system resources and send alerts if thresholds exceeded.

**File**: `workflows/system-health-check.yaml`

```yaml
workflow:
  name: "system-health-check"
  description: "Monitor system health metrics"
  version: "1.0"
  
  trigger:
    type: "schedule"
    cron: "*/15 * * * *"  # Every 15 minutes
  
  variables:
    disk_threshold: 90  # Alert if disk >90% full
    memory_threshold: 85  # Alert if memory >85% used
  
  steps:
    - name: "check_disk"
      tool: "shell"
      params:
        command: "df -h / | awk 'NR==2 {print $5}' | sed 's/%//'"
    
    - name: "check_memory"
      tool: "shell"
      params:
        command: "free | awk 'NR==2 {printf \"%.0f\", $3/$2 * 100}'"
    
    - name: "check_cpu"
      tool: "shell"
      params:
        command: "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//'"
    
    - name: "evaluate_health"
      tool: "llm"
      params:
        prompt: |
          System metrics:
          - Disk usage: ${steps.check_disk.result}%
          - Memory usage: ${steps.check_memory.result}%
          - CPU usage: ${steps.check_cpu.result}%
          
          Thresholds:
          - Disk: ${vars.disk_threshold}%
          - Memory: ${vars.memory_threshold}%
          
          Determine if any metrics exceed thresholds and recommend actions.
    
    - name: "alert_if_needed"
      tool: "shell"
      params:
        command: |
          if [ ${steps.check_disk.result} -gt ${vars.disk_threshold} ]; then
            echo "ALERT: Disk usage critical!"
          fi
      condition: "${steps.check_disk.result} > ${vars.disk_threshold}"
```

---

### 6. Website Uptime Monitor

Check if websites are up and responding correctly.

**File**: `workflows/website-uptime-monitor.yaml`

```yaml
workflow:
  name: "website-uptime-monitor"
  description: "Monitor website uptime and response times"
  version: "1.0"
  
  trigger:
    type: "schedule"
    cron: "*/5 * * * *"  # Every 5 minutes
  
  variables:
    websites:
      - url: "https://example.com"
        expected_status: 200
      - url: "https://api.example.com/health"
        expected_status: 200
  
  steps:
    - name: "check_website_1"
      tool: "http"
      params:
        method: "GET"
        url: "${vars.websites[0].url}"
        timeout: 10
    
    - name: "check_website_2"
      tool: "http"
      params:
        method: "GET"
        url: "${vars.websites[1].url}"
        timeout: 10
    
    - name: "analyze_results"
      tool: "llm"
      params:
        prompt: |
          Website monitoring results:
          
          Site 1 (${vars.websites[0].url}):
          Status: ${steps.check_website_1.status}
          Response time: ${steps.check_website_1.duration}ms
          
          Site 2 (${vars.websites[1].url}):
          Status: ${steps.check_website_2.status}
          Response time: ${steps.check_website_2.duration}ms
          
          Report any issues and suggest actions.
    
    - name: "log_status"
      tool: "file"
      params:
        action: "append"
        path: "logs/uptime_${date:YYYY-MM-DD}.log"
        content: |
          [${datetime:ISO}] ${steps.analyze_results.result}
```

---

## 📊 Data Processing Workflows

### 7. Daily Data Pipeline

Process and analyze data files on a schedule.

**File**: `workflows/daily-data-pipeline.yaml`

```yaml
workflow:
  name: "daily-data-pipeline"
  description: "Process and analyze daily data files"
  version: "1.0"
  
  trigger:
    type: "schedule"
    cron: "0 1 * * *"  # 1:00 AM daily
  
  variables:
    input_dir: "data/raw"
    output_dir: "data/processed"
  
  steps:
    - name: "list_new_files"
      tool: "shell"
      params:
        command: |
          find ${vars.input_dir} -name "*.csv" -mtime -1
    
    - name: "process_files"
      tool: "code_execution"
      params:
        language: "python"
        task: |
          Process CSV files:
          1. Load each CSV file
          2. Clean data (remove nulls, duplicates)
          3. Calculate summary statistics
          4. Export to JSON format
          
          Files: ${steps.list_new_files.result}
          Output: ${vars.output_dir}
    
    - name: "generate_report"
      tool: "code_execution"
      params:
        language: "python"
        task: |
          Create data quality report:
          1. Count records processed
          2. List any data issues found
          3. Generate visualizations
          4. Export as HTML report
    
    - name: "archive_raw_files"
      tool: "shell"
      params:
        command: |
          tar -czf ${vars.input_dir}/archive_$(date +%Y%m%d).tar.gz ${vars.input_dir}/*.csv
          rm ${vars.input_dir}/*.csv
```

---

## 🎯 Advanced Workflow Patterns

### 8. Conditional Workflow with Error Handling

**File**: `workflows/conditional-deployment.yaml`

```yaml
workflow:
  name: "conditional-deployment"
  description: "Deploy only if tests pass"
  version: "1.0"
  
  trigger:
    type: "manual"
  
  steps:
    - name: "run_tests"
      tool: "shell"
      params:
        command: "pytest tests/ -v"
      on_error: "stop"  # Stop workflow if tests fail
    
    - name: "check_test_results"
      tool: "shell"
      params:
        command: "echo $?"  # Exit code of previous command
    
    - name: "deploy"
      tool: "shell"
      params:
        command: "./deploy.sh production"
      condition: "${steps.check_test_results.result} == 0"  # Only if tests passed
      on_error: "rollback"
    
    - name: "notify_success"
      tool: "llm"
      params:
        prompt: "Generate deployment success notification"
      condition: "${steps.deploy.status} == 'success'"
    
    - name: "notify_failure"
      tool: "llm"
      params:
        prompt: |
          Generate deployment failure alert with:
          - Test results: ${steps.run_tests.result}
          - Error: ${steps.deploy.error}
      condition: "${steps.deploy.status} == 'failed'"
  
  error_handler:
    - name: "rollback"
      tool: "shell"
      params:
        command: "./rollback.sh"
```

---

### 9. Parallel Execution Workflow

Execute independent tasks in parallel for faster completion.

**File**: `workflows/parallel-checks.yaml`

```yaml
workflow:
  name: "parallel-checks"
  description: "Run multiple checks in parallel"
  version: "1.0"
  
  trigger:
    type: "manual"
  
  parallel_groups:
    - name: "quality_checks"
      parallel: true  # Run steps in this group concurrently
      steps:
        - name: "lint_python"
          tool: "shell"
          params:
            command: "flake8 ."
        
        - name: "lint_javascript"
          tool: "shell"
          params:
            command: "npm run lint"
        
        - name: "type_check"
          tool: "shell"
          params:
            command: "mypy ."
        
        - name: "security_scan"
          tool: "shell"
          params:
            command: "bandit -r ."
    
    - name: "generate_summary"
      parallel: false  # Run sequentially after parallel group
      steps:
        - name: "summarize_results"
          tool: "llm"
          params:
            prompt: |
              Summarize code quality check results:
              
              Linting (Python): ${steps.lint_python.status}
              Linting (JS): ${steps.lint_javascript.status}
              Type Checking: ${steps.type_check.status}
              Security: ${steps.security_scan.status}
```

---

## 🔧 Workflow Best Practices

### 1. Use Variables for Reusability

```yaml
variables:
  environment: "production"
  api_url: "https://api.${vars.environment}.example.com"
  
steps:
  - name: "deploy"
    tool: "shell"
    params:
      command: "deploy --env ${vars.environment} --url ${vars.api_url}"
```

### 2. Add Error Handling

```yaml
steps:
  - name: "critical_step"
    on_error: "stop"  # Stop entire workflow
  
  - name: "optional_step"
    on_error: "continue"  # Continue to next step
  
  - name: "step_with_retry"
    on_error: "retry"
    retry:
      max_attempts: 3
      delay: 5  # seconds
```

### 3. Use Conditions Wisely

```yaml
steps:
  - name: "deploy_to_prod"
    condition: "${env.BRANCH} == 'main' AND ${steps.tests.status} == 'success'"
```

### 4. Log Important Events

```yaml
steps:
  - name: "log_execution"
    tool: "file"
    params:
      action: "append"
      path: "logs/workflow_${workflow.name}_${date:YYYY-MM-DD}.log"
      content: "[${datetime:ISO}] Workflow ${workflow.name} executed successfully"
```

---

## 📚 Next Steps

- **Explore More**: Check [docs/manual/en/workflows.md](docs/manual/en/workflows.md) for full workflow syntax
- **Create Custom Workflows**: Adapt examples to your specific needs
- **Share Workflows**: Contribute useful workflows to community
- **Proactive Learning**: Alpha will suggest workflows based on repeated manual tasks

---

**Version**: v1.0.0
**Last Updated**: 2026-02-02
**Maintainer**: Alpha Development Team
