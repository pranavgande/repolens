"""Deterministic AI-free fallbacks for Repolens.

These functions keep the public demo usable when no external LLM API key is
configured. They are intentionally conservative: they describe evidence
already present in the repository analysis instead of pretending to reason
like an LLM.
"""

from pathlib import Path
from typing import Iterable


def folder_description(folder_name: str, files: Iterable[str], language: str = "unknown") -> str:
    name = folder_name.lower()
    file_names = [Path(f).name.lower() for f in files]
    joined = " ".join(file_names)

    patterns = [
        (("test", "tests", "__tests__"), "contains automated tests and validation code"),
        (("route", "routes", "api"), "contains request routing or API boundary code"),
        (("controller", "controllers"), "contains request-handling or controller logic"),
        (("service", "services"), "contains application or domain service logic"),
        (("model", "models", "schema", "schemas"), "contains data models or schema definitions"),
        (("component", "components"), "contains reusable UI components"),
        (("hook", "hooks"), "contains reusable frontend hooks"),
        (("util", "utils", "helpers"), "contains shared utility functions"),
        (("middleware", "middlewares"), "contains middleware that runs between requests and handlers"),
        (("config", "configs"), "contains application configuration and environment setup"),
        (("graph", "analysis", "analyzer"), "contains analysis and dependency-processing logic"),
        (("m1",), "contains the first-stage repository or folder analysis pipeline"),
        (("m2",), "contains entry-point and execution-flow analysis"),
        (("m3",), "contains dependency-graph construction and structural analysis"),
        (("b3",), "contains repository-level summary and reporting logic"),
    ]
    for names, description in patterns:
        if name in names:
            return description

    if any(ext in joined for ext in (".tsx", ".jsx", ".css")) and language in {"javascript", "typescript"}:
        return "contains frontend presentation code and related UI assets"
    if any(ext in joined for ext in (".py",)) and language == "python":
        return "contains Python implementation modules for the application"

    return f"contains project files related to the '{folder_name}' module"


def execution_flow(
    entry_file: str,
    language: str,
    source_code: str,
    deps: Iterable[str],
) -> str:
    lines = [f"Entry Point: {entry_file}", "Execution Flow:"]
    source = source_code.lower()
    dep_list = list(deps)

    if language == "python":
        if "dotenv" in source:
            lines.append(f"  {entry_file} → loads environment configuration")
        if any(token in source for token in ("fastapi(", "flask(", "django")):
            lines.append(f"  → initializes the web application")
        if any(token in source for token in ("uvicorn.run(", "app.run(", "execute_from_command_line(")):
            lines.append("  → starts the application server")
        elif "if __name__" in source:
            lines.append("  → enters the module's main execution guard")
    elif language in {"javascript", "typescript"}:
        if "dotenv.config(" in source:
            lines.append(f"  {entry_file} → loads environment configuration")
        if any(token in source for token in ("express(", "fastify(", "createServer(")):
            lines.append("  → initializes the application/server")
        if any(token in source for token in (".listen(", "server.listen(")):
            lines.append("  → starts listening for incoming requests")
    else:
        lines.append(f"  {entry_file} → begins application startup")

    if dep_list:
        shown = ", ".join(dep_list[:6])
        suffix = " and more" if len(dep_list) > 6 else ""
        lines.append(f"  → loads direct dependencies: {shown}{suffix}")

    if len(lines) == 2:
        lines.append(f"  {entry_file} → executes the detected entry-point module")
    return "\n".join(lines)


def repository_summary(
    repo_url: str,
    language: str,
    total_files: int,
    architecture_hint: str,
    entry_file: str,
    total_edges: int,
    critical_files: str,
    cycles: str,
) -> str:
    cycle_sentence = (
        "The dependency graph contains circular dependencies that may deserve review."
        if not cycles.startswith("None")
        else "The dependency graph contains no detected circular dependencies."
    )
    critical = critical_files.splitlines()[0].strip() if critical_files else "No critical files were identified."
    return (
        f"This {language} repository contains {total_files} analysed files and follows a "
        f"{architecture_hint} structure. Its detected entry point is {entry_file}, with "
        f"{total_edges} dependency edges mapped across the codebase. The most central file "
        f"identified by the dependency analysis is {critical}. {cycle_sentence} "
        f"Repolens generated this summary from static repository evidence for {repo_url}; "
        f"an external language model was not required."
    )
