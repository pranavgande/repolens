from ai.fallback import execution_flow, folder_description, repository_summary

flow = execution_flow(
    entry_file="main.py",
    language="python",
    source_code="from fastapi import FastAPI\napp = FastAPI()\n",
    deps=["routes/api.py"],
)
assert "Entry Point: main.py" in flow
assert "initializes the web application" in flow
assert "routes/api.py" in flow

assert folder_description("routes", ["users.py"], "python") == (
    "contains request routing or API boundary code"
)

summary = repository_summary(
    repo_url="https://github.com/example/repo",
    language="python",
    total_files=12,
    architecture_hint="Layered",
    entry_file="main.py",
    total_edges=17,
    critical_files="  main.py (imported by 0 file(s))",
    cycles="None — clean architecture",
)
assert "12 analysed files" in summary
assert "no detected circular dependencies" in summary

print("fallback smoke test: PASS")
