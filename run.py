"""
run.py — Entry point for the CV Tailoring Agent demo.

Usage:
    python run.py                          # agent mode (default)
    python run.py --mode chatbot           # chatbot baseline
    python run.py --cv data/Dev-Raj-Resume.pdf --jd data/jds/jd_recruitment_officer_final.pdf
"""
import os
import sys
import argparse
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(): pass

load_dotenv()

PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(str(PROJECT_ROOT))

from src.core.openrouter_provider import OpenRouterProvider
from src.tools._session import session
from src.tools.cv_extractor import cv_extractor_tool
from src.tools.jd_tool import jd_tool
from src.tools.section_drafter import section_drafter_tool
from src.tools.ats_validator import ats_validator_tool
from src.agent.agent import ReActAgent
from src.chatbot import Chatbot


CV_PATH = PROJECT_ROOT / "data" / "Dev-Raj-Resume.pdf"
JD_PATH = PROJECT_ROOT / "data" / "jds" / "jd_recruitment_officer_final.pdf"
MODEL   = os.getenv("OPENROUTER_MODEL", "qwen/qwen3.6-plus:free")


def run_agent(cv_path: str, jd_path: str):
    print(f"\n{'='*60}")
    print("MODE: ReAct Agent")
    print(f"CV : {cv_path}")
    print(f"JD : {jd_path}")
    print('='*60)

    llm = OpenRouterProvider(model_name=MODEL)
    session.llm = llm

    tools  = [cv_extractor_tool, jd_tool, section_drafter_tool, ats_validator_tool]
    agent  = ReActAgent(llm=llm, tools=tools, max_steps=8)

    task = f"""Tailor the candidate's CV for the target job.

CV file : {cv_path}
JD file : {jd_path}

Follow these steps in order:
1. Call extract_cv({cv_path}) to load the candidate's CV.
2. Call extract_jd({jd_path}) to load the job requirements.
3. Call draft_section(experience) to rewrite the Work Experience section.
4. Call validate_ats() to score the tailored CV.
5. If ATS score >= 80 and no missing keywords, give Final Answer with the tailored experience text.
   Otherwise call draft_section(experience) again to improve, then validate_ats() once more.
"""

    result = agent.run(task)
    print("\nFINAL ANSWER:")
    print(result)
    return result


def run_chatbot(cv_path: str, jd_path: str):
    print(f"\n{'='*60}")
    print("MODE: Chatbot Baseline")
    print('='*60)

    llm  = OpenRouterProvider(model_name=MODEL)
    bot  = Chatbot(llm)

    question = (
        f"I am a candidate whose CV is at '{cv_path}'. "
        f"The job description is in the file '{jd_path}'. "
        "Without any tools, give me your best advice on how to tailor my Work Experience section "
        "for this job, and estimate whether my CV would pass an ATS filter."
    )

    print(f"\nUSER: {question}\n")
    response = bot.chat(question)
    print(f"CHATBOT:\n{response}")
    return response


def main():
    parser = argparse.ArgumentParser(description="CV Tailoring Agent")
    parser.add_argument("--mode", choices=["agent", "chatbot"], default="agent")
    parser.add_argument("--cv",  default=str(CV_PATH))
    parser.add_argument("--jd",  default=str(JD_PATH))
    args = parser.parse_args()

    if args.mode == "agent":
        run_agent(args.cv, args.jd)
    else:
        run_chatbot(args.cv, args.jd)


if __name__ == "__main__":
    main()
