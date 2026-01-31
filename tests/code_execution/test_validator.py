"""
Comprehensive Tests for CodeValidator

Tests syntax validation, security scanning, quality assessment, and dataclass functionality
for all supported languages.

Total tests: 15
"""

import pytest
from alpha.code_execution.validator import (
    CodeValidator,
    ValidationResult,
    SecurityReport,
    QualityReport
)


class TestCodeValidator:
    """Test suite for CodeValidator"""

    @pytest.fixture
    def validator(self):
        """Create CodeValidator instance"""
        return CodeValidator()

    # Syntax Validation Tests

    def test_validate_syntax_python_valid(self, validator):
        """Test syntax validation for valid Python code"""
        code = "def hello():\n    print('Hello, World!')\n\nhello()"
        result = validator.validate_syntax(code, "python")

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_syntax_python_invalid(self, validator):
        """Test syntax validation for invalid Python code"""
        code = "def hello(\n    print('missing closing paren')"
        result = validator.validate_syntax(code, "python")

        assert not result.is_valid
        assert len(result.errors) > 0

    def test_validate_syntax_javascript_valid(self, validator):
        """Test syntax validation for valid JavaScript code"""
        code = "function add(a, b) { return a + b; }\nconsole.log(add(1, 2));"
        result = validator.validate_syntax(code, "javascript")

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_syntax_bash_valid(self, validator):
        """Test syntax validation for valid Bash code"""
        code = "#!/bin/bash\necho 'Hello from Bash'"
        result = validator.validate_syntax(code, "bash")

        assert result.is_valid

    def test_validate_syntax_empty_code(self, validator):
        """Test validation of empty code"""
        result = validator.validate_syntax("", "python")

        assert not result.is_valid
        assert "empty" in result.errors[0].lower()

    def test_validate_syntax_unsupported_language(self, validator):
        """Test validation with unsupported language"""
        result = validator.validate_syntax("some code", "ruby")

        assert not result.is_valid
        assert "unsupported" in result.errors[0].lower() or "not supported" in result.errors[0].lower()

    # Security Scanning Tests

    def test_check_security_python_safe(self, validator):
        """Test security check for safe Python code"""
        code = "x = 5\ny = 10\nprint(x + y)"
        report = validator.check_security(code, "python")

        assert report.is_safe
        assert report.risk_level == "low"
        assert len(report.dangerous_patterns) == 0

    def test_check_security_python_dangerous_eval(self, validator):
        """Test detection of dangerous eval/exec patterns"""
        code = "user_input = input('Enter code: ')\neval(user_input)"
        report = validator.check_security(code, "python")

        assert not report.is_safe
        assert report.risk_level in ["medium", "high"]
        assert len(report.dangerous_patterns) > 0
        assert any("eval" in p for p in report.dangerous_patterns)

    def test_check_security_bash_rm_command(self, validator):
        """Test detection of dangerous rm commands"""
        code = "#!/bin/bash\nrm -rf /"
        report = validator.check_security(code, "bash")

        assert not report.is_safe
        assert report.risk_level == "high"
        assert len(report.dangerous_patterns) > 0

    def test_check_security_risk_level_assessment(self, validator):
        """Test risk level assessment"""
        # High risk code (using eval which is explicitly high-risk)
        high_risk = "eval('__import__(\"os\").system(\"rm -rf /\")')"
        report_high = validator.check_security(high_risk, "python")
        assert report_high.risk_level == "high"

        # Medium risk code
        medium_risk = "import subprocess\nsubprocess.run(['ls', '-la'])"
        report_medium = validator.check_security(medium_risk, "python")
        assert report_medium.risk_level in ["medium", "low"]

    # Quality Assessment Tests

    def test_assess_quality_good_code(self, validator):
        """Test quality assessment for well-written code"""
        code = '''def calculate_factorial(n):
    """Calculate factorial of n recursively."""
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)

# Test the function
result = calculate_factorial(5)
print(f"Factorial: {result}")
'''
        report = validator.assess_quality(code, "python")

        assert report.score > 0.5
        assert "total_lines" in report.metrics
        assert "has_documentation" in report.metrics

    def test_assess_quality_poor_code(self, validator):
        """Test quality assessment for code with issues"""
        code = "x=1;y=2;z=3;print(x+y+z);a=4;b=5;c=6;d=7;e=8;f=9;g=10"
        report = validator.assess_quality(code, "python")

        assert report.score < 0.8
        assert len(report.issues) > 0

    def test_assess_quality_empty_code(self, validator):
        """Test quality assessment of empty code"""
        report = validator.assess_quality("", "python")

        assert report.score == 0.0
        assert "empty" in report.issues[0].lower()

    # Dataclass Tests

    def test_validation_result_string_representation(self):
        """Test ValidationResult __str__ method"""
        result = ValidationResult(
            is_valid=False,
            errors=["Syntax error on line 5"],
            warnings=["Unused variable"],
            suggestions=["Add docstrings"]
        )

        str_repr = str(result)
        assert "INVALID" in str_repr
        assert "Syntax error" in str_repr
        assert "Unused variable" in str_repr

    def test_security_report_string_representation(self):
        """Test SecurityReport __str__ method"""
        report = SecurityReport(
            is_safe=False,
            dangerous_patterns=["eval()", "exec()"],
            risk_level="high",
            recommendations=["Avoid eval", "Use safe alternatives"]
        )

        str_repr = str(report)
        assert "UNSAFE" in str_repr
        assert "high" in str_repr.lower()
        assert "eval()" in str_repr

    def test_quality_report_string_representation(self):
        """Test QualityReport __str__ method"""
        report = QualityReport(
            score=0.75,
            issues=["Missing docstrings"],
            metrics={"total_lines": 20, "comment_ratio": 0.1}
        )

        str_repr = str(report)
        assert "75%" in str_repr
        assert "total_lines" in str_repr
        assert "Missing docstrings" in str_repr


class TestValidatorIntegration:
    """Integration tests for validator with language handlers"""

    @pytest.fixture
    def validator(self):
        return CodeValidator()

    def test_language_handler_integration_python(self, validator):
        """Test integration with Python handler"""
        code = "import os\nprint(os.getcwd())"
        
        # Validate syntax
        validation = validator.validate_syntax(code, "python")
        assert validation.is_valid

        # Check security
        security = validator.check_security(code, "python")
        assert isinstance(security, SecurityReport)

        # Assess quality
        quality = validator.assess_quality(code, "python")
        assert isinstance(quality, QualityReport)

    def test_handler_caching(self, validator):
        """Test that language handlers are cached"""
        # First call creates handler
        validator.validate_syntax("x = 1", "python")
        
        # Second call should use cached handler
        validator.validate_syntax("y = 2", "python")
        
        # Verify cache is populated
        assert "python" in validator._handlers_cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
