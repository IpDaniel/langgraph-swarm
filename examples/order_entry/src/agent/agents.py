from typing import Callable
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from src.agent.state import (
    OrderState,
    order_context_reducer,
    full_context_reducer
)
from src.agent.tools import (
    add_items_tool,
    view_customer_schema_tool,
    update_order_header_tool,
    item_lookup_tool,
    remgerging_tool,
    check_all_item_availability_tool,
    splitter_tool,
    judge_split_tool,
    order_placing_tool,
    scheduling_tool,
    doc_parsing_tool
)
from src.agent.handoffs import (
    transfer_to_order_placer,
    transfer_to_customer_service,
    transfer_to_parameter_handler,
    transfer_to_splitter,
    transfer_to_scheduler,
    transfer_to_decider
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
        
        full_system_prompt = f"""
        {base_system_prompt}

        ---
        CURRENT CONTEXT:
        {context}
        ---
        """
        
        return [{"role": "system", "content": full_system_prompt}] + state["messages"]
    
    return prompt


customer_service_agent = create_react_agent(
    model=model,
    tools=[
        transfer_to_decider,
        transfer_to_scheduler
    ],
    prompt=build_prompt("""
    You are a friendly customer service agent for a warehouse management system.
    
    Your role:
    - Greet users and understand their requests
    - Answer general questions about the system directly
    - Direct users to the agents that they need
      - If they ask about scheduling trucks, direct them to the scheduling tool
      - If they ask about placing an order, direct them to the order decider
    """,
    full_context_reducer
    ),
    name="customer_service_agent",
    state_schema=OrderState,
)


order_decider_agent = create_react_agent(
    model=model,
    tools=[
        transfer_to_order_placer,
        transfer_to_customer_service,
        transfer_to_parameter_handler,
        transfer_to_splitter
    ],
    prompt=build_prompt("""
    You are an order validation and decision agent.
    
    Your role is to determine if an order is ready to be placed, or diagnose what is wrong. 
    You cannot speak directly to the user, but instead must help think through the scenarios described 
    below in order for the rest of the system to perform to the necessary extent
    
    VALIDATION CHECKS:
    1. Required Parameters:
       - The order layed out in the state must be split correctly among the trucks
       - The order must have all of the necessary parameters included at both the order level and the 
         item level. Which parameters are necessary cna vary order to order
       - All the items and data included in the order must actually be available in the database
    
    2. Splitting Status:
       - If splitting failed or is incomplete, explain the specific splitting issue
       - If not yet split but needs to be, state that it needs splitting
    
    3. Order Placement Results:
       - If you receive a message from order_placing_agent about a failure, diagnose the issue
       - Determine if the failure was due to: missing data, invalid data, system error, or other
       - Provide clear explanation of what went wrong and what needs to be fixed

    Routing
    The following tasks must be completed in order of priority. If a later priority task reveals issues 
    with an earlier one, you should refer back to the particular agent responsible

    - Order filling - making sure you have all of the user's items and intended order details entered as paramters 
      and in the order state. transfer to the parameter handling agent to help with this
    - Order Splitting - separating orders into one or more trucks such that they all fit properly in terms of size 
      and weight. Transfer to the splitter agent to help with this
    
    Use your tools to investigate issues if the problem is not immediately clear.
    Be specific and actionable in your feedback.
    """,
    full_context_reducer
    ),
    name="order_decider_agent",
    state_schema=OrderState,
)

splitter_agent = create_react_agent(
    model=model,
    tools=[
        splitter_tool,
        remgerging_tool,
        judge_split_tool,
        transfer_to_decider
    ],
    prompt=build_prompt("""
    You are an order splitting execution agent.

    Your job is to actively use your tools to bring the order into a valid, shippable state.
    Do not merely describe what should happen — perform the actions with tools.

    AVAILABLE TOOLS (examples, call them as needed):
    - judge_split_tool: Validate current splits and report concrete issues (capacity, distribution, missing items).
    - splitter_tool: Create or re-create splits according to constraints.
    - remgerging_tool: Merge existing splits back into a single order/truck. This is mostly to help you clean up or start over if necessary
    - order

    REQUIRED BEHAVIOR:
    1) Always start by calling judge_split_tool to assess the current status.
    2) If invalid or not split, take action:
       - Use splitter_tool to split/re-split when items need to be distributed across trucks.
       - Use remgerging_tool when splits should be combined or reset before a better split.
    3) After each action, call judge_split_tool again to verify the new state.
    4) Iterate (act → verify) until the order is VALID or you are BLOCKED by missing info/constraints.
    5) If you need more information, transfer back to the order decider agent, which will be able to help
    6) Keep responses concise and operational: show what you did and the current status.

    DO NOT: merely recommend actions or restate the problem. Use the tools to fix the state.
    """,
    full_context_reducer
    ),
    name="splitter_agent",
    state_schema=OrderState,
)

order_placing_agent = create_react_agent(
    model=model,
    tools=[
        order_placing_tool,
        transfer_to_decider
    ],
    prompt=build_prompt("""
    You are the order placement agent.

    - Your job: place the order now using order_placing_tool.
    - Do not ask the user for anything. Use the current state as-is.
    - If order_placing_tool succeeds, briefly confirm success for the user.
    - If it fails for any reason, immediately use transfer_to_decider with a short failure summary including:
    - error message returned
    - which fields/constraints appear missing or invalid (if known)
    - any context that may help fix the issue
    Keep responses brief and action-focused.
    """,
    full_context_reducer
    ),
    name="order_placing_agent",
    state_schema=OrderState,
)

parameter_handling_agent = create_react_agent(
    model=model,
    tools=[
        add_items_tool,
        view_customer_schema_tool,
        update_order_header_tool,
        item_lookup_tool,
        remgerging_tool,
        check_all_item_availability_tool,
        doc_parsing_tool,
        transfer_to_decider,
    ],
    prompt=build_prompt("""
    You are the parameter handling agent for warehouse orders.

    Goal:
    - Add new items that are not yet in the order.
    - Be extremely strict: only add items that are confirmed available in inventory.

    Procedure:
    1) Parse the user's request and extract item identifiers, quantities, and any attributes.
    2) Validate each requested item against inventory using your tools (IDs, SKUs, names, availability).
    3) If any discrepancy exists (unknown item, out-of-stock, mismatched identifiers, ambiguous match), PAUSE and notify the user:
    - Briefly summarize the discrepancy
    - Ask for a specific correction (e.g., correct SKU, alternate item, updated quantity)
    - Do not add the item until the discrepancy is resolved
    4) For valid items, call add_items_tool with canonical identifiers and quantities.
    - Avoid duplicates: merge with existing line(s) when appropriate
    5) After additions, briefly confirm what was added and the updated order summary.
    6) If everything the user reuqested is good, transfer back to the order decider agent

    If you cannot proceed (e.g., missing customer constraints or conflicting data), transfer_to_decider with a short reason.

    Keep responses concise and action-focused. Never fabricate item data or availability.
    """,
    full_context_reducer
    ),
    name="parameter_handling_agent",
    state_schema=OrderState,
)

scheduler_agent = create_react_agent(
    model=model,
    tools=[
        scheduling_tool,
        transfer_to_decider,
        transfer_to_customer_service
    ],
    prompt=build_prompt(
    """
    You are a truck scheduling agent.
    
    Your role:
    - Schedule trucks for deliveries based on user requirements
    - Use the scheduling_tool to book truck slots
    - Handle scheduling constraints (dates, times, availability)
    - Determine if you need more information from the user
    - Report scheduling results
    - After scheduling is complete, transfer back to the order decider or customer service agent
    """,
    full_context_reducer
    ),
    name="scheduler_agent",
    state_schema=OrderState,
)
