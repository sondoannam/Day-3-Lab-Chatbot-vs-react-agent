import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )
        return f"""
        You are an intelligent assistant. You have access to the following tools:
        {tool_descriptions}

        Use the following format strictly:
        Thought: your line of reasoning.
        Action: tool_name(argument)
        Observation: result of the tool call.
        ... (repeat Thought/Action/Observation if needed)
        Final Answer: your final response.

        Only call one tool at a time. Do not make up tool names.
        """

    def _parse_thought(self, text: str) -> Optional[str]:
        match = re.search(r"Thought:\s*(.+?)(?=\nAction:|\nFinal Answer:|$)", text, re.DOTALL)
        return match.group(1).strip() if match else None

    def _parse_action(self, text: str) -> Optional[tuple[str, str]]:
        match = re.search(r"Action:\s*(\w+)\(([^)]*)\)", text)
        if match:
            tool_name = match.group(1).strip()
            args = match.group(2).strip().strip("'\"")  # strip quotes
            return tool_name, args
        return None

    def _parse_final_answer(self, text: str) -> Optional[str]:
        match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
        return match.group(1).strip() if match else None

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        current_prompt = user_input
        steps = 0

        while steps < self.max_steps:

            # ── Step 1: Call the LLM ──────────────────────────────────
            result = self.llm.generate(
                current_prompt,
                system_prompt=self.get_system_prompt()
            )
            response_text = result["content"]

            logger.log_event("LLM_RESPONSE", {
                "step": steps,
                "usage": result.get("usage"),
                "latency_ms": result.get("latency_ms"),
            })

            # ── Step 1: Parse Thought ─────────────────────────────────
            thought = self._parse_thought(response_text)
            if thought:
                logger.log_event("THOUGHT", {"step": steps, "thought": thought})

            # ── Step 1: Check for Final Answer first ──────────────────
            final_answer = self._parse_final_answer(response_text)
            if final_answer:
                logger.log_event("FINAL_ANSWER", {"step": steps, "answer": final_answer})
                logger.log_event("AGENT_END", {"steps": steps + 1})
                return final_answer

            # ── Step 1: Parse Action ──────────────────────────────────
            action = self._parse_action(response_text)

            if action:
                tool_name, args = action
                logger.log_event("ACTION", {"step": steps, "tool": tool_name, "args": args})

                # ── Step 2: Execute tool ──────────────────────────────
                observation = self._execute_tool(tool_name, args)

                # Append Observation and continue the loop
                current_prompt = (
                    f"{current_prompt}\n"
                    f"Thought: {thought}\n"
                    f"Action: {tool_name}({args})\n"
                    f"Observation: {observation}\n"
                )
            else:
                current_prompt = f"{current_prompt}\n{response_text}\n"

            steps += 1

        logger.log_event("AGENT_END", {"steps": steps})
        return "Max steps reached without a Final Answer."

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Finds the tool by name and calls its function with args.
        Each tool function receives a single string argument
        (the agent formats it that way via Action: tool_name(arg)).
        """
        for tool in self.tools:
            if tool["name"] == tool_name:
                try:
                    result = tool["function"](args)

                    # If the tool returns a dict (like extract_cv does),
                    # surface the error or return the content
                    if isinstance(result, dict):
                        if result.get("error"):
                            return f"Error: {result['error']}"
                        return result.get("content") or str(result)

                    return str(result)

                except Exception as e:
                    logger.log_event("TOOL_ERROR", {"tool": tool_name, "error": str(e)})
                    return f"Tool '{tool_name}' raised an error: {e}"

        return f"Tool '{tool_name}' not found."