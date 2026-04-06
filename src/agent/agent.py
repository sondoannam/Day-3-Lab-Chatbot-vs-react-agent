import re
from typing import List, Dict, Any, Optional

from pydantic import BaseModel

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

        try:
            from src.tools._session import session

            session.llm = llm
        except ImportError:
            pass

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )
        return f"""You are a CV tailoring assistant with access to tools. You MUST use tools to complete any task — never answer from memory or make up content.

AVAILABLE TOOLS:
{tool_descriptions}

STRICT FORMAT — follow exactly on every response:
Thought: <your reasoning about what to do next>
Action: <tool_name>(<argument>)

Wait for the Observation before continuing.
After receiving Observations from ALL required tools, you may write:
Final Answer: <your response based only on tool Observations>

RULES:
- You MUST call extract_cv and extract_jd before draft_section or validate_ats.
- NEVER write Final Answer before calling all required tools.
- NEVER invent company names, dates, or skills not seen in Observations.
- One Action per response, then stop and wait."""

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
        Each tool function receives a single string argument.

        For complex dict results (e.g. CandidateMasterCV from extract_cv):
        - Store full data in session.cv_data
        - Return a concise human-readable summary to the LLM
        """
        for tool in self.tools:
            if tool["name"] == tool_name:
                try:
                    result = tool["function"](args)

                    if isinstance(result, BaseModel):
                        return result.model_dump_json(indent=2)

                    if isinstance(result, dict):
                        if result.get("error"):
                            return f"Error: {result['error']}"

                        try:
                            from src.tools._session import session

                            session.set_cv_data(result)
                        except ImportError:
                            pass

                        return self._summarize_cv_dict(result)

                    return str(result)

                except Exception as e:
                    logger.log_event("TOOL_ERROR", {"tool": tool_name, "error": str(e)})
                    return f"Tool '{tool_name}' raised an error: {e}"

        return f"Tool '{tool_name}' not found."

    @staticmethod
    def _summarize_cv_dict(cv: dict) -> str:
        """Return a short observation the LLM can reason about."""
        contact = cv.get("contact", {})
        name    = contact.get("full_name", "Unknown")
        skills  = [s["name"] for s in cv.get("skills", [])][:8]
        exps    = cv.get("work_experience", [])
        roles   = [f"{e['job_title']} @ {e['company_name']}" for e in exps]
        edu     = [e.get("institution", "") for e in cv.get("education", [])]
        warns   = [w for w in cv.get("metadata", {}).get("warnings", []) if "page" not in w]

        lines = [
            f"CV extracted: {name}",
            f"Skills ({len(cv.get('skills', []))} total): {', '.join(skills)}" + ("..." if len(cv.get("skills", [])) > 8 else ""),
            f"Work history ({len(exps)} roles): {';'.join(roles)}",
            f"Education: {';'.join(edu) or 'N/A'}",
        ]
        if warns:
            lines.append(f"Warnings: {';'.join(warns)}")
        return "\n".join(lines)