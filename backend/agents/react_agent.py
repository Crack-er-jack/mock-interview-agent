"""
A custom ReAct (Reasoning and Acting) Agent implementation for educational purposes.

This demonstrates how frameworks like LangChain's `AgentExecutor` actually work under the hood.
Instead of relying on hidden abstractions, we explicitly define:
1. The strict formatting rules (System Prompt).
2. The parsing logic (Regex/String splitting).
3. The execution loop (The While Loop).
"""

import re
from openai import OpenAI
import config
from .tools import TOOLS, TOOL_DESCRIPTIONS

def _get_client() -> OpenAI:
    return OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)

# ---------------------------------------------------------------------------
# 1. THE AGENT PROMPT
# ---------------------------------------------------------------------------
# In LangChain, this is usually hidden inside hub.pull("hwchase17/react").
# Here, we explicitly tell the LLM exactly how it must think and act.
REACT_SYSTEM_PROMPT = f"""
You are an intelligent Assistant tasked with answering questions and solving problems.
You have access to the following tools:

{TOOL_DESCRIPTIONS}

You MUST solve the user's request using the following strict format. Never deviate from this format:

Question: the input question you must answer
Thought: you should always think about what to do next
Action: the action to take, should be exactly one of the tool names: [{', '.join(TOOLS.keys())}]
Action Input: the input to the action (just the raw string of the query)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation cycle can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!
"""

# ---------------------------------------------------------------------------
# 2. THE PARSER
# ---------------------------------------------------------------------------
# In LangChain, this is handled by an `OutputParser` (e.g., ReActSingleInputOutputParser).
# LLMs output raw text. We need to extract the "Action" and "Action Input" strings 
# from the text to actually run our Python functions.
def parse_llm_output(text: str) -> tuple[str, str] | str:
    """
    Parses the LLM output. 
    Returns ('tool_name', 'tool_input') if it wants to act.
    Returns the final answer string if it finishes.
    """
    if "Final Answer:" in text:
        return text.split("Final Answer:")[-1].strip()

    # Look for "Action: <tool_name>" and "Action Input: <input>"
    # This regex is exactly what LangChain uses internally.
    action_match = re.search(r"Action:\s*(.*?)\n", text)
    input_match = re.search(r"Action Input:\s*(.*)", text)

    if action_match and input_match:
        action = action_match.group(1).strip()
        action_input = input_match.group(1).strip()
        return action, action_input
        
    # If the LLM hallucinates or breaks format, we throw an error (LangChain does this too!)
    raise ValueError(f"Could not parse LLM output: {text}")

# ---------------------------------------------------------------------------
# 3. THE AGENT LOOP
# ---------------------------------------------------------------------------
# In LangChain, this is `AgentExecutor.invoke()`. 
# It's literally just a while loop that orchestrates the Prompt -> LLM -> Parser -> Tool -> Prompt cycle.
def run_react_agent(goal: str, max_iterations: int = 5) -> str:
    """
    Runs the ReAct loop to achieve a specific goal.
    """
    client = _get_client()
    
    # We maintain a running scratchpad of everything that has happened so far.
    # In LangChain, this is the `agent_scratchpad` variable.
    prompt = REACT_SYSTEM_PROMPT + f"\nQuestion: {goal}\n"
    
    print("\n" + "="*50)
    print(f"🤖 STARTING AGENT LOOP FOR GOAL: {goal}")
    print("="*50 + "\n")

    for i in range(max_iterations):
        print(f"\n--- Iteration {i+1} ---")
        
        # Step 1: Query the LLM
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0, # 0.0 is crucial for agents so they stick strictly to the formatting rules
            stop=["Observation:"] # LangChain TRICK: We force the LLM to stop generating text as soon as it types "Observation:". That way, it doesn't hallucinate the tool's result! Our Python code will supply the true Observation.
        )
        
        llm_response = response.choices[0].message.content.strip()
        print(f"LLM Response:\n{llm_response}\n")
        
        # Add the LLM's thought process to our running prompt
        prompt += llm_response + "\n"
        
        # Step 2: Parse the output to decide what to do
        try:
            parsed = parse_llm_output(llm_response)
        except ValueError as e:
            print(f"Parsing error: {e}. Telling the LLM to fix it.")
            prompt += "Observation: Invalid format. Please provide an Action and Action Input, or a Final Answer.\n"
            continue
            
        # Step 3A: If it's a string, it's the Final Answer! We break the loop.
        if isinstance(parsed, str):
            print("🏁 AGENT FINISHED!")
            return parsed
            
        # Step 3B: If it's a tuple, it wants to use a tool.
        action, action_input = parsed
        print(f"🛠️ Agent requested tool: '{action}' with input: '{action_input}'")
        
        if action in TOOLS:
            # Actually execute the Python function
            tool_func = TOOLS[action]
            try:
                observation = tool_func(action_input)
            except Exception as e:
                observation = f"Error executing tool: {e}"
        else:
            observation = f"Tool '{action}' not found."
            
        print(f"👁️ Observation:\n{observation}")
        
        # Add the true observation back into the prompt so the LLM sees it on the next iteration.
        prompt += f"Observation: {observation}\n"
        
    return "Agent failed to finish within max iterations."
