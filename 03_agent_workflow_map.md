# Agent, Plugin, Chatflow, and Workflow Map

This project is not "four Python tools only". The correct structure is:
- Agent: the role and reasoning layer
- Plugin: the callable function or tool the agent can use
- Chatflow: the user interaction path inside one agent
- Workflow: the multi-agent orchestration across the whole product

## 1. Main Architecture
- Main Agent: CDMO Orchestrator
- Sub-Agents:
  - A1 Data Intake and Cleaning Agent
  - A2 Financial Analysis Agent
  - A3 Valuation and Assumptions Agent
  - A4 Report and Visualization Agent
- Plugins:
  - WRDS financial statement plugin
  - Forecast plugin
  - Beta plugin
  - DCF plugin
  - Knowledge base plugin
  - Chart export plugin if the platform provides one

## 2. What the Python Code Is
The Python source files are the implementation of the plugins, not the whole agent.
Each plugin is one callable capability that the agent can invoke inside a chatflow or workflow.

## 3. Chatflow Design by Agent
### A1 Data Intake and Cleaning Agent
- Chatflow role: ask for WRDS username, ticker, year range, and password
- Plugin call: WRDS financial statement plugin
- Output: cleaned tables and data notes

### A2 Financial Analysis Agent
- Chatflow role: explain ratios, trends, and peer differences
- Plugin call: Python analysis and chart generation in the report step
- Output: ratio tables, benchmark notes, and figures

### A3 Valuation and Assumptions Agent
- Chatflow role: collect human assumptions before DCF
- Plugin calls: forecast plugin, beta plugin, DCF plugin
- Output: assumptions, valuation table, scenario summary

### A4 Report and Visualization Agent
- Chatflow role: turn analysis into analyst-style narrative
- Plugin calls: chart references and output pack assembly
- Output: industry overview, company analysis, valuation summary, risks, and final package

## 4. Workflow Design Across Agents
Recommended workflow:
1) User enters company and peer info
2) A1 cleans data
3) A2 performs analysis
4) A3 asks for forecast assumptions and runs DCF
5) A4 writes the final report
6) Orchestrator assembles the downloadable output pack
7) Optional export/download branch runs after the core valuation flow finishes

## 5. What to Copy Where
- Paste the Python code into the matching Coze Python tool
- Paste the prompt text into the matching agent system prompt
- Use the workflow builder to connect A1 -> A2 -> A3 -> A4
- Upload the reference PDFs to the knowledge base
- Use the test input txt files to run end-to-end checks
- Keep export/download as a separate terminal branch so it does not affect valuation logic

## 6. Why This Matters
This structure matches the course language better:
- agent = role + reasoning
- plugin = function/tool
- chatflow = in-agent interaction path
- workflow = multi-agent orchestration

