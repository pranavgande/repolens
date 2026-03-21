# m1/folder_explainer.py

"""
Tier 3 of M1's folder analysis: LLM fallback for unrecognised folders.

This module is only invoked when folder_analyzer.py's pattern matching
and content inference both failed to produce a confident description.
In a typical well-structured project this happens rarely — maybe once
or twice per repository for project-specific folder names like
'orchestration/', 'saga/', or 'compliance/'.

Follows the exact same USE_LOCAL_MODEL flag pattern as m2/flow_explainer.py
so switching between local Qwen and Gemini is a single boolean change,
consistent across the entire backend.
"""

import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# ── Model selection — mirrors m2/flow_explainer.py exactly ───────────────────
USE_LOCAL_MODEL = False
LOCAL_MODEL_ID  = "Qwen/Qwen2.5-1.5B-Instruct"
HF_CACHE_DIR    = "D:/Huggingface_cache"


# ── Prompt template ───────────────────────────────────────────────────────────
# The prompt is intentionally minimal. We give the LLM three pieces of
# information: the folder name, the filenames inside it, and the broader
# project context (language and architecture hint). From those three signals
# a capable model can produce a reliable one-sentence description.
#
# We constrain the output to exactly one sentence because M1's output is
# meant to be an annotated file tree — concise labels, not paragraphs.
# A judge scanning the output during a demo should be able to read the
# entire M1 result in under 30 seconds.

FOLDER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a senior software architect reviewing an unfamiliar codebase. "
        "Your job is to write clear, concise folder descriptions that help a new "
        "developer understand the project structure at a glance. "
        "Always respond with exactly one sentence. Never use bullet points. "
        "Never start with 'This folder' — start with a verb or noun directly."
    ),
    (
        "human",
        """A software project written in {language} has a folder called '{folder_name}'.

The files inside this folder are:
{file_list}

The detected project architecture is: {architecture_hint}

In exactly one sentence, describe what role this folder plays in the project.
Do not mention specific filenames. Focus on the folder's purpose and responsibility."""
    )
])


# ── Backend 1: Gemini ─────────────────────────────────────────────────────────

def _build_chain_gemini():
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY not found. Make sure your .env file exists "
            "at the project root and contains: GEMINI_API_KEY=your_key_here"
        )

    model = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=api_key,
        # temperature=0 makes the output maximally deterministic.
        # For a one-sentence description, you want consistency —
        # the same folder should always get roughly the same description.
        temperature=0,
    )

    return FOLDER_PROMPT | model


# ── Backend 2: Local Qwen ─────────────────────────────────────────────────────

def _build_chain_local():
    from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
    import transformers
    import logging
    import warnings
    
    transformers.logging.set_verbosity_error()
    warnings.filterwarnings("ignore")

    os.environ["HF_HOME"] = HF_CACHE_DIR

    print("  Loading local Qwen2.5-1.5B-Instruct model...")

    llm = HuggingFacePipeline.from_model_id(
        model_id=LOCAL_MODEL_ID,
        task="text-generation",
        pipeline_kwargs={
            # 100 tokens is plenty for a single sentence description.
            # Keeping this low makes local inference significantly faster
            # than the 512 tokens we use for M2's longer narrative output.
            "max_new_tokens":    100,
            "do_sample":         False,
            "temperature":       None,
            "top_p":             None,
            "repetition_penalty":1.1,
        },
    )

    model = ChatHuggingFace(llm=llm)
    return FOLDER_PROMPT | model


# ── Dispatcher ────────────────────────────────────────────────────────────────

def _build_chain():
    if USE_LOCAL_MODEL:
        print("  [Backend: Local Qwen2.5-1.5B-Instruct]")
        return _build_chain_local()
    else:
        print("  [Backend: Gemini 1.5 Flash via API]")
        return _build_chain_gemini()


# ── Main function ─────────────────────────────────────────────────────────────

def explain_folder(
    folder_name:       str,
    files_inside:      list[str],
    language:          str = "javascript",
    architecture_hint: str = "Unknown",
) -> str:
    """
    Ask the LLM to describe a folder whose purpose couldn't be determined
    by pattern matching or content inference.

    Returns a plain string — the one-sentence description — rather than
    a dict, because this function has a single, simple output. The pipeline
    wraps it into the result dict itself.

    Parameters:
        folder_name:       e.g. "orchestration" or "saga"
        files_inside:      list of filenames in that folder
        language:          detected project language from M2's result
        architecture_hint: detected architecture from folder_analyzer.py
    """
    chain = _build_chain()

    # Format the file list as a readable bulleted string for the prompt.
    # We cap at 10 files to keep the prompt short — if a folder has 50 files,
    # the first 10 names are enough for the LLM to understand its purpose.
    sample_files = files_inside[:10]
    file_list    = "\n".join(f"  - {f}" for f in sample_files)
    if len(files_inside) > 10:
        file_list += f"\n  ... and {len(files_inside) - 10} more files"

    print(f"  Calling LLM for unrecognised folder: '{folder_name}'...")

    response = chain.invoke({
        "folder_name":       folder_name,
        "file_list":         file_list,
        "language":          language,
        "architecture_hint": architecture_hint,
    })

    # Same version-resilient content extraction as flow_explainer.py —
    # handles both plain string and list-of-blocks response formats.
    content = response.content
    if isinstance(content, list):
        description = " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        ).strip()
    else:
        description = content.strip()

    # --- CLEANUP FOR LOCAL HUGGINGFACE MODELS ---
    if "<|im_start|>assistant\n" in description:
        description = description.split("<|im_start|>assistant\n")[-1]
    description = description.replace("<|im_end|>", "").strip()
    # --------------------------------------------

    # Clean up common LLM response quirks — some models add a leading
    # newline or wrap the sentence in quotes.
    description = description.strip('"').strip("'").strip()

    return description


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    # Test with a deliberately unusual folder name that won't be in the
    # pattern dictionary — this simulates the real LLM fallback scenario.
    test_cases = [
        {
            "folder_name":  "orchestration",
            "files_inside": ["payment_saga.js", "order_workflow.js", "notification_flow.js"],
            "language":     "javascript",
            "architecture_hint": "MVC + Service",
        },
        {
            "folder_name":  "telemetry",
            "files_inside": ["metrics_collector.py", "trace_exporter.py", "health_reporter.py"],
            "language":     "python",
            "architecture_hint": "Layered",
        },
    ]

    backend_label = "Local Qwen2.5-1.5B" if USE_LOCAL_MODEL else "Gemini 1.5 Flash"
    print(f"Testing folder_explainer.py via {backend_label}")
    print("=" * 55)

    for case in test_cases:
        print(f"\nFolder: {case['folder_name']}/")
        description = explain_folder(**case)
        print(f"Description: {description}")