"""Push prompts to Langfuse prompt management.

Usage:
    python push_prompts.py
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))

from langfuse import Langfuse
from agent.prompts import SYSTEM_PROMPT, PROMPT_NAME


def push():
    lf = Langfuse()
    lf.create_prompt(
        name=PROMPT_NAME,
        prompt=SYSTEM_PROMPT,
        labels=["production"],
        type="text",
    )
    print(f"Prompt '{PROMPT_NAME}' pushed to Langfuse.")

    # Verify it was saved
    p = lf.get_prompt(PROMPT_NAME)
    print(f"Version {p.version} active. Labels: {p.labels}")


if __name__ == "__main__":
    push()
