import pytest
from pathlib import Path
from tardisbase.testing.regression_comparison.run_tests import (
    get_all_optional_dependencies, 
    handle_fallback
)


def test_get_all_optional_dependencies_with_file(tmp_path):
    toml_content = """
[project.optional-dependencies]
test = ["pytest>=6.0"]
dev = ["black", "flake8"]
"""
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(toml_content)
    
    result = get_all_optional_dependencies(tmp_path)
    assert set(result) == {"test", "dev"}



