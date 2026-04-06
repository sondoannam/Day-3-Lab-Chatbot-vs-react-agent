"""
Chatbot Baseline — simple multi-turn LLM chatbot, no tools, no reasoning loop.
Used as a performance/quality baseline to compare against the ReAct agent.
"""

from typing import List, Dict
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

SYSTEM_PROMPT = """You are a professional CV tailoring assistant.
Help users optimize their CV for specific job descriptions.
Answer directly based on your knowledge — you have no access to external tools.
"""


class Chatbot:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.history: List[Dict[str, str]] = []

    def chat(self, user_input: str) -> str:
        logger.log_event("CHATBOT_INPUT", {"input": user_input, "model": self.llm.model_name})

        # Build conversation context as a single prompt
        context = "\n".join(
            f"{msg['role'].upper()}: {msg['content']}" for msg in self.history
        )
        prompt = f"{context}\nUSER: {user_input}\nASSISTANT:" if context else user_input

        result = self.llm.generate(prompt, system_prompt=SYSTEM_PROMPT)
        response = result["content"].strip()

        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": response})

        logger.log_event("CHATBOT_OUTPUT", {
            "response": response[:200],
            "tokens": result["usage"],
            "latency_ms": result["latency_ms"],
        })

        return response

    def reset(self):
        self.history = []
