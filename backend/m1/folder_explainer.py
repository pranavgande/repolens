"""M1 folder descriptions with Claude primary and local/Gemini fallback."""

import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from ai.claude import generate as generate_claude, is_configured as claude_configured
from ai.fallback import folder_description as generate_fallback_folder

load_dotenv()

USE_LOCAL_MODEL = False
LOCAL_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
HF_CACHE_DIR = "D:/Huggingface_cache"

FOLDER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a senior software architect reviewing an unfamiliar codebase. "
        "Write clear, concise folder descriptions that help a new developer "
        "understand the project structure at a glance. Always respond with exactly "
        "one sentence. Never use bullet points. Never start with 'This folder'."
    ),
    (
        "human",
        """A software project written in {language} has a folder called '{folder_name}'.

The files inside this folder are:
{file_list}

The detected project architecture is: {architecture_hint}

In exactly one sentence, describe what role this folder plays in the project.
Do not mention specific filenames. Focus on purpose and responsibility."""
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
        temperature=0,
    )
    return FOLDER_PROMPT | model


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
            "max_new_tokens": 100,
            "do_sample": False,
            "temperature": None,
            "top_p": None,
            "repetition_penalty": 1.1,
        },
    )
    return FOLDER_PROMPT | ChatHuggingFace(llm=llm)


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
    return text.replace("<|im_end|>", "").strip().strip('"').strip("'").strip()


def explain_folder(
    folder_name: str,
    files_inside: list[str],
    language: str = "javascript",
    architecture_hint: str = "Unknown",
) -> str:
    sample_files = files_inside[:10]
    file_list = "\n".join(f"  - {name}" for name in sample_files)
    if len(files_inside) > 10:
        file_list += f"\n  ... and {len(files_inside) - 10} more files"

    print(f"  Calling LLM for unrecognised folder: '{folder_name}'...")

    if claude_configured():
        system_prompt = (
            "You are a senior software architect reviewing an unfamiliar codebase. "
            "Write a clear, concise folder description. Respond with exactly one "
            "sentence, never use bullet points, and never start with 'This folder'."
        )
        user_prompt = f"""A {language} software project has a folder called '{folder_name}'.

Files inside:
{file_list}

Detected architecture: {architecture_hint}

Describe the folder's role in exactly one sentence. Do not mention specific filenames."""
        return _clean_content(generate_claude(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=120,
        ))

    if os.environ.get("GEMINI_API_KEY") or USE_LOCAL_MODEL:
        chain = _build_chain()
        response = chain.invoke({
            "folder_name": folder_name,
            "file_list": file_list,
            "language": language,
            "architecture_hint": architecture_hint,
        })
        return _clean_content(response.content)

    print("  No external AI key configured — using deterministic M1 fallback")
    return generate_fallback_folder(folder_name, files_inside, language)


if __name__ == "__main__":
    print("M1 folder explainer ready. Configure ANTHROPIC_API_KEY for Claude.")
