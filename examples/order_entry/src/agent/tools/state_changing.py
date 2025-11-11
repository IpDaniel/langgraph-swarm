from typing import Annotated, Any, Optional
from langgraph.prebuilt import InjectedState
from langchain_core.tools import tool
from src.agent.services.wms_interface.korber.schemas import (
    CreateReplaceOrderMessageBody,
    ReceiptDetails,
    AgentOrder,
    OrderHeader,
    OrderDetails,
    OrderDetailLine,
    PartialOrderHeader,
    PartialOrderDetailLine
)


@tool
def initiate_order_tool(
    state: Annotated[Any, InjectedState],
    order_header: OrderHeader,
) -> dict:
    """Initiate a new order with header information.
    
    Args:
        order_header: Complete order header with all order details, addresses, carrier info, etc.
    """
    agent_order: AgentOrder = state["order"]
    for order in agent_order.orders:
        if order.order_header.CustomerOrderNumber == order_header.CustomerOrderNumber:
            return {
                "error": "OrderAlreadyExists",
                "message": f"An order with CustomerOrderNumber '{order_header.CustomerOrderNumber}' already exists.",
                "existing_order": order.model_dump()
            }
    
    order_details = OrderDetails(DetailLine=[]) # empty to start
    new_order = CreateReplaceOrderMessageBody(
        order_header=order_header,
        remarks=None,
        EdiHeaderData=[],
        Details=order_details
    )
    updated_orders = agent_order.orders + [new_order]
    return {"order": AgentOrder(orders=updated_orders)}

@tool
def remove_order_tool(
    state: Annotated[Any, InjectedState],
    CustomerOrderNumber: str
) -> dict:
    """Remove an entire order from the agent order state.
    
    Args:
        CustomerOrderNumber: The customer order number of the order to remove
    
    Returns:
        Dict state update with the order removed.
    """
    agent_order: AgentOrder = state["order"]
    
    target_order_index = None
    for idx, order in enumerate(agent_order.orders):
        if order.order_header.CustomerOrderNumber == CustomerOrderNumber:
            target_order_index = idx
            break
    
    if target_order_index is None:
        return {
            "error": "OrderNotFound",
            "message": f"Order with CustomerOrderNumber '{CustomerOrderNumber}' not found.",
        }
    
    # Remove the order from the orders list
    updated_orders = agent_order.orders.copy()
    updated_orders.pop(target_order_index)
    
    return {"order": AgentOrder(orders=updated_orders)}

@tool
def add_items_tool(
    state: Annotated[Any, InjectedState],
    CustomerOrderNumber: str,
    items: ReceiptDetails,
) -> dict:
    """Add one or more items to the order.
    
    Args:
        CustomerOrderNumber: The customer order number to add items to
        items: Receipt details containing the items to add (DetailLine with item codes, quantities, etc.)
    
    Returns:
        Dict state update with appended items.
    """
    agent_order: AgentOrder = state["order"]
    
    target_order = None
    target_order_index = None
    for idx, order in enumerate(agent_order.orders):
        if order.order_header.CustomerOrderNumber == CustomerOrderNumber:
            target_order = order
            target_order_index = idx
            break
    
    if target_order is None:
        return {
            "error": "OrderNotFound",
            "message": f"Order with CustomerOrderNumber '{CustomerOrderNumber}' not found.",
        }
    new_order_line = [
        OrderDetailLine(
            ItemCode=receipt_line.ItemCode,
            InventoryLevel2=receipt_line.InventoryLevel2 or "",
            InventoryLevel3=receipt_line.InventoryLevel3 or "",
            InventoryLevel4=receipt_line.InventoryLevel4 or "",
            Quantity=receipt_line.Quantity,
            SkuCode=receipt_line.SkuCode or "",
            LineRemarks=receipt_line.LineRemarks,
            EdiDetailData=receipt_line.EdiDetailData or []
        )
        for receipt_line in items.DetailLine
    ]
    
    existing_line = target_order.Details.DetailLine
    updated_details = OrderDetails(DetailLine=existing_line + new_order_line)
    updated_order = CreateReplaceOrderMessageBody(
        order_header=target_order.order_header,
        remarks=target_order.remarks,
        EdiHeaderData=target_order.EdiHeaderData or [],
        Details=updated_details
    )
    
    updated_orders = agent_order.orders.copy()
    updated_orders[target_order_index] = updated_order
    return {"order": AgentOrder(orders=updated_orders)}


@tool
def update_order_header_tool(
    state: Annotated[Any, InjectedState],
    CustomerOrderNumber: str,
    header_updates: PartialOrderHeader,
) -> dict:
    """Update one or more fields in an order header.
    
    Args:
        CustomerOrderNumber: The customer order number of the order to update
        header_updates: Partial order header with only the fields you want to change.
            All fields are optional - only include the ones you want to update.
            The LLM can see all available fields and their descriptions in the schema.
    
    Returns:
        Dict state update with the updated order header.
    """
    agent_order: AgentOrder = state["order"]
    
    target_order = None
    target_order_index = None
    for idx, order in enumerate(agent_order.orders):
        if order.order_header.CustomerOrderNumber == CustomerOrderNumber:
            target_order = order
            target_order_index = idx
            break
    
    if target_order is None:
        return {
            "error": "OrderNotFound",
            "message": f"Order with CustomerOrderNumber '{CustomerOrderNumber}' not found.",
        }
    
    existing_header_dict = target_order.order_header.model_dump(exclude_none=False)
    updates_dict = header_updates.model_dump(exclude_none=True)
    updated_header_dict = {**existing_header_dict, **updates_dict}
    updated_header = OrderHeader(**updated_header_dict)
    
    updated_order = CreateReplaceOrderMessageBody(
        order_header=updated_header,
        remarks=target_order.remarks,
        EdiHeaderData=target_order.EdiHeaderData or [],
        Details=target_order.Details
    )
    
    updated_orders = agent_order.orders.copy()
    updated_orders[target_order_index] = updated_order
    return {"order": AgentOrder(orders=updated_orders)}

@tool
def update_item_tool(
    state: Annotated[Any, InjectedState],
    CustomerOrderNumber: str,
    ItemCode: str,
    InventoryLevel2: str = "",
    InventoryLevel3: str = "",
    InventoryLevel4: str = "",
    line_updates: Optional[PartialOrderDetailLine] = None,
) -> dict:
    """Update one or more fields in an order line item.
    
    Args:
        CustomerOrderNumber: The customer order number of the order containing the item
        ItemCode: The item code of the line item to update
        InventoryLevel2: Inventory level 2 identifier (optional, default empty string)
        InventoryLevel3: Inventory level 3 identifier (optional, default empty string)
        InventoryLevel4: Inventory level 4 identifier (optional, default empty string)
        line_updates: Partial order detail line with only the fields you want to change.
            All fields are optional - only include the ones you want to update.
    
    Returns:
        Dict state update with the updated order line item.
    """
    if line_updates is None:
        return {
            "error": "InvalidInput",
            "message": "line_updates parameter is required. At least one field must be provided to update.",
        }
    
    agent_order: AgentOrder = state["order"]
    
    target_order = None
    target_order_index = None
    for idx, order in enumerate(agent_order.orders):
        if order.order_header.CustomerOrderNumber == CustomerOrderNumber:
            target_order = order
            target_order_index = idx
            break
    
    if target_order is None:
        return {
            "error": "OrderNotFound",
            "message": f"Order with CustomerOrderNumber '{CustomerOrderNumber}' not found.",
        }
    
    # Find the specific line item by matching ItemCode and inventory levels
    target_line_index = None
    for idx, line in enumerate(target_order.Details.DetailLine):
        if (line.ItemCode == ItemCode and
            (line.InventoryLevel2 or "") == (InventoryLevel2 or "") and
            (line.InventoryLevel3 or "") == (InventoryLevel3 or "") and
            (line.InventoryLevel4 or "") == (InventoryLevel4 or "")):
            target_line_index = idx
            break
    
    if target_line_index is None:
        return {
            "error": "ItemNotFound",
            "message": (
                f"Line item with ItemCode '{ItemCode}', "
                f"InventoryLevel2 '{InventoryLevel2}', "
                f"InventoryLevel3 '{InventoryLevel3}', "
                f"InventoryLevel4 '{InventoryLevel4}' not found in order '{CustomerOrderNumber}'."
            ),
        }
    
    existing_line_dict = target_order.Details.DetailLine[target_line_index].model_dump(exclude_none=False)
    updates_dict = line_updates.model_dump(exclude_none=True)
    updated_line_dict = {**existing_line_dict, **updates_dict}
    updated_line = OrderDetailLine(**updated_line_dict)
    updated_lines = target_order.Details.DetailLine.copy()
    updated_lines[target_line_index] = updated_line
    updated_details = OrderDetails(DetailLine=updated_lines)
    updated_order = CreateReplaceOrderMessageBody(
        order_header=target_order.order_header,
        remarks=target_order.remarks,
        EdiHeaderData=target_order.EdiHeaderData or [],
        Details=updated_details
    )
    updated_orders = agent_order.orders.copy()
    updated_orders[target_order_index] = updated_order
    return {"order": AgentOrder(orders=updated_orders)}

@tool
def remove_item_tool(
    state: Annotated[Any, InjectedState],
    CustomerOrderNumber: str,
    ItemCode: str,
    InventoryLevel2: str = "",
    InventoryLevel3: str = "",
    InventoryLevel4: str = "",
) -> dict:
    """Remove a line item from an order.
    
    Args:
        CustomerOrderNumber: The customer order number of the order containing the item
        ItemCode: The item code of the line item to remove
        InventoryLevel2: Inventory level 2 identifier (optional, default empty string)
        InventoryLevel3: Inventory level 3 identifier (optional, default empty string)
        InventoryLevel4: Inventory level 4 identifier (optional, default empty string)
    
    Returns:
        Dict state update with the item removed from the order.
    """
    agent_order: AgentOrder = state["order"]
    
    target_order = None
    target_order_index = None
    for idx, order in enumerate(agent_order.orders):
        if order.order_header.CustomerOrderNumber == CustomerOrderNumber:
            target_order = order
            target_order_index = idx
            break
    
    if target_order is None:
        return {
            "error": "OrderNotFound",
            "message": f"Order with CustomerOrderNumber '{CustomerOrderNumber}' not found.",
        }
    
    target_line_index = None
    for idx, line in enumerate(target_order.Details.DetailLine):
        if (line.ItemCode == ItemCode and
            (line.InventoryLevel2 or "") == (InventoryLevel2 or "") and
            (line.InventoryLevel3 or "") == (InventoryLevel3 or "") and
            (line.InventoryLevel4 or "") == (InventoryLevel4 or "")):
            target_line_index = idx
            break
    
    if target_line_index is None:
        return {
            "error": "ItemNotFound",
            "message": (
                f"Line item with ItemCode '{ItemCode}', "
                f"InventoryLevel2 '{InventoryLevel2}', "
                f"InventoryLevel3 '{InventoryLevel3}', "
                f"InventoryLevel4 '{InventoryLevel4}' not found in order '{CustomerOrderNumber}'."
            ),
        }
    updated_lines = target_order.Details.DetailLine.copy()
    updated_lines.pop(target_line_index)
    updated_details = OrderDetails(DetailLine=updated_lines)
    updated_order = CreateReplaceOrderMessageBody(
        order_header=target_order.order_header,
        remarks=target_order.remarks,
        EdiHeaderData=target_order.EdiHeaderData or [],
        Details=updated_details
    )
    updated_orders = agent_order.orders.copy()
    updated_orders[target_order_index] = updated_order
    return {"order": AgentOrder(orders=updated_orders)}


@tool
def remgerging_tool(
    state: Annotated[Any, InjectedState],
) -> dict:
    """Merge existing splits back into a single order/truck to reset before re-splitting.
    
    Returns:
        Dict state update reflecting merged splits.
    """
    # Stub implementation
    pass


@tool
def splitter_tool(
    state: Annotated[Any, InjectedState],
    strategy: str = "capacity_balanced",
) -> dict:
    """Split or re-split the order into trucks according to constraints.
    
    Args:
        strategy: Optional splitting strategy (e.g., "capacity_balanced").
    
    Returns:
        Dict state update reflecting computed splits.
    """
    # Stub implementation
    pass


@tool
def order_placing_tool(
    state: Annotated[Any, InjectedState],
) -> dict:
    """Place the order into the WMS/OMS.
    
    Returns:
        A short success message or raises an error in real implementation.
    """
    # Stub implementation
    pass


@tool
def scheduling_tool(
    state: Annotated[Any, InjectedState],
    delivery_date: str = "",
    delivery_window: str = "",
) -> dict:
    """Schedule trucks/slots for deliveries based on the order and constraints.
    
    Args:
        delivery_date: Preferred delivery date (ISO string).
        delivery_window: Preferred time window (e.g., "08:00-12:00").
    
    Returns:
        Dict with scheduling result details.
    """
    # Stub implementation
    pass

