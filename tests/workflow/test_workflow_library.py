"""
Unit tests for workflow library module
"""

import pytest
import os
import tempfile
from pathlib import Path

from alpha.workflow.definition import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowParameter,
    ParameterType,
)
from alpha.workflow.library import WorkflowLibrary


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_workflows.db")
        yield db_path


@pytest.fixture
def library(temp_db):
    """Create WorkflowLibrary instance with temp database"""
    return WorkflowLibrary(db_path=temp_db)


@pytest.fixture
def sample_workflow():
    """Create sample workflow for testing"""
    return WorkflowDefinition(
        name="Test Workflow",
        version="1.0.0",
        description="A test workflow",
        author="tester",
        tags=["test", "demo"],
        steps=[
            WorkflowStep(
                id="step1", tool="shell", action="execute", parameters={"command": "echo hello"}
            )
        ],
    )


def test_library_initialization(temp_db):
    """Test library initialization creates database"""
    library = WorkflowLibrary(db_path=temp_db)
    assert Path(temp_db).exists()


def test_save_workflow(library, sample_workflow):
    """Test saving workflow to library"""
    result = library.save(sample_workflow)
    assert result is True


def test_save_invalid_workflow(library):
    """Test saving invalid workflow fails"""
    invalid_workflow = WorkflowDefinition(name="", version="1.0.0", steps=[])

    with pytest.raises(ValueError):
        library.save(invalid_workflow)


def test_get_workflow(library, sample_workflow):
    """Test retrieving workflow by name"""
    library.save(sample_workflow)

    retrieved = library.get("Test Workflow")

    assert retrieved is not None
    assert retrieved.name == "Test Workflow"
    assert retrieved.version == "1.0.0"


def test_get_nonexistent_workflow(library):
    """Test retrieving non-existent workflow returns None"""
    result = library.get("Nonexistent")
    assert result is None


def test_get_workflow_by_id(library, sample_workflow):
    """Test retrieving workflow by ID"""
    library.save(sample_workflow)

    retrieved = library.get_by_id(sample_workflow.id)

    assert retrieved is not None
    assert retrieved.id == sample_workflow.id


def test_list_workflows(library):
    """Test listing workflows"""
    # Save multiple workflows
    for i in range(3):
        workflow = WorkflowDefinition(
            name=f"Workflow {i}",
            version="1.0.0",
            steps=[WorkflowStep(id="step1", tool="test", action="run", parameters={})],
        )
        library.save(workflow)

    workflows = library.list()

    assert len(workflows) == 3


def test_list_workflows_with_tags(library):
    """Test listing workflows filtered by tags"""
    # Save workflows with different tags
    workflow1 = WorkflowDefinition(
        name="Tagged Workflow 1",
        version="1.0.0",
        tags=["production", "critical"],
        steps=[WorkflowStep(id="step1", tool="test", action="run", parameters={})],
    )

    workflow2 = WorkflowDefinition(
        name="Tagged Workflow 2",
        version="1.0.0",
        tags=["development", "test"],
        steps=[WorkflowStep(id="step1", tool="test", action="run", parameters={})],
    )

    library.save(workflow1)
    library.save(workflow2)

    # Filter by production tag
    results = library.list(tags=["production"])

    assert len(results) == 1
    assert results[0].name == "Tagged Workflow 1"


def test_list_workflows_with_search(library):
    """Test listing workflows with search query"""
    workflow1 = WorkflowDefinition(
        name="Email Workflow",
        version="1.0.0",
        description="Send daily email reports",
        steps=[WorkflowStep(id="step1", tool="test", action="run", parameters={})],
    )

    workflow2 = WorkflowDefinition(
        name="Backup Workflow",
        version="1.0.0",
        description="Backup files daily",
        steps=[WorkflowStep(id="step1", tool="test", action="run", parameters={})],
    )

    library.save(workflow1)
    library.save(workflow2)

    # Search for "email"
    results = library.list(search="email")

    assert len(results) == 1
    assert results[0].name == "Email Workflow"


def test_delete_workflow(library, sample_workflow):
    """Test deleting workflow"""
    library.save(sample_workflow)

    # Verify it exists
    assert library.exists("Test Workflow")

    # Delete it
    result = library.delete("Test Workflow")

    assert result is True
    assert not library.exists("Test Workflow")


def test_delete_nonexistent_workflow(library):
    """Test deleting non-existent workflow returns False"""
    result = library.delete("Nonexistent")
    assert result is False


def test_workflow_exists(library, sample_workflow):
    """Test checking if workflow exists"""
    assert not library.exists("Test Workflow")

    library.save(sample_workflow)

    assert library.exists("Test Workflow")


def test_count_workflows(library):
    """Test counting workflows"""
    assert library.count() == 0

    # Add workflows
    for i in range(5):
        workflow = WorkflowDefinition(
            name=f"Workflow {i}",
            version="1.0.0",
            steps=[WorkflowStep(id="step1", tool="test", action="run", parameters={})],
        )
        library.save(workflow)

    assert library.count() == 5


def test_update_workflow(library, sample_workflow):
    """Test updating existing workflow"""
    library.save(sample_workflow)

    # Modify workflow
    sample_workflow.description = "Updated description"
    library.save(sample_workflow)

    # Retrieve and verify
    retrieved = library.get("Test Workflow")
    assert retrieved.description == "Updated description"


def test_export_workflow_json(library, sample_workflow, temp_db):
    """Test exporting workflow to JSON"""
    library.save(sample_workflow)

    export_path = os.path.join(os.path.dirname(temp_db), "export.json")
    result = library.export_workflow("Test Workflow", export_path)

    assert result is True
    assert Path(export_path).exists()


def test_export_nonexistent_workflow(library, temp_db):
    """Test exporting non-existent workflow returns False"""
    export_path = os.path.join(os.path.dirname(temp_db), "export.json")
    result = library.export_workflow("Nonexistent", export_path)

    assert result is False


def test_import_workflow_json(library, sample_workflow, temp_db):
    """Test importing workflow from JSON"""
    # First export a workflow
    library.save(sample_workflow)
    export_path = os.path.join(os.path.dirname(temp_db), "export.json")
    library.export_workflow("Test Workflow", export_path)

    # Delete from library
    library.delete("Test Workflow")

    # Import back
    imported = library.import_workflow(export_path)

    assert imported is not None
    assert imported.name == "Test Workflow"
    assert library.exists("Test Workflow")


def test_log_execution(library, sample_workflow):
    """Test logging workflow execution"""
    from datetime import datetime

    library.save(sample_workflow)

    result = library.log_execution(
        workflow_id=sample_workflow.id,
        execution_id="exec-123",
        parameters={"param1": "value1"},
        status="completed",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        result={"output": "success"},
    )

    assert result is True


def test_get_execution_history(library, sample_workflow):
    """Test retrieving execution history"""
    from datetime import datetime

    library.save(sample_workflow)

    # Log multiple executions
    for i in range(3):
        library.log_execution(
            workflow_id=sample_workflow.id,
            execution_id=f"exec-{i}",
            parameters={},
            status="completed",
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )

    history = library.get_execution_history("Test Workflow")

    assert len(history) == 3


def test_get_execution_history_limit(library, sample_workflow):
    """Test execution history respects limit"""
    from datetime import datetime

    library.save(sample_workflow)

    # Log multiple executions
    for i in range(10):
        library.log_execution(
            workflow_id=sample_workflow.id,
            execution_id=f"exec-{i}",
            parameters={},
            status="completed",
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )

    history = library.get_execution_history("Test Workflow", limit=5)

    assert len(history) == 5
