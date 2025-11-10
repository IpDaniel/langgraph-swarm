from typing import Callable
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from order_entry.src.agent.state import (
    OrderState,
    order_context_reducer,
    full_context_reducer
)
from order_entry.src.agent.tools import (
    add_to_order, 
    remove_from_order, 
    update_customer_info, 
    finalize_order
)
from order_entry.src.agent.handoffs import (
    transfer_to_checkout,
    transfer_to_sales
)

# Initialize the model
model = ChatOpenAI(model="gpt-4o")

# Prompt builder helper
def build_prompt(
    base_system_prompt: str,
    context_reducer: Callable[[dict, RunnableConfig], str],
) -> Callable[[dict, RunnableConfig], list]:
    """Build a dynamic prompt function that combines base prompt with context."""
    def prompt(state: dict, config: RunnableConfig) -> list:
        context = context_reducer(state, config)
        
        full_system_prompt = f"""{base_system_prompt}

---
CURRENT CONTEXT:
{context}
---
"""
        
        return [{"role": "system", "content": full_system_prompt}] + state["messages"]
    
    return prompt

# Create agents with OrderState schema so tool updates propagate to parent
sales_agent = create_react_agent(
    model,
    tools=[
        add_to_order,
        remove_from_order,
        update_customer_info,
        transfer_to_checkout,
    ],
    prompt=build_prompt(
        """You are a friendly sales assistant helping customers build their order.

Your workflow:
1. Greet the customer warmly
2. When they want an item, ask for ALL required details:
   - What item? (be specific)
   - What size/quantity?
   - Any special requests?
3. Ask ONE question at a time - don't overwhelm them
4. Once you have all details, use add_to_order tool
5. Confirm what was added and ask if they want anything else
6. When they're ready to checkout, use transfer_to_checkout tool

Be conversational, helpful, and patient. Always confirm details before adding items.""",
        order_context_reducer
    ),
    name="sales_agent",
    state_schema=OrderState,  # KEY: Use parent OrderState so updates propagate
)

checkout_agent = create_react_agent(
    model,
    tools=[
        finalize_order,
        transfer_to_sales,
    ],
    prompt=build_prompt(
        """You are a checkout assistant responsible for finalizing orders.

Your workflow:
1. Review the complete order with the customer
2. Confirm customer information (name, email if needed)
3. If customer info is missing, ask for it politely
4. Once everything is confirmed, use finalize_order tool
5. If customer wants to modify the order, use transfer_to_sales tool

Be thorough, professional, and ensure accuracy before finalizing.""",
        full_context_reducer
    ),
    name="checkout_agent",
    state_schema=OrderState,  # KEY: Use parent OrderState so updates propagate
)