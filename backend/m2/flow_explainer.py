"""M2 execution-flow explanation with Claude primary and local/Gemini fallback."""

import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from ai.claude import generate as generate_claude, is_configured as claude_configured

load_dotenv()

USE_LOCAL_MODEL = False
LOCAL_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
HF_CACHE_DIR = "D:/Huggingface_cache"

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
{source_code}

=== DIRECT DEPENDENCIES ===
{deps_text}

Describe what happens when this application starts up, step by step.
Focus on what gets loaded, connected, registered, and what starts listening or running.

Produce EXACTLY this format, with no extra commentary:

Entry Point: {entry_file}
Execution Flow:
  {entry_file} <first thing it does>
  → <second step>
  → <third step>
  → <continue for each meaningful startup action>"""
    )
])


def _build_chain_gemini():
    from langchain_google_genai import ChatGoogleGenerativeAI
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY not found")
    model = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=api_key,
        temperature=0.2,
    )
    return FLOW_PROMPT | model


def _build_chain_local():
    from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
    import transformers
    import warnings
    transformers.logging.set_verbosity_error()
    warnings.filterwarnings("ignore")
    os.environ["HF_HOME"] = HF_CACHE_DIR
    llm = HuggingFacePipeline.from_model_id(
        model_id=LOCAL_MODEL_ID,
        task="text-generation",
        pipeline_kwargs={
            "max_new_tokens": 512,
            "do_sample": False,
            "temperature": None,
            "top_p": None,
            "repetition_penalty": 1.1,
        },
    )
    return FLOW_PROMPT | ChatHuggingFace(llm=llm)


def _build_chain():
    if USE_LOCAL_MODEL:
        print("  [Backend: Local Qwen2.5-1.5B-Instruct]")
        return _build_chain_local()
    print("  [Fallback backend: Gemini via API]")
    return _build_chain_gemini()


def _clean_content(content) -> str:
    if isinstance(content, list):
        text = " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        ).strip()
    else:
        text = str(content).strip()
    if "<|im_start|>assistant\n" in text:
        text = text.split("<|im_start|>assistant\n")[-1]
    return text.replace("<|im_end|>", "").strip()


def explain_flow(
    entry_file: str,
    source_bytes: bytes,
    language: str,
    first_level_deps: list[str],
) -> dict:
    source_code = source_bytes.decode("utf-8", errors="ignore")
    deps_text = (
        "\n".join(f"  - {dep}" for dep in first_level_deps)
        if first_level_deps
        else "  (no local dependencies detected)"
    )

    print(f"  Running inference for '{entry_file}'...")

    if claude_configured():
        system_prompt = (
            "You are a senior software architect helping a new developer "
            "understand an unfamiliar codebase. Be concise, precise, and "
            "focus on high-level startup behaviour rather than implementation details."
        )
        user_prompt = f"""Analyse the entry point file of a {language} project and
describe its execution flow in plain English.

=== ENTRY POINT FILE ===
Filename: {entry_file}

Source code:
{source_code}

=== DIRECT DEPENDENCIES ===
{deps_text}

Describe what happens when this application starts up, step by step.
Focus on what gets loaded, connected, registered, and what starts listening or running.

Produce EXACTLY this format, with no extra commentary:

Entry Point: {entry_file}
Execution Flow:
  {entry_file} <first thing it does>
  → <second step>
  → <third step>
  → <continue for each meaningful startup action>"""
        explanation_text = generate_claude(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=700,
        )
    else:
        chain = _build_chain()
        response = chain.invoke({
            "entry_file": entry_file,
            "language": language,
            "source_code": source_code,
            "deps_text": deps_text,
        })
        explanation_text = _clean_content(response.content)

    return {
        "entry_file": entry_file,
        "language": language,
        "explanation": explanation_text,
        "first_level_deps": first_level_deps,
    }


if __name__ == "__main__":
    print("M2 flow explainer ready. Configure ANTHROPIC_API_KEY for Claude.")
