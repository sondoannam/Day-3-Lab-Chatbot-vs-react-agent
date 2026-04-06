import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.openrouter_provider import OpenRouterProvider
from src.agent.agent import ReActAgent
from src.tools.cv_extractor import cv_extractor_tool

CV_PATH = "data/Dev-Raj-Resume.pdf"

def main():
    llm = OpenRouterProvider()

    agent = ReActAgent(
        llm=llm,
        tools=[cv_extractor_tool],
        max_steps=5,
    )

    prompt = (
        f"Extract all information from the CV located at '{CV_PATH}'. "
        "Then summarize the candidate's key skills, work experience, and education."
    )

    print("Running agent...\n")
    answer = agent.run(prompt)

    print("\n===== RESULT =====")
    print(answer)


if __name__ == "__main__":
    main()