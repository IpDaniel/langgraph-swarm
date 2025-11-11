from langgraph_swarm import create_handoff_tool

# Additional handoffs referenced in agents.py
transfer_to_decider = create_handoff_tool(
    agent_name="order_decider_agent",
    description="Transfer to the order decider to validate readiness or diagnose issues.",
)

transfer_to_order_placer = create_handoff_tool(
    agent_name="order_placing_agent",
    description="Transfer to the order placement agent to place the order.",
)

transfer_to_customer_service = create_handoff_tool(
    agent_name="customer_service_agent",
    description="Transfer to a customer service agent for general assistance or routing.",
)

transfer_to_parameter_handler = create_handoff_tool(
    agent_name="parameter_handling_agent",
    description="Transfer to the parameter handling agent to add/validate items and order parameters.",
)

transfer_to_splitter = create_handoff_tool(
    agent_name="splitter_agent",
    description="Transfer to the splitting agent to create or fix truck splits.",
)

transfer_to_scheduler = create_handoff_tool(
    agent_name="scheduler_agent",
    description="Transfer to the scheduling agent to schedule trucks and delivery slots.",
)