# m2/flow_explainer.py

"""
Phase 3 of the M2 pipeline: Execution Flow Explanation.

Supports two model backends switched via the USE_LOCAL_MODEL flag:
  - Gemini 1.5 Flash (via LangChain + Google API) — high quality, needs API key
  - Qwen2.5-1.5B-Instruct (local HuggingFace model) — for offline testing

Only _build_chain() and the two backend functions know about the model choice.
Everything else — the prompt, explain_flow(), the content parser — is identical
regardless of which backend is active. This is LangChain's core value: write
your logic once, swap the model without touching anything downstream.

When you're ready to switch to Gemini for the real hackathon demo,
the only change in the entire codebase is flipping USE_LOCAL_MODEL = True
to USE_LOCAL_MODEL = False. That's the whole switch.
"""

import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# ── Model selection flag ───────────────────────────────────────────────────────
# Flip this to False when you're ready to use the Gemini API for the real demo.
USE_LOCAL_MODEL = False

# Your Qwen model ID on HuggingFace Hub.
LOCAL_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

# The folder where you downloaded your HuggingFace models.
# This tells the transformers library exactly where to look on disk
# instead of searching the default cache (~/.cache/huggingface).
# Change this path to wherever your Qwen model is stored on your machine.
HF_CACHE_DIR = "D:/Huggingface_cache"


# ── Shared prompt template ─────────────────────────────────────────────────────
# Defined once at module level so both backends reuse the exact same prompt.
# This guarantees a fair comparison when you switch models — the input is
# identical, only the model changes.
FLOW_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a senior software architect helping a new developer "
        "understand an unfamiliar codebase. Be concise, precise, and "
        "focus on high-level behaviour rather than implementation details."
    ),
    (
        "human",
        """Analyse the entry point file of a {language} project and 
describe its execution flow in plain English.

=== ENTRY POINT FILE ===
Filename: {entry_file}

Source code:
```
{source_code}
```

=== DIRECT DEPENDENCIES (from static import analysis) ===
{deps_text}

=== YOUR TASK ===
Describe what happens when this application starts up, step by step.
Focus on: what gets loaded, what gets connected, what gets registered,
and what starts listening or running.

Produce your response in EXACTLY this format, no extra commentary:

Entry Point: {entry_file}
Execution Flow:
  {entry_file} <first thing it does>
  → <second step>
  → <third step>
  → <continue for each meaningful startup action>"""
    )
])


# ── Backend 1: Gemini via Google API ──────────────────────────────────────────

def _build_chain_gemini():
    """
    Build the LangChain chain backed by Gemini 1.5 Flash.
    Reads GEMINI_API_KEY from the .env file.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY not found. Make sure your .env file exists "
            "at the project root and contains: GEMINI_API_KEY=your_key_here"
        )

    model = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.2,
    )

    return FLOW_PROMPT | model


# ── Backend 2: Local Qwen2.5-1.5B-Instruct ────────────────────────────────────

def _build_chain_local():
    """
    Build the LangChain chain backed by your locally downloaded Qwen2.5 model.

    The key difference from our previous attempt is that we now use
    langchain_huggingface instead of langchain_community. This is the
    officially maintained package for local HuggingFace models, and its
    ChatHuggingFace class is specifically built to accept HuggingFacePipeline
    — no type validation errors.

    HuggingFacePipeline.from_model_id() is a convenience method that
    handles loading the tokenizer, the model weights, and constructing
    the pipeline in a single call — replacing the three manual steps
    we had before. It reads from HF_HOME to find your downloaded model.
    """
    # Imported locally so these heavy packages are only loaded when
    # the local backend is actually being used.
    from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
    import transformers
    import logging
    import warnings
    
    # Hide all the annoying library chatter from terminal output
    transformers.logging.set_verbosity_error()
    warnings.filterwarnings("ignore")

    # Tell HuggingFace where your models are stored on disk.
    # This must be set BEFORE from_model_id() is called, because
    # the transformers library reads this environment variable at
    # the moment it searches for the model files.
    os.environ["HF_HOME"] = HF_CACHE_DIR

    print("  Loading local Qwen2.5-1.5B-Instruct model...")
    print("  (First load takes 20-60 seconds while weights load into RAM)")

    # from_model_id() loads the tokenizer + weights + pipeline in one step.
    # do_sample=False gives greedy decoding — deterministic, consistent output.
    # repetition_penalty discourages the small model from looping on phrases.
    llm = HuggingFacePipeline.from_model_id(
        model_id=LOCAL_MODEL_ID,
        task="text-generation",
        pipeline_kwargs={
            "max_new_tokens": 512,
            "do_sample": False,
            "temperature": None,        # must be None when do_sample=False
            "top_p": None,              # must be None when do_sample=False
            "repetition_penalty": 1.1,
        },
    )

    # ChatHuggingFace wraps the pipeline and applies Qwen's chat template,
    # which formats your system/human messages into the special token
    # structure (<|im_start|>system, <|im_start|>user, etc.) that
    # Qwen2.5-Instruct was trained to expect. Without this, the model
    # would receive a blob of plain text and ignore the system instruction.
    model = ChatHuggingFace(llm=llm)

    return FLOW_PROMPT | model


# ── Dispatcher ────────────────────────────────────────────────────────────────

def _build_chain():
    """
    Single entry point for chain construction. Reads USE_LOCAL_MODEL and
    delegates to the appropriate backend. This is the only place in the
    entire file that knows the flag exists.
    """
    if USE_LOCAL_MODEL:
        print("  [Backend: Local Qwen2.5-1.5B-Instruct]")
        return _build_chain_local()
    else:
        print("  [Backend: Gemini 1.5 Flash via API]")
        return _build_chain_gemini()


# ── Main pipeline function ─────────────────────────────────────────────────────

def explain_flow(
    entry_file: str,
    source_bytes: bytes,
    language: str,
    first_level_deps: list[str],
) -> dict:
    """
    Main function for Phase 3. Calls whichever model backend is active
    and returns a structured result dict. Intentionally model-agnostic —
    it never checks USE_LOCAL_MODEL or imports anything model-specific.
    """
    chain = _build_chain()

    source_code = source_bytes.decode("utf-8", errors="ignore")
    deps_text = (
        "\n".join(f"  - {dep}" for dep in first_level_deps)
        if first_level_deps
        else "  (no local dependencies detected)"
    )

    print(f"  Running inference for '{entry_file}'...")

    response = chain.invoke({
        "entry_file":  entry_file,
        "language":    language,
        "source_code": source_code,
        "deps_text":   deps_text,
    })

    # LangChain returns response.content either as a plain string (older
    # versions) or as a list of content blocks (newer versions, to support
    # multi-modal responses). We handle both so the code is version-resilient.
    content = response.content
    if isinstance(content, list):
        explanation_text = " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        ).strip()
    else:
        explanation_text = content.strip()

    # --- CLEANUP FOR LOCAL HUGGINGFACE MODELS ---
    # The local model returns the entire prompt along with the answer.
    # We slice it down to only what comes after the assistant tag.
    if "<|im_start|>assistant\n" in explanation_text:
        explanation_text = explanation_text.split("<|im_start|>assistant\n")[-1]
    # Remove any trailing End-Of-Turn tokens
    explanation_text = explanation_text.replace("<|im_end|>", "").strip()
    # --------------------------------------------

    return {
        "entry_file":       entry_file,
        "language":         language,
        "explanation":      explanation_text,
        "first_level_deps": first_level_deps,
    }


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    from mock_data.mock_repo import MOCK_REPO_FILES

    backend_label = "Local Qwen2.5-1.5B" if USE_LOCAL_MODEL else "Gemini 1.5 Flash"
    print(f"Testing Phase 3: Flow Explanation via {backend_label}")
    print("=" * 55)

    result = explain_flow(
        entry_file="server.js",
        source_bytes=MOCK_REPO_FILES["server.js"],
        language="javascript",
        first_level_deps=[
            "config/db.config.js",
            "routes/auth.routes.js",
            "routes/user.routes.js",
        ],
    )

    print("\n=== MODEL OUTPUT ===")
    print(result["explanation"])