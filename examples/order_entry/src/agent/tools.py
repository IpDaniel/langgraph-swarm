import logging
from typing import Annotated, Any
from langchain_core.runnables.utils import AnyConfigurableField
from langgraph.prebuilt import InjectedState
from langchain_core.tools import tool
from pydantic.types import AnyItemType

logger = logging.getLogger(__name__)

# Order management tools
@tool
def add_to_order(
    item_name: str,
    quantity: int,
    price: float,
    state: Annotated[Any, InjectedState],
) -> dict:
    """Add an item to the customer's order.
    
    Args:
        item_name: Name of the item to add
        quantity: Number of items to add
        price: Price per item
    """
    logger.info(f"[DEBUG add_to_order] Received state: {state}")
    current_items = state.get("order_items", [])
    current_total = state.get("order_total", 0.0)
    logger.info(f"[DEBUG add_to_order] Current items: {current_items}, Current total: {current_total}")
    
    new_item = {
        "name": item_name,
        "quantity": quantity,
        "price": price,
        "total": quantity * price
    }
    
    updated_items = current_items + [new_item]
    updated_total = current_total + (quantity * price)
    logger.info(f"[DEBUG add_to_order] Returning update: order_items={len(updated_items)} items, order_total={updated_total}")
    
    return {
        "order_items": updated_items,
        "order_total": updated_total
    }


@tool
def remove_from_order(
    item_name: str,
    state: Annotated[Any, InjectedState],
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
    state: Annotated[Any, InjectedState],
    name: str = "",
    email: str = "",
) -> dict:
    """Update customer information.
    
    Args:
        name: Customer's name
        email: Customer's email address
    """
    logger.info(f"[DEBUG update_customer_info] Received state: {state}")
    updates = {}
    if name:
        updates["customer_name"] = name
    if email:
        updates["customer_email"] = email
    logger.info(f"[DEBUG update_customer_info] Returning updates: {updates}")
    return updates


@tool
def finalize_order(
    state: Annotated[Any, InjectedState],
) -> str:
    """Finalize and submit the order for processing.
    
    This tool completes the order and should only be called when:
    - All items are confirmed
    - Customer information is complete
    - Customer has approved the order
    """
    logger.info(f"[DEBUG finalize_order] Received FULL state: {state}")
    logger.info(f"[DEBUG finalize_order] State keys: {list(state.keys())}")
    order_items = state.get("order_items", [])
    order_total = state.get("order_total", 0.0)
    customer_name = state.get("customer_name", "")
    logger.info(f"[DEBUG finalize_order] order_items type: {type(order_items)}, value: {order_items}")
    logger.info(f"[DEBUG finalize_order] order_total: {order_total}")
    logger.info(f"[DEBUG finalize_order] customer_name: {customer_name}")
    
    if not order_items:
        logger.error(f"[DEBUG finalize_order] ERROR: order_items is empty or falsy. Type: {type(order_items)}, Value: {repr(order_items)}")
        return "Error: Cannot finalize an empty order."
    
    if not customer_name:
        return "Error: Customer name is required before finalizing."
    
    # In a real system, you would submit to your order processing system here
    return f"Order finalized successfully! Order #{hash(str(order_items)) % 10000} for {customer_name} totaling ${order_total:.2f} has been submitted."