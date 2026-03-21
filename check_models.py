import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

print("Models available for your API key that support text generation:\n")

for model in genai.list_models():
    # We filter for generateContent because that's what LangChain uses
    # under the hood — other methods like embedContent or countTokens
    # are irrelevant for our LLM call use case
    if "generateContent" in model.supported_generation_methods:
        print(f"  Name:         {model.name}")
        print(f"  Display name: {model.display_name}")
        print(f"  Description:  {model.description[:80]}...")
        print()
