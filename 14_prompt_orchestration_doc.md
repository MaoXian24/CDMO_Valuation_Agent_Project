# Prompt and Orchestration Document (Template)

## Agent Roles
- A1 Data Intake
- A2 Financial Analysis
- A3 Valuation
- A4 Report Writer
- Orchestrator

## Prompt Design
- Use the templates in 03_prompts.
- Emphasize CDMO industry specificity.

## Workflow Logic
- Sequential calls: A1 -> A2 -> A3 -> A4.
- Human-in-the-loop confirmation before final DCF.

## Tools Used
- Python tool for data and valuation.
- Knowledge base for CDMO reports.
- Optional chart tool.

## Interaction Design
- Ask for assumptions clearly.
- Provide default suggestions.

## Exported Workflow File
- Save the exported workflow or screenshots in 02_agents.

