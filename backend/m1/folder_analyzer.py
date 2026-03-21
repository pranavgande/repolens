# m1/folder_analyzer.py

"""
Tier 1 and Tier 2 of M1's three-tier folder analysis system.

Tier 1 — Pattern matching: looks up the folder name in a dictionary of
universally recognised conventions. If found, returns immediately with
no further work. This handles roughly 80% of folders in any real project.

Tier 2 — Content inference: if the folder name wasn't recognised, peeks
at the filenames inside and infers purpose from naming patterns. No file
contents are read — just the names themselves, which M3 already collected.

If both tiers fail to produce a confident answer, this module returns None
and the pipeline hands off to folder_explainer.py (the LLM fallback).
"""


# ── Tier 1: Known folder pattern dictionary ───────────────────────────────────
#
# This dictionary is the heart of M1. Each key is a folder name (lowercased),
# and each value is a plain-English description of that folder's role.
#
# The descriptions are written from the perspective of a new developer reading
# them for the first time — they explain *why* the folder exists, not *what
# files are inside it*. That distinction matters: a developer can see the files
# themselves, but they can't always tell why those files live where they do.
#
# Coverage spans Node.js/Express, Python/FastAPI/Flask/Django, React,
# Java Spring, and common full-stack conventions.

KNOWN_FOLDER_PATTERNS = {

    # ── Core MVC / layered architecture ───────────────────────────────────────
    "controllers":  "Handles incoming HTTP requests, validates inputs, and delegates business logic to the service layer",
    "controller":   "Handles incoming HTTP requests, validates inputs, and delegates business logic to the service layer",
    "models":       "Defines data structures, database schemas, and data access patterns",
    "model":        "Defines data structures, database schemas, and data access patterns",
    "views":        "Contains presentation templates or view logic that renders data for the user",
    "view":         "Contains presentation templates or view logic that renders data for the user",
    "services":     "Contains business logic, decoupled from the HTTP layer and reusable across controllers",
    "service":      "Contains business logic, decoupled from the HTTP layer and reusable across controllers",

    # ── Routing ───────────────────────────────────────────────────────────────
    "routes":       "Defines API endpoints and maps each URL path to its corresponding controller function",
    "route":        "Defines API endpoints and maps each URL path to its corresponding controller function",
    "routers":      "Defines API endpoints and maps each URL path to its corresponding controller function",
    "router":       "Defines API endpoints and maps each URL path to its corresponding controller function",

    # ── Middleware / filters ───────────────────────────────────────────────────
    "middleware":   "Preprocesses requests before they reach route handlers — handles auth, logging, rate limiting, and validation",
    "middlewares":  "Preprocesses requests before they reach route handlers — handles auth, logging, rate limiting, and validation",
    "filters":      "Intercepts and processes requests or responses — commonly used for authentication and error handling",
    "interceptors": "Intercepts HTTP calls to add cross-cutting behaviour like logging, caching, or token refresh",
    "guards":       "Enforces access control rules, preventing unauthorised users from reaching protected routes",

    # ── Configuration ─────────────────────────────────────────────────────────
    "config":       "Stores application configuration — database connections, environment settings, and third-party service setup",
    "configs":      "Stores application configuration — database connections, environment settings, and third-party service setup",
    "configuration":"Stores application configuration — database connections, environment settings, and third-party service setup",
    "settings":     "Defines application-wide settings, often loaded from environment variables",
    "env":          "Contains environment variable definitions and configuration profiles for different deployment contexts",

    # ── Utilities / helpers ───────────────────────────────────────────────────
    "utils":        "Shared utility functions used across the codebase — formatting, validation helpers, and common transformations",
    "util":         "Shared utility functions used across the codebase — formatting, validation helpers, and common transformations",
    "helpers":      "Helper functions that simplify repetitive tasks across multiple modules",
    "helper":       "Helper functions that simplify repetitive tasks across multiple modules",
    "lib":          "Internal library code — reusable modules that provide core functionality to the rest of the application",
    "libs":         "Internal library code — reusable modules that provide core functionality to the rest of the application",
    "common":       "Shared code used by multiple modules — constants, base classes, shared types, and cross-cutting utilities",
    "shared":       "Code shared across multiple features or layers — typically DTOs, interfaces, and utility functions",
    "core":         "Fundamental building blocks of the application — base classes, core abstractions, and foundational logic",

    # ── Database ──────────────────────────────────────────────────────────────
    "migrations":   "Database migration scripts that define schema changes over time in a version-controlled way",
    "migration":    "Database migration scripts that define schema changes over time in a version-controlled way",
    "seeds":        "Database seed scripts that populate initial or test data",
    "seeders":      "Database seed scripts that populate initial or test data",
    "db":           "Database-related code — connection setup, query builders, and data access utilities",
    "database":     "Database-related code — connection setup, query builders, and data access utilities",
    "repositories": "Data access layer that abstracts database operations behind a clean interface",
    "repository":   "Data access layer that abstracts database operations behind a clean interface",
    "schemas":      "Defines data validation schemas or database table structures",
    "schema":       "Defines data validation schemas or database table structures",

    # ── Testing ───────────────────────────────────────────────────────────────
    "tests":        "Automated tests — unit tests, integration tests, and end-to-end tests for the application",
    "test":         "Automated tests — unit tests, integration tests, and end-to-end tests for the application",
    "__tests__":    "Jest test files — unit and integration tests co-located with the source they test",
    "spec":         "Test specification files — commonly used with Jasmine, RSpec, or similar BDD frameworks",
    "specs":        "Test specification files — commonly used with Jasmine, RSpec, or similar BDD frameworks",
    "e2e":          "End-to-end tests that simulate real user interactions with the fully running application",
    "fixtures":     "Static test data used by tests to set up known application states",
    "mocks":        "Mock implementations of external dependencies used to isolate units during testing",

    # ── Frontend / UI ─────────────────────────────────────────────────────────
    "components":   "Reusable UI components — self-contained building blocks of the user interface",
    "component":    "Reusable UI components — self-contained building blocks of the user interface",
    "pages":        "Top-level page components, each corresponding to a distinct route in the application",
    "page":         "Top-level page components, each corresponding to a distinct route in the application",
    "layouts":      "Wrapper components that define the overall page structure shared across multiple pages",
    "layout":       "Wrapper components that define the overall page structure shared across multiple pages",
    "hooks":        "Custom React hooks that encapsulate reusable stateful logic",
    "hook":         "Custom React hooks that encapsulate reusable stateful logic",
    "store":        "Global state management — Redux store, Zustand store, or similar centralised state",
    "stores":       "Global state management — Redux store, Zustand store, or similar centralised state",
    "context":      "React Context providers that make shared state available to component subtrees",
    "contexts":     "React Context providers that make shared state available to component subtrees",
    "styles":       "CSS, SCSS, or styled-component files that define the visual appearance of the UI",
    "style":        "CSS, SCSS, or styled-component files that define the visual appearance of the UI",
    "assets":       "Static assets — images, fonts, icons, and other binary files served directly to the client",
    "static":       "Statically served files — CSS, JavaScript bundles, images, and other public assets",
    "public":       "Publicly accessible static files served directly by the web server without processing",
    "templates":    "HTML or template engine files that define the structure of rendered pages",
    "template":     "HTML or template engine files that define the structure of rendered pages",

    # ── API / integration ─────────────────────────────────────────────────────
    "api":          "API-related code — endpoint definitions, API clients, or interface contracts",
    "graphql":      "GraphQL schema definitions, resolvers, and query/mutation handlers",
    "grpc":         "gRPC service definitions, protocol buffer schemas, and generated client/server stubs",
    "webhooks":     "Webhook handlers that receive and process incoming event notifications from external services",
    "integrations": "Third-party service integrations — external APIs, payment processors, email providers, and so on",

    # ── Infrastructure / DevOps ───────────────────────────────────────────────
    "scripts":      "Utility and automation scripts — build scripts, deployment helpers, and developer tooling",
    "docker":       "Docker configuration files — Dockerfiles and docker-compose definitions",
    "deploy":       "Deployment configuration and infrastructure-as-code definitions",
    "deployment":   "Deployment configuration and infrastructure-as-code definitions",
    "terraform":    "Terraform infrastructure definitions for cloud resource provisioning",
    "kubernetes":   "Kubernetes manifests for container orchestration and deployment",
    "k8s":          "Kubernetes manifests for container orchestration and deployment",
    "ci":           "Continuous integration configuration — pipeline definitions and automated build scripts",
    "logs":         "Log output directory — runtime application logs stored for debugging and monitoring",

    # ── Documentation ─────────────────────────────────────────────────────────
    "docs":         "Project documentation — API references, architecture guides, and developer notes",
    "doc":          "Project documentation — API references, architecture guides, and developer notes",
    "documentation":"Project documentation — API references, architecture guides, and developer notes",

    # ── Types / interfaces ────────────────────────────────────────────────────
    "types":        "TypeScript type definitions and interfaces shared across the codebase",
    "type":         "TypeScript type definitions and interfaces shared across the codebase",
    "interfaces":   "Abstract interface definitions that decouple implementation from contract",
    "interface":    "Abstract interface definitions that decouple implementation from contract",
    "dto":          "Data Transfer Objects — plain data structures used to pass data between layers",
    "dtos":         "Data Transfer Objects — plain data structures used to pass data between layers",
    "entities":     "Domain entity classes that represent core business objects with identity and lifecycle",

    # ── Events / messaging ────────────────────────────────────────────────────
    "events":       "Event definitions and event handler implementations for an event-driven architecture",
    "event":        "Event definitions and event handler implementations for an event-driven architecture",
    "queues":       "Message queue producers and consumers for asynchronous task processing",
    "queue":        "Message queue producers and consumers for asynchronous task processing",
    "jobs":         "Background job definitions — scheduled tasks and asynchronous work items",
    "job":          "Background job definitions — scheduled tasks and asynchronous work items",
    "tasks":        "Asynchronous task definitions, typically processed by a task queue like Celery or BullMQ",
    "workers":      "Background worker processes that consume jobs from a queue and execute them asynchronously",
    "worker":       "Background worker processes that consume jobs from a queue and execute them asynchronously",

    # ── Security ──────────────────────────────────────────────────────────────
    "auth":         "Authentication and authorisation logic — login flows, token management, and permission checks",
    "authentication":"Authentication logic — identity verification, session management, and credential handling",
    "authorisation":"Authorisation logic — permission checks and access control rule enforcement",
    "authorization":"Authorisation logic — permission checks and access control rule enforcement",
    "security":     "Security-related code — encryption utilities, security headers, and vulnerability mitigations",

    # ── Source root aliases ───────────────────────────────────────────────────
    "src":          "Primary source code directory — contains all application logic",
    "app":          "Core application code — the main module housing features, routing, and business logic",
    "main":         "Application entry and initialisation code",
}


# ── Architecture pattern detection ────────────────────────────────────────────
#
# These sets define which folder combinations suggest a particular architecture.
# If a project's folders are a superset of a pattern's required folders,
# we label the architecture accordingly. This feeds the architecture_hint
# field in M1's output and supports Bonus Feature B3.

ARCHITECTURE_PATTERNS = {
    "MVC":              {"models", "views", "controllers"},
    "MVC + Service":    {"models", "controllers", "services", "routes"},
    "Layered":          {"controllers", "services", "repositories"},
    "Feature-based":    {"components", "hooks", "store"},
    "Clean Architecture":{"entities", "repositories", "services", "controllers"},
    "Event-driven":     {"events", "handlers", "queues"},
}

# ── Filename suffixes that reveal folder purpose ───────────────────────────────
#
# Used in Tier 2 content inference. If a significant portion of the files
# inside an unknown folder share one of these suffixes, we can infer the
# folder's role even without recognising its name.

FILENAME_SUFFIX_HINTS = {
    ".controller.js":  "Handles HTTP requests — likely a controllers layer",
    ".controller.ts":  "Handles HTTP requests — likely a controllers layer",
    ".service.js":     "Contains business logic — likely a services layer",
    ".service.ts":     "Contains business logic — likely a services layer",
    ".model.js":       "Defines data schemas — likely a models layer",
    ".model.ts":       "Defines data schemas — likely a models layer",
    ".route.js":       "Defines API routes — likely a routing layer",
    ".route.ts":       "Defines API routes — likely a routing layer",
    ".routes.js":      "Defines API routes — likely a routing layer",
    ".routes.ts":      "Defines API routes — likely a routing layer",
    ".middleware.js":  "Request preprocessing — likely a middleware layer",
    ".middleware.ts":  "Request preprocessing — likely a middleware layer",
    ".test.js":        "Automated tests — likely a test suite",
    ".test.ts":        "Automated tests — likely a test suite",
    ".spec.js":        "Automated tests — likely a test suite",
    ".spec.ts":        "Automated tests — likely a test suite",
    ".config.js":      "Configuration files — likely a config layer",
    ".config.ts":      "Configuration files — likely a config layer",
    ".helper.js":      "Utility helpers — likely a helpers or utils layer",
    ".helper.ts":      "Utility helpers — likely a helpers or utils layer",
    ".dto.ts":         "Data transfer objects — likely a DTOs layer",
    ".entity.ts":      "Domain entities — likely an entities layer",
    ".repository.ts":  "Data access layer — likely a repositories layer",
    ".component.tsx":  "React UI components — likely a components layer",
    ".component.ts":   "Angular components — likely a components layer",
    ".hook.ts":        "Custom React hooks — likely a hooks layer",
    ".py":             "Python source files",
}


def analyze_folder(
    folder_name: str,
    files_inside: list[str],
) -> dict:
    """
    Analyse a single folder and return a description with a confidence source.

    This function runs Tier 1 (pattern match) first. If that produces no
    result, it runs Tier 2 (content inference from filenames). If that also
    produces no result, it returns source='unknown' so the pipeline knows
    to hand off to the LLM fallback.

    Parameters:
        folder_name:   the folder's name, e.g. "controllers" or "orchestration"
        files_inside:  list of filenames inside this folder, e.g.
                       ["auth.controller.js", "user.controller.js"]

    Returns a dict with:
        "description": plain-English explanation string, or None if unknown
        "source":      "pattern_match", "content_inference", or "unknown"
    """

    # ── Tier 1: Pattern match ──────────────────────────────────────────────────
    # Normalise to lowercase to handle folders named "Controllers" or "MODELS"
    normalised = folder_name.lower().strip("/").strip("\\")

    if normalised in KNOWN_FOLDER_PATTERNS:
        return {
            "description": KNOWN_FOLDER_PATTERNS[normalised],
            "source":      "pattern_match",
        }

    # ── Tier 2: Content inference from filenames ───────────────────────────────
    # Count how many files inside match each suffix hint.
    # If any suffix accounts for the majority of files in the folder,
    # that's a strong enough signal to describe the folder's purpose.
    if files_inside:
        suffix_counts: dict[str, int] = {}

        for filename in files_inside:
            for suffix, hint in FILENAME_SUFFIX_HINTS.items():
                if filename.endswith(suffix):
                    suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1

        if suffix_counts:
            # Find the most common suffix in this folder
            dominant_suffix = max(suffix_counts, key=lambda s: suffix_counts[s])
            dominant_count  = suffix_counts[dominant_suffix]
            total_files     = len(files_inside)

            # If more than half the files share a recognisable suffix,
            # we're confident enough to describe the folder from that signal.
            if dominant_count / total_files >= 0.5:
                return {
                    "description": FILENAME_SUFFIX_HINTS[dominant_suffix],
                    "source":      "content_inference",
                }

    # ── No result — hand off to LLM ───────────────────────────────────────────
    return {
        "description": None,
        "source":      "unknown",
    }


def detect_architecture(folder_names: set[str]) -> str:
    """
    Detect the architectural pattern used in the project based on which
    folders are present.

    We check each known pattern's required folder set against the actual
    folder names. The most specific matching pattern (the one with the most
    required folders) wins, because a project that has controllers + services
    + repositories + models is more accurately described as "Clean Architecture"
    than just "MVC".

    Returns a human-readable architecture label or "Unknown" if no pattern fits.
    """
    normalised_folders = {f.lower().strip("/") for f in folder_names}

    best_match      = None
    best_match_size = 0

    for pattern_name, required_folders in ARCHITECTURE_PATTERNS.items():
        # Check if all required folders for this pattern are present
        if required_folders.issubset(normalised_folders):
            # Prefer more specific patterns (larger required sets)
            if len(required_folders) > best_match_size:
                best_match      = pattern_name
                best_match_size = len(required_folders)

    return best_match if best_match else "Unknown"


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    # Simulate the clusters dict that M3's analyzer produces.
    # This is exactly the shape of graph_stats["clusters"].
    mock_clusters = {
        "routes":      ["auth.routes.js", "user.routes.js"],
        "controllers": ["auth.controller.js", "user.controller.js"],
        "services":    ["auth.service.js", "user.service.js"],
        "models":      ["user.model.js"],
        "middleware":  ["auth.middleware.js"],
        "config":      ["db.config.js"],
        ".":           ["server.js"],  # root-level files
    }

    print("Testing folder_analyzer.py against mock clusters")
    print("=" * 55)

    for folder, files in mock_clusters.items():
        if folder == ".":
            continue  # skip root — it's the entry point, not a module group
        result = analyze_folder(folder, files)
        print(f"\n  {folder}/")
        print(f"    Description : {result['description']}")
        print(f"    Source      : {result['source']}")

    folder_names = set(mock_clusters.keys())
    arch = detect_architecture(folder_names)
    print(f"\nDetected architecture: {arch}")