# Agentic Calculation Protocol
## Integrating LLM Logic with Deterministic Python Tools

This document details the architecture and communication flow between the **RAG Agent** (Intelligence), the **Router** (Control), and the **Calculation Layer** (Execution). It is designed to allow you to extend the system with new tools and calculators.

---

## 1. High-Level Architecture

The system follows a **Router-Tool Pattern**. It does not allow the AI to run Python code arbitrarily. Instead, it uses a strict permission flow:

1.  **Router:** Scans user input for specific "Trigger Keywords" to determine INTENT.
2.  **Permission:** If INTENT = `calc`, the system *injects* the Tool Definitions into the LLM's context.
3.  **Bridge:** The LLM uses its reasoning to structure a **JSON Tool Call** instead of text.
4.  **Execution:** The Python runtime intercepts this JSON, runs the `calc_tools.py` function, and feeds the result back to the LLM.

---

## 2. Step-by-Step Communication Flow

### Step A: The Trigger (Router)
**Location:** `rag_agent.py` -> `detect_intent()`

The system first decides *if* the calculation layer is needed. This prevents the LLM from trying to do math on simple text queries.

*   **Logic:** Checks for keywords in the user query.
*   **Current Triggers:** `["calculate", "demand", "load", "how many", "size of", "va", "watts"]`
*   **Result:** Sets `intent = "calc"`.

### Step B: The Permission (Tool Injection)
**Location:** `rag_agent.py` -> `query()`

If `intent == "calc"`, we pass a **Tool Schema** to the OpenAI API. This tells the LLM: *"You have a calculator available. Here is how to use it."*

```json
// The Schema sent to the LLM
{
  "name": "perform_calculation",
  "description": "Performs mathematical calculations...",
  "parameters": {
    "expression": "The math string (e.g. '50 * 180')",
    "source_citation": "NEC 220.14(I)"
  }
}
```

### Step C: The Bridge (LLM Reasoning)
**Location:** OpenAI API (Cloud)

The LLM receives:
1.  User Question: *"Demand for 50 receptacles?"*
2.  Retrieved Context: *"NEC 220.14(I) states 180 VA per yoke."*
3.  Tool Definition: `perform_calculation(expression)`

The LLM "thinks": *I need to multiply 50 by 180. I will call the tool.*
**Output:** It generates a structured request, not text:
`CALL: perform_calculation(expression="50 * 180")`

### Step D: The Execution (Python Runtime)
**Location:** `rag_agent.py` (Event Loop) -> `calc_tools.py`

The script detects the Tool Call request and hands it off to the safe calculator.

1.  **Intercept:** `if tool_call.function.name == "perform_calculation":`
2.  **Hand-off:** Calls `self.calculator.evaluate_expression("50 * 180")`
3.  **Safety Check:** `calc_tools.py` strips units ("VA") and uses `simpleeval` to ensure no malicious code runs.
4.  **Return:** Python returns `{"result": 9000, "unit": "VA"}`.

### Step E: The Synthesis (Final Answer)
The result is sent back to the LLM as a "Tool Output" message. The LLM now acts as a translator, converting the raw number into the **Guidance** format:

> "Using the value of 180 VA from NEC 220.14, the total is 9,000 VA."

---

## 3. How to Extend This System

To add new capabilities (e.g., a "Voltage Drop Calculator"), follow this pattern:

### 1. Update the Router
Add new keywords to `detect_intent` in `rag_agent.py`:
```python
calc_triggers.append("voltage drop")
```

### 2. Define the Tool Logic
Add the logic to `execution/calc_tools.py`:
```python
def calculate_voltage_drop(self, amps, dist, wire_size):
    # Deterministic physics formula
    return (2 * 12.9 * dist * amps) / get_cmil(wire_size)
```

### 3. Register the Tool
Update the tool definition list in `rag_agent.py`:
```python
tools = [
    {
        "name": "calc_voltage_drop",
        "description": "Calculates voltage drop...",
        "parameters": { "amps": ..., "distance": ... }
    }
]
```

### 4. Handle Execution
Add the handler in the `query` loop:
```python
if tool_name == "calc_voltage_drop":
    result = self.calculator.calculate_voltage_drop(...)
```
