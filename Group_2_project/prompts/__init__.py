"""
prompts/
========
Separated prompt templates for each agent.

WHY PROMPTS ARE IN THEIR OWN PACKAGE:
    1. Prompts are the #1 thing you'll iterate on. Keeping them separate
       means you can tweak agent behavior without touching logic code.
    2. Version control — you can see prompt changes in git diffs cleanly.
    3. Testing — you can unit-test prompts independently of agent logic.
    4. Collaboration — prompt engineers and Python devs work on different files.

Each module exports two constants:
    SYSTEM_PROMPT  — The agent's persona and instructions.
    USER_PROMPT_TEMPLATE — A format string with {placeholders} for runtime data.
"""
