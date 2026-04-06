# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: []
- **Student ID**: []
- **Date**: [Date Here]

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: [e.g., `src/tools/search_tool.py`]
- **Code Highlights**: [Copy snippets or link file lines]
- **Documentation**: [Brief explanation of how your code interacts with the ReAct loop]

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: [e.g., Agent caught in an infinite loop with `Action: search(None)`]
- **Log Source**: [Link or snippet from `logs/YYYY-MM-DD.log`]
- **Diagnosis**: [Why did the LLM do this? Was it the prompt, the model, or the tool spec?]
- **Solution**: [How did you fix it? (e.g., updated `Thought` examples in the system prompt)]

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: How did the `Thought` block help the agent compared to a direct Chatbot answer?
2.  **Reliability**: In which cases did the Agent actually perform *worse* than the Chatbot?
3.  **Observation**: How did the environment feedback (observations) influence the next steps?

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: [e.g., Use an asynchronous queue for tool calls]
- **Safety**: [e.g., Implement a 'Supervisor' LLM to audit the agent's actions]
- **Performance**: [e.g., Vector DB for tool retrieval in a many-tool system]

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
