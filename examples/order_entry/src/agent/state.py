from typing import Optional, List
from pydantic import Field
from langgraph_swarm import SwarmState
from langchain_core.runnables import RunnableConfig

from order_entry.src.agent.schemas.file import StateFile
from order_entry.src.agent.schemas.customer_context import CustomerContext
from services.wms_interface.korber.schemas import AgentOrder

# Custom state schema for order management
class OrderState(SwarmState):
    order: AgentOrder = AgentOrder(orders=[])
    documents: List[StateFile] = Field(default_factory=list)
    customer_context: CustomerContext = Field(default_factory=CustomerContext)

class OrderState(SwarmState):
    """State schema for the order entry system."""
    order_items: Optional[list[dict]] = Field(default_factory=list)
    order_total: Optional[float] = Field(default=0.0)
    customer_name: Optional[str] = Field(default="")
    customer_email: Optional[str] = Field(default="")
    # Required by create_react_agent when using custom state_schema
    remaining_steps: Optional[int] = Field(default=None)


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