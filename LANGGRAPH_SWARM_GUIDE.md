# LangGraph Swarm - Key Concepts Summary

## 1. AGENT BASICS

**Creating Agents:**
- Use `create_react_agent(model, tools, prompt, name)`
- Name must be unique and match handoff tool references
- Each agent is a specialized component in your swarm

**System Prompts:**
- Simple string: `prompt="You are a sales assistant"`
- Dynamic callable: `prompt=my_function` where function has signature `(state: dict, config: RunnableConfig) -> list`
- Callable gives you access to state for context injection
- NO JANKY PROMPTS NEEDED - can be clean and simple

---

## 2. TOOLS AND STATE MODIFICATION

**Creating Tools:**
- Regular Python functions with docstrings
- Docstring becomes the tool description for the LLM
- Parameters in the function signature = what LLM provides

**State Injection (THE MAGIC):**
```python
@tool
def add_to_order(
    item_name: str,           # LLM provides
    quantity: int,            # LLM provides
    state: Annotated[dict, InjectedState]  # Auto-injected!
) -> dict:
    # Return dictionary to update state
    return {
        "order_items": current_items + [new_item],
        "order_total": new_total
    }
```

**Key Points:**
- `InjectedState` parameters are INVISIBLE to the LLM
- LLM never has to provide or see the full state
- Saves tokens, prevents hallucination
- Return a dict = state update
- Can also return `Command` for more control

**Other Injectable Parameters:**
- `state: Annotated[dict, InjectedState]` - current graph state
- `config: RunnableConfig` - runtime config (user_id, etc.)
- `tool_call_id: Annotated[str, InjectedToolCallId]` - tool call ID
- `store: Annotated[BaseStore, InjectedStore]` - long-term memory

---

## 3. CUSTOM STATE SCHEMA

**Extend SwarmState:**
```python
class OrderState(SwarmState):
    order_items: list[dict] = []
    order_total: float = 0.0
    customer_name: str = ""

# Use when creating swarm
builder = create_swarm(
    [agent1, agent2],
    default_active_agent="agent1",
    state_schema=OrderState  # Your custom state
)
```

**Two Approaches for State:**
- Option A: External state (global vars, databases) - simple
- Option B: Graph state (custom StateSchema) - more structured

---

## 4. CONTEXT AND PROMPTS

**The Callable Pattern:**
```python
def build_prompt(base_prompt: str, context_reducer):
    def prompt_function(state: dict, config: RunnableConfig) -> list:
        context = context_reducer(state, config)
        full_prompt = f"{base_prompt}\n\nCONTEXT:\n{context}"
        return [{"role": "system", "content": full_prompt}] + state["messages"]
    return prompt_function
```

**Context Reducers:**
- Functions that format state into readable context strings
- Reusable across multiple agents
- Each agent can see different parts of state
- Keeps prompts clean and composable

**Why Return List of Messages:**
- String prompt: Just system message, framework appends conversation
- Callable: Full control over what agent sees
- Can filter messages, limit history, transform content, hide tool calls
- Return format: `[{system_msg}, ...conversation_history]`

---

## 5. HANDOFF TOOLS

**Creating Handoffs:**
```python
transfer_to_checkout = create_handoff_tool(
    agent_name="checkout_agent",  # Must match agent name
    description="Transfer to checkout agent when ready to finalize"
)
```

**How It Works:**
- Handoff tools define the edges in your swarm
- When agent calls handoff tool, control transfers to that agent
- Updates `active_agent` in state
- System remembers which agent was last active
- Next user message goes to that agent

**Graph Edges:**
- YES - edges are defined purely by handoff tools
- No need to manually define edges
- Swarm automatically discovers connections from tools

---

## 6. HUMAN-IN-THE-LOOP

**Agents Can Ask Questions:**
- NO SPECIAL TOOL NEEDED
- Agents just respond with text asking questions
- Natural conversation flow
- Guide behavior with system prompts

**Example Prompt:**
```
You are a sales assistant.

When you need information:
1. Ask clear, specific questions
2. Wait for user response before taking action
3. Don't assume - always confirm

Example: "What size would you like - small, medium, or large?"
```

**Creating Internal Agents:**
- Use prompt: "You do NOT interact with users. Transfer to customer_service_agent if you need user input"
- Filter user messages in prompt callable
- They can still call tools and process data

---

## 7. MULTI-TURN CONVERSATIONS & CHECKPOINTER

**In LangGraph Studio UI:**
- Checkpointer provided automatically by dev server
- Multi-turn works out of the box
- Each browser session = one thread

**In Python Code:**
```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
app = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "123"}}
result1 = app.invoke({"messages": [...]}, config)
result2 = app.invoke({"messages": [...]}, config)  # Same thread!
```

**Without Checkpointer:**
- Each invoke() is isolated
- No memory between calls
- Swarm forgets active agent
- Conversation history lost

**With Checkpointer:**
- State persists between turns
- Remembers active agent
- Maintains conversation history
- Enables true multi-turn conversations

---

## 8. ENVIRONMENT SETUP (Windows)

**Setting API Keys (Command Prompt):**
```cmd
set OPENAI_API_KEY=your-key-here
echo %OPENAI_API_KEY%  # Verify
```

**Running the Dev Server:**
```cmd
cd examples\customer_support
uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev
```

---

## 9. COMPLETE EXAMPLE PATTERN

```python
from langgraph_swarm import SwarmState, create_swarm, create_handoff_tool
from langgraph.prebuilt import create_react_agent, InjectedState
from langchain_openai import ChatOpenAI

# 1. Define custom state
class OrderState(SwarmState):
    order_items: list[dict] = []
    order_total: float = 0.0

# 2. Create tools with state injection
@tool
def add_to_order(item: str, price: float, state: Annotated[dict, InjectedState]) -> dict:
    items = state.get("order_items", [])
    return {
        "order_items": items + [{"item": item, "price": price}],
        "order_total": state.get("order_total", 0) + price
    }

# 3. Create context reducer
def order_context_reducer(state: dict, config: RunnableConfig) -> str:
    items = state.get("order_items", [])
    total = state.get("order_total", 0)
    return f"Current Order: {len(items)} items, ${total:.2f}"

# 4. Build prompt helper
def build_prompt(base_prompt: str, reducer):
    def prompt_fn(state: dict, config: RunnableConfig) -> list:
        context = reducer(state, config)
        return [
            {"role": "system", "content": f"{base_prompt}\n\n{context}"}
        ] + state["messages"]
    return prompt_fn

# 5. Create agents
model = ChatOpenAI(model="gpt-4o")

sales_agent = create_react_agent(
    model,
    tools=[add_to_order, create_handoff_tool("checkout_agent")],
    prompt=build_prompt("You are a sales assistant", order_context_reducer),
    name="sales_agent"
)

checkout_agent = create_react_agent(
    model,
    tools=[finalize_order],
    prompt=build_prompt("You are a checkout assistant", order_context_reducer),
    name="checkout_agent"
)

# 6. Build swarm
app = create_swarm(
    [sales_agent, checkout_agent],
    default_active_agent="sales_agent",
    state_schema=OrderState
).compile(checkpointer=InMemorySaver())  # Add if running in Python
```

---

## KEY TAKEAWAYS

✅ Tools can modify state directly by returning dicts
✅ InjectedState makes tools clean and prevents hallucination
✅ Context reducers keep prompts composable and maintainable
✅ Agents can ask users questions naturally - no special tools
✅ Handoff tools define the swarm topology
✅ Checkpointer required for multi-turn (except in UI)
✅ Callable prompts give full control over conversation history
✅ Clean, simple code - no janky workarounds needed

---

Good luck building your swarm! 🚀

