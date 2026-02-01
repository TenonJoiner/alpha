"""
Tests for WorkflowSuggestionGenerator
"""

import pytest
from datetime import datetime, timedelta
from alpha.workflow.suggestion_generator import (
    WorkflowSuggestion,
    WorkflowSuggestionGenerator
)
from alpha.workflow.pattern_detector import WorkflowPattern


class TestWorkflowSuggestion:
    """Tests for WorkflowSuggestion dataclass"""

    def test_create_suggestion(self):
        """Test creating a WorkflowSuggestion instance"""
        now = datetime.now()
        suggestion = WorkflowSuggestion(
            suggestion_id="sug_001",
            pattern_id="pattern_001",
            suggested_name="Test Workflow",
            description="Test description",
            confidence=0.85,
            priority=4,
            steps=[{"name": "step1", "type": "command"}],
            parameters={"date": {"type": "string"}},
            triggers=["daily"],
            created_at=now,
            status="pending"
        )

        assert suggestion.suggestion_id == "sug_001"
        assert suggestion.priority == 4
        assert suggestion.confidence == 0.85
        assert suggestion.status == "pending"
        assert len(suggestion.steps) == 1

    def test_suggestion_to_dict(self):
        """Test converting suggestion to dictionary"""
        now = datetime.now()
        suggestion = WorkflowSuggestion(
            suggestion_id="sug_002",
            pattern_id="pattern_002",
            suggested_name="Deploy Workflow",
            description="Deploy workflow",
            confidence=0.9,
            priority=5,
            steps=[],
            parameters={},
            triggers=["after git push"],
            created_at=now,
            status="pending"
        )

        result = suggestion.to_dict()
        assert result["suggestion_id"] == "sug_002"
        assert result["priority"] == 5
        assert result["confidence"] == 0.9
        assert "created_at" in result


class TestPriorityCalculation:
    """Tests for priority calculation"""

    def test_priority_5_high_freq_high_conf(self):
        """Test priority 5: high frequency and high confidence"""
        generator = WorkflowSuggestionGenerator()

        pattern = WorkflowPattern(
            pattern_id="p1",
            task_sequence=["task1", "task2"],
            frequency=8,
            confidence=0.9,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            avg_interval=timedelta(days=1),
            task_ids=["t1"],
            suggested_workflow_name="Test"
        )

        priority = generator._calculate_priority(pattern)
        assert priority == 5

    def test_priority_3_medium(self):
        """Test priority 3: medium frequency and confidence"""
        generator = WorkflowSuggestionGenerator()

        pattern = WorkflowPattern(
            pattern_id="p2",
            task_sequence=["task1", "task2"],
            frequency=5,
            confidence=0.75,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            avg_interval=timedelta(days=2),
            task_ids=["t2"],
            suggested_workflow_name="Test"
        )

        priority = generator._calculate_priority(pattern)
        assert priority == 3

    def test_priority_1_low(self):
        """Test priority 1: low frequency or confidence"""
        generator = WorkflowSuggestionGenerator()

        pattern = WorkflowPattern(
            pattern_id="p3",
            task_sequence=["task1"],
            frequency=2,
            confidence=0.6,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            avg_interval=timedelta(days=10),
            task_ids=["t3"],
            suggested_workflow_name="Test"
        )

        priority = generator._calculate_priority(pattern)
        assert priority == 1


class TestDescriptionGeneration:
    """Tests for description generation"""

    def test_generate_description_basic(self):
        """Test generating basic description"""
        generator = WorkflowSuggestionGenerator()

        now = datetime.now()
        pattern = WorkflowPattern(
            pattern_id="p1",
            task_sequence=["task1", "task2", "task3"],
            frequency=5,
            confidence=0.85,
            first_seen=now - timedelta(days=10),
            last_seen=now,
            avg_interval=timedelta(days=2),
            task_ids=["t1"],
            suggested_workflow_name="Test Workflow"
        )

        description = generator._generate_description(pattern)

        assert "3 steps" in description
        assert "5 times" in description
        assert "85%" in description or "0.85" in str(pattern.confidence)

    def test_generate_description_recent(self):
        """Test description for recent pattern"""
        generator = WorkflowSuggestionGenerator()

        now = datetime.now()
        pattern = WorkflowPattern(
            pattern_id="p2",
            task_sequence=["task1", "task2"],
            frequency=3,
            confidence=0.8,
            first_seen=now - timedelta(days=5),
            last_seen=now,
            avg_interval=timedelta(days=1),
            task_ids=["t2"],
            suggested_workflow_name="Recent Workflow"
        )

        description = generator._generate_description(pattern)
        assert "last week" in description or "last month" in description


class TestTriggerDetection:
    """Tests for trigger detection"""

    def test_detect_daily_trigger(self):
        """Test detecting daily temporal trigger"""
        generator = WorkflowSuggestionGenerator()

        pattern = WorkflowPattern(
            pattern_id="p1",
            task_sequence=["backup files"],
            frequency=7,
            confidence=0.9,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            avg_interval=timedelta(days=1),
            task_ids=["t1"],
            suggested_workflow_name="Daily Backup"
        )

        triggers = generator._detect_triggers(pattern)

        assert len(triggers) > 0
        assert any("daily" in t for t in triggers)

    def test_detect_git_trigger(self):
        """Test detecting git-related trigger"""
        generator = WorkflowSuggestionGenerator()

        pattern = WorkflowPattern(
            pattern_id="p2",
            task_sequence=["git pull", "run tests"],
            frequency=5,
            confidence=0.85,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            avg_interval=timedelta(days=2),
            task_ids=["t2"],
            suggested_workflow_name="Git Workflow"
        )

        triggers = generator._detect_triggers(pattern)

        assert len(triggers) > 0
        assert any("git" in t.lower() for t in triggers)

    def test_detect_manual_trigger_default(self):
        """Test default manual trigger when no patterns detected"""
        generator = WorkflowSuggestionGenerator()

        pattern = WorkflowPattern(
            pattern_id="p3",
            task_sequence=["random task"],
            frequency=3,
            confidence=0.7,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            avg_interval=timedelta(days=0),
            task_ids=["t3"],
            suggested_workflow_name="Manual Workflow"
        )

        triggers = generator._detect_triggers(pattern)

        assert len(triggers) > 0
        assert any("manual" in t for t in triggers)


class TestStepGeneration:
    """Tests for workflow step generation"""

    def test_infer_command_step_type(self):
        """Test inferring command step type"""
        generator = WorkflowSuggestionGenerator()

        step_type = generator._infer_step_type("git commit -m 'message'")
        assert step_type == "command"

        step_type = generator._infer_step_type("run tests")
        assert step_type == "command"

    def test_infer_file_operation_step_type(self):
        """Test inferring file operation step type"""
        generator = WorkflowSuggestionGenerator()

        step_type = generator._infer_step_type("backup files")
        assert step_type == "file_operation"

        step_type = generator._infer_step_type("copy data")
        assert step_type == "file_operation"

    def test_infer_generic_step_type(self):
        """Test inferring generic step type"""
        generator = WorkflowSuggestionGenerator()

        step_type = generator._infer_step_type("do something")
        assert step_type == "generic"

    def test_create_step_from_task(self):
        """Test creating workflow step from task"""
        generator = WorkflowSuggestionGenerator()

        step = generator._create_step_from_task("git pull", step_index=0)

        assert step["name"] == "step_1"
        assert step["type"] == "command"
        assert step["description"] == "git pull"
        assert "error_handling" in step


class TestParameterExtraction:
    """Tests for parameter extraction"""

    def test_extract_date_parameter(self):
        """Test extracting date parameter"""
        generator = WorkflowSuggestionGenerator()

        params = generator._extract_parameters_from_task("deploy on DATETOKEN")

        assert "date" in params
        assert params["date"]["type"] == "string"

    def test_extract_path_parameter(self):
        """Test extracting path parameter"""
        generator = WorkflowSuggestionGenerator()

        params = generator._extract_parameters_from_task("backup PATHTOKEN")

        assert "path" in params
        assert params["path"]["format"] == "path"

    def test_extract_multiple_parameters(self):
        """Test extracting multiple parameters"""
        generator = WorkflowSuggestionGenerator()

        params = generator._extract_parameters_from_task(
            "backup PATHTOKEN at TIMETOKEN"
        )

        assert "path" in params
        assert "time" in params

    def test_extract_no_parameters(self):
        """Test extracting no parameters"""
        generator = WorkflowSuggestionGenerator()

        params = generator._extract_parameters_from_task("simple task")

        assert len(params) == 0


class TestWorkflowGeneration:
    """Tests for complete workflow generation"""

    def test_create_workflow_from_pattern(self):
        """Test creating complete workflow from pattern"""
        generator = WorkflowSuggestionGenerator()

        pattern = WorkflowPattern(
            pattern_id="p1",
            task_sequence=["git pull", "run tests", "deploy"],
            frequency=5,
            confidence=0.85,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            avg_interval=timedelta(days=1),
            task_ids=["t1", "t2", "t3"],
            suggested_workflow_name="Deploy Workflow"
        )

        workflow_def = generator.create_workflow_from_pattern(pattern)

        assert workflow_def["name"] == "Deploy Workflow"
        assert len(workflow_def["steps"]) == 3
        assert "parameters" in workflow_def
        assert "metadata" in workflow_def
        assert workflow_def["metadata"]["auto_generated"] is True

    def test_generate_workflow_suggestions(self):
        """Test generating workflow suggestions from patterns"""
        generator = WorkflowSuggestionGenerator()

        patterns = [
            WorkflowPattern(
                pattern_id="p1",
                task_sequence=["task1", "task2"],
                frequency=8,
                confidence=0.9,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                avg_interval=timedelta(days=1),
                task_ids=["t1"],
                suggested_workflow_name="High Priority Workflow"
            ),
            WorkflowPattern(
                pattern_id="p2",
                task_sequence=["task3"],
                frequency=3,
                confidence=0.7,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                avg_interval=timedelta(days=3),
                task_ids=["t2"],
                suggested_workflow_name="Low Priority Workflow"
            )
        ]

        suggestions = generator.generate_workflow_suggestions(patterns, max_suggestions=5)

        assert len(suggestions) == 2
        assert suggestions[0].priority > suggestions[1].priority  # Sorted by priority

    def test_generate_suggestions_empty_patterns(self):
        """Test generating suggestions with empty pattern list"""
        generator = WorkflowSuggestionGenerator()

        suggestions = generator.generate_workflow_suggestions([])

        assert len(suggestions) == 0


class TestEdgeCases:
    """Tests for edge cases"""

    def test_generator_initialization(self):
        """Test initializing generator"""
        generator = WorkflowSuggestionGenerator(
            suggestion_store=None,
            workflow_library=None
        )

        assert generator.suggestion_store is None
        assert generator.workflow_library is None

    def test_detect_opportunities_no_library(self):
        """Test detecting opportunities without workflow library"""
        generator = WorkflowSuggestionGenerator()

        opportunities = generator.detect_workflow_execution_opportunities({})

        assert len(opportunities) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
