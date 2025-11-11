import json
import yaml
from typing import Annotated, Any
from langgraph.prebuilt import InjectedState
from langchain_core.tools import tool
from src.agent.services.doc_parsing.doc_parsing import Normalizer
from src.agent.schemas.file import StateFile
from src.agent.services.wms_interface.korber.schemas import (
    InventoryDetailsQueryMessageBody,
    AgentOrder
)
from src.agent.services.wms_interface.korber.interface import KorberInterface

@tool
def doc_parsing_tool(
    doc_title: str,
    doc_s3_link: str
) -> str:
    """
    Retrieve and parse a document to extract its readable text content.
    
    Use this tool when you need to read documents that the user has uploaded,
    such as PDFs, Excel files, Word documents, invoices, or purchase orders.
    The tool fetches the document from S3 and converts it to readable text
    that you can analyze to extract order information, item details, dates, etc.
    
    Args:
        doc_s3_link: The S3 URL/link of the document to parse (e.g., "s3://bucket/invoice.pdf")
        doc_title: The title of the document
        
    Returns:
        Plain text content of the document, converted from PDF/Excel/Word format
        into readable text that you can parse to extract order parameters
    """
    return Normalizer().normalize(StateFile(title=doc_title, s3_link=doc_s3_link))


@tool
def item_lookup_tool(
    query: InventoryDetailsQueryMessageBody,
) -> str:
    """
    Look up item details and inventory information from the warehouse system.
    
    Use this tool to verify that item codes exist, get item descriptions,
    check inventory levels, and validate item data before creating orders.
    
    Args:
        query: Item lookup query with CompanyCode, CustomerCode, ItemCode, and optional inventory level filters.
        
    Returns:
        JSON string with item details including:
        - Item code and description
        - Available inventory quantity
        - Inventory levels and locations
        - Item status and availability
    """
    
    try:
        korber = KorberInterface()
        result = korber.lookup_item(query)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "item_code": query.ItemCode,
            "message": "Failed to lookup item. Item may not exist or system error occurred."
        }, indent=2)

# TODO: [API DETAILS NEEDED]: need to know how to determine if the header data is available (dropdowns)
@tool
def check_all_item_availability_tool(
    state: Annotated[Any, InjectedState],
) -> str:
    """Check availability for all items currently in the order.
    
    Returns:
        Dict summary with per-item availability and an overall status.
    """
    agent_order: AgentOrder = state["order"]
    return KorberInterface().check_availability(agent_order=agent_order)

# TODO: [API DETAILS NEEDED]: need to know how to get a customer's header mappings
@tool
def view_customer_schema_tool(
    customer_code: str
) -> str:
    """View the customer’s required schema/constraints for orders and items.
    
    Returns:
        A brief textual description of required fields and constraints.
        Informs the user on important information such as which terms 
        refer to which inventory levels
    """
    return KorberInterface().check_customer_schema(customer_code=customer_code)

@tool
def full_order_placing_tool(
    state: Annotated[Any, InjectedState],
) -> dict:
    """Place the full agent_order into the WMS/OMS with all orders.
    
    Returns:
        A message informing the user the status of the attempt to place the order
    
    Always clear successfully placed orders from the active state so that they do not 
    get placed again. Use other tools for this
    """
    agent_order: AgentOrder = state["order"]
    results = []
    for order in agent_order.orders:
        results.append(KorberInterface().place_order(order=order))
    return yaml.dump(results, default_flow_style=False)

@tool
def single_order_placing_tool(
    state: Annotated[Any, InjectedState],
    CustomerOrderNumber: str,
) -> str:
    """Place one specific order from the agent_order into the WMS/OMS.
    
    Args:
        CustomerOrderNumber: The customer order number of the order to place
    
    Returns:
        A message informing the user the status of the attempt to place the order

    Always clear successfully placed orders from the active state so that they do not 
    get placed again. Use other tools for this
    """
    agent_order: AgentOrder = state["order"]
    
    target_order = None
    for order in agent_order.orders:
        if order.order_header.CustomerOrderNumber == CustomerOrderNumber:
            target_order = order
            break
    
    if target_order is None:
        return f"Error: Order with CustomerOrderNumber '{CustomerOrderNumber}' not found."
    
    try:
        response = KorberInterface().place_order(order=target_order)
        
        if response.Result.Success:
            return (
                f"Successfully placed order '{CustomerOrderNumber}'.\n"
                f"E3PL Order Number: {response.Message.OrderNumber}\n"
                f"Status Code: {response.Result.Code}"
            )
        else:
            return (
                f"Failed to place order '{CustomerOrderNumber}'.\n"
                f"Error: {response.Result.ErrorMessage}\n"
                f"Status Code: {response.Result.Code}"
            )
    except Exception as e:
        return f"Error placing order '{CustomerOrderNumber}': {str(e)}"


@tool
def judge_split_tool(
    state: Annotated[Any, InjectedState],
) -> str:
    """Validate current splits for capacity, distribution, and completeness.
    
    Returns:
        Dict with validation results and issues found, plus an overall valid flag.
    """
    # Stub implementation
    pass