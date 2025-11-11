from typing import Optional, List
from pydantic import Field
from langgraph_swarm import SwarmState
from langchain_core.runnables import RunnableConfig

from src.agent.schemas.file import StateFile
from src.agent.schemas.customer_context import CustomerContext
from src.agent.services.wms_interface.korber.schemas import AgentOrder
from src.agent.schemas.customer_context import Detail

class OrderState(SwarmState):
    order: AgentOrder = AgentOrder(orders=[])
    documents: List[StateFile] = Field(default_factory=list)
    customer_context: CustomerContext = Field(default_factory=CustomerContext)

    remaining_steps: Optional[int] = Field(default=None) # Required for some reason

# Context reducers for different agents
def order_context_reducer(state: dict, config: RunnableConfig) -> str:
    """Reducer for sales agent - shows order items only."""
    order: AgentOrder = state.get("order")
    if not order or not order.orders:
        return "Current Order: Empty"
    
    lines = []
    for order_idx, korber_order in enumerate(order.orders, 1):
        if order_idx > 1:
            lines.append("")
        
        header = korber_order.order_header
        lines.append(f"Order {order_idx}:")
        lines.append(f"  Customer Order Number: {header.CustomerOrderNumber}")
        lines.append(f"  PO Number: {header.PoNumber or 'N/A'}")
        lines.append(f"  Ship To: {header.ship_to.ShipToName}")
        
        if korber_order.Details and korber_order.Details.DetailLine:
            lines.append("  Items:")
            for line in korber_order.Details.DetailLine:
                lines.append(f"    - {line.Quantity}x {line.ItemCode}" + 
                           (f" ({line.InventoryLevel2})" if line.InventoryLevel2 else ""))
        else:
            lines.append("  Items: (none)")
    
    return "\n".join(lines)


def full_context_reducer(state: dict, config: RunnableConfig) -> str:
    """Reducer for checkout agent - shows everything including customer context and documents."""
    # State is passed as dict, not OrderState object
    lines = []
    
    customer_context: CustomerContext = state.get("customer_context")
    if customer_context and hasattr(customer_context, "details") and customer_context.details:
        lines.append("Customer Context:")
        for detail in customer_context.details:
            lines.append(f"  {detail.code:04d}: {detail.content}")
        lines.append("")
    
    documents: List[StateFile] = state.get("documents")
    if documents:
        lines.append("Documents:")
        for doc in documents:
            lines.append(f"  - {doc.title} ({doc.s3_link})")
        lines.append("")
    
    order: AgentOrder = state.get("order")
    if order and order.orders:
        for order_idx, korber_order in enumerate(order.orders, 1):
            if order_idx > 1:
                lines.append("")
            
            header = korber_order.order_header
            lines.append(f"Order {order_idx}:")
            lines.append(f"  Customer Order Number: {header.CustomerOrderNumber}")
            lines.append(f"  PO Number: {header.PoNumber or 'N/A'}")
            lines.append(f"  Company Code: {header.CompanyCode}")
            lines.append(f"  Customer Code: {header.CustomerCode}")
            lines.append(f"  Ship To: {header.ship_to.ShipToName}")
            if header.ship_to.ShipToAdd1:
                lines.append(f"    {header.ship_to.ShipToAdd1}")
            if header.ship_to.ShipToCity:
                city_state = f"{header.ship_to.ShipToCity}"
                if header.ship_to.ShipToState:
                    city_state += f", {header.ship_to.ShipToState}"
                if header.ship_to.ShipToZip:
                    city_state += f" {header.ship_to.ShipToZip}"
                lines.append(f"    {city_state}")
            
            if header.sold_to:
                lines.append(f"  Sold To: {header.sold_to.SoldToName or 'N/A'}")
            
            if korber_order.Details and korber_order.Details.DetailLine:
                lines.append("  Items:")
                for line in korber_order.Details.DetailLine:
                    item_line = f"    - {line.Quantity}x {line.ItemCode}"
                    if line.InventoryLevel2:
                        item_line += f" (Level 2: {line.InventoryLevel2})"
                    if line.InventoryLevel3:
                        item_line += f" (Level 3: {line.InventoryLevel3})"
                    if line.InventoryLevel4:
                        item_line += f" (Level 4: {line.InventoryLevel4})"
                    if line.SkuCode:
                        item_line += f" [SKU: {line.SkuCode}]"
                    lines.append(item_line)
            else:
                lines.append("  Items: (none)")
    else:
        lines.append("Current Order: Empty")
    
    return "\n".join(lines)