from ai.fallback import execution_flow, folder_description, repository_summary


def test_execution_flow_works_without_external_ai():
    result = execution_flow(
        entry_file="main.py",
        language="python",
        source_code="from fastapi import FastAPI\napp = FastAPI()\n",
        deps=["routes/api.py"],
    )
    assert "Entry Point: main.py" in result
    assert "initializes the web application" in result
    assert "routes/api.py" in result


def test_folder_description_uses_project_structure():
    result = folder_description("routes", ["users.py", "health.py"], "python")
    assert result == "contains request routing or API boundary code"


def test_repository_summary_is_conservative():
    result = repository_summary(
        repo_url="https://github.com/example/repo",
        language="python",
        total_files=12,
        architecture_hint="Layered",
        entry_file="main.py",
        total_edges=17,
        critical_files="  main.py (imported by 0 file(s))",
        cycles="None — clean architecture",
    )
    assert "12 analysed files" in result
    assert "main.py" in result
    assert "no detected circular dependencies" in result
