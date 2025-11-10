from typing import Annotated, Callable
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph_swarm import SwarmState, create_handoff_tool, create_swarm
from langchain_core.tools import tool

# Initialize the model
model = ChatOpenAI(model="gpt-4o")


# Custom state schema for order management
class OrderState(SwarmState):
    """State schema for the order entry system."""
    order_items: list[dict] = []
    order_total: float = 0.0
    customer_name: str = ""
    customer_email: str = ""


# Order management tools
@tool
def add_to_order(
    item_name: str,
    quantity: int,
    price: float,
    state: Annotated[dict, InjectedState],
) -> dict:
    """Add an item to the customer's order.
    
    Args:
        item_name: Name of the item to add
        quantity: Number of items to add
        price: Price per item
    """
    current_items = state.get("order_items", [])
    current_total = state.get("order_total", 0.0)
    
    new_item = {
        "name": item_name,
        "quantity": quantity,
        "price": price,
        "total": quantity * price
    }
    
    return {
        "order_items": current_items + [new_item],
        "order_total": current_total + (quantity * price)
    }


@tool
def remove_from_order(
    item_name: str,
    state: Annotated[dict, InjectedState],
) -> dict:
    """Remove an item from the customer's order.
    
    Args:
        item_name: Name of the item to remove
    """
    current_items = state.get("order_items", [])
    current_total = state.get("order_total", 0.0)
    
    # Find and remove item
    updated_items = [item for item in current_items if item["name"] != item_name]
    removed_items = [item for item in current_items if item["name"] == item_name]
    
    removed_total = sum(item["total"] for item in removed_items)
    
    return {
        "order_items": updated_items,
        "order_total": current_total - removed_total
    }


@tool
def update_customer_info(
    state: Annotated[dict, InjectedState],
    name: str = "",
    email: str = "",
) -> dict:
    """Update customer information.
    
    Args:
        name: Customer's name
        email: Customer's email address
    """
    updates = {}
    if name:
        updates["customer_name"] = name
    if email:
        updates["customer_email"] = email
    return updates


@tool
def finalize_order(
    state: Annotated[dict, InjectedState],
) -> str:
    """Finalize and submit the order for processing.
    
    This tool completes the order and should only be called when:
    - All items are confirmed
    - Customer information is complete
    - Customer has approved the order
    """
    order_items = state.get("order_items", [])
    order_total = state.get("order_total", 0.0)
    customer_name = state.get("customer_name", "")
    
    if not order_items:
        return "Error: Cannot finalize an empty order."
    
    if not customer_name:
        return "Error: Customer name is required before finalizing."
    
    # In a real system, you would submit to your order processing system here
    return f"Order finalized successfully! Order #{hash(str(order_items)) % 10000} for {customer_name} totaling ${order_total:.2f} has been submitted."


# Handoff tools
transfer_to_checkout = create_handoff_tool(
    agent_name="checkout_agent",
    description="Transfer to the checkout agent when the customer is ready to finalize their order.",
)

transfer_to_sales = create_handoff_tool(
    agent_name="sales_agent",
    description="Transfer back to the sales agent if the customer wants to modify their order.",
)


# Context reducers for different agents
def order_context_reducer(state: dict, config: RunnableConfig) -> str:
    """Reducer for sales agent - shows order items and total only."""
    order_items = state.get("order_items", [])
    order_total = state.get("order_total", 0.0)
    
    if not order_items:
        return "Current Order: Empty\nTotal: $0.00"
    
    items_text = "\n".join([
        f"  - {item['quantity']}x {item['name']} @ ${item['price']:.2f} = ${item['total']:.2f}"
        for item in order_items
    ])
    
    return f"""Current Order:
{items_text}
Total: ${order_total:.2f}"""


def full_context_reducer(state: dict, config: RunnableConfig) -> str:
    """Reducer for checkout agent - shows everything including customer info."""
    order_items = state.get("order_items", [])
    order_total = state.get("order_total", 0.0)
    customer_name = state.get("customer_name", "Not provided")
    customer_email = state.get("customer_email", "Not provided")
    
    items_text = "\n".join([
        f"  - {item['quantity']}x {item['name']} @ ${item['price']:.2f}"
        for item in order_items
    ]) if order_items else "  (none)"
    
    return f"""Customer: {customer_name}
Email: {customer_email}
Order Items:
{items_text}
Order Total: ${order_total:.2f}"""


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


# Create agents
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
)

# Build and compile the swarm
builder = create_swarm(
    [sales_agent, checkout_agent],
    default_active_agent="sales_agent",
    state_schema=OrderState,
)
app = builder.compile()

