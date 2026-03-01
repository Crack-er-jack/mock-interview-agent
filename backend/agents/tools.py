"""
Tools for the ReAct Agent.
In LangChain, you'd use the `@tool` decorator. Here, we just define normal Python functions
and manually describe them to the agent.
"""
import json
import os

def search_problem_db(query: str) -> str:
    """
    Searches the mock database of problems for a given difficulty or tag.
    Returns a string representation of the matching problems.
    """
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "problems.json")
    
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            problems = json.load(f)
    except FileNotFoundError:
        return "Error: Database not found."
        
    query = query.lower().strip()
    results = []
    
    for p in problems:
        # Simple search across title, difficulty, or tags
        if query in p["difficulty"].lower() or any(query == tag.lower() for tag in p["tags"]):
            results.append(
                f"Title: {p['title']} (Difficulty: {p['difficulty']})\n"
                f"Description: {p['description']}\n"
                f"Ideal Solution: {p['ideal_solution']}\n"
            )
            
    if not results:
        return f"No problems found matching query: '{query}'"
        
    return "Found the following problems:\n\n" + "\n---\n".join(results)

# In a real agent framework (like LangChain), the framework uses introspection or schemas 
# to automatically generate these descriptions for the LLM. We do it manually here.
TOOLS = {
    "search_problem_db": search_problem_db
}

# This is what we inject into the system prompt so the LLM knows what hands it has.
TOOL_DESCRIPTIONS = """
1. search_problem_db(query: str)
   - Use this to find coding problems. 
   - 'query' should be a difficulty level (e.g., "easy", "medium", "hard") or a topic tag (e.g., "arrays", "graphs", "sorting").
   - Returns details about matching problems.
"""
