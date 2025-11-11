import logging
from langgraph_swarm import create_swarm
from src.agent.state import OrderState
from src.agent.agents import (
    customer_service_agent, 
    order_decider_agent, 
    splitter_agent, 
    order_placing_agent, 
    parameter_handling_agent, 
    scheduler_agent
)

logger = logging.getLogger(__name__)

# Build and compile the swarm with no checkpointer

builder = create_swarm(
    [
        customer_service_agent, 
        order_decider_agent, 
        splitter_agent, 
        order_placing_agent, 
        parameter_handling_agent, 
        scheduler_agent
    ],
    default_active_agent="customer_service_agent",
    state_schema=OrderState,
)
app = builder.compile()

# Filter out empty/None values for order fields to preserve persisted state
# LangGraph Studio sends all fields in input, even if empty, which can overwrite persisted state
# original_invoke = app.invoke

# def filtered_invoke(input_data, config=None):
#     """Filter out empty/None values for order fields to preserve persisted state."""
#     logger.info(f"[DEBUG filtered_invoke] Original input_data keys: {list(input_data.keys()) if isinstance(input_data, dict) else 'not a dict'}")
#     if isinstance(input_data, dict):
#         # Fields that should only be included if they have non-default values
#         order_fields = ['order_items', 'order_total', 'customer_name', 'customer_email']
        
#         # Filter: exclude order fields if they're None, empty list, empty string, or 0.0
#         # This allows persisted state to be preserved when Studio sends empty values
#         filtered = {}
#         for k, v in input_data.items():
#             if k in order_fields:
#                 logger.info(f"[DEBUG filtered_invoke] Checking order field '{k}': value={v}, type={type(v)}")
#                 # Only include if it's a meaningful value (not default/empty)
#                 if v is not None and v != [] and v != "" and v != 0.0:
#                     logger.info(f"[DEBUG filtered_invoke] Including '{k}' with value: {v}")
#                     filtered[k] = v
#                 else:
#                     logger.info(f"[DEBUG filtered_invoke] FILTERING OUT '{k}' (empty/default value)")
#                 # Otherwise, exclude it so persisted state isn't overwritten
#             else:
#                 # Always include non-order fields (like 'messages', 'active_agent')
#                 filtered[k] = v
#         logger.info(f"[DEBUG filtered_invoke] Filtered input_data keys: {list(filtered.keys())}")
#         input_data = filtered
#     return original_invoke(input_data, config)

# app.invoke = filtered_invoke

