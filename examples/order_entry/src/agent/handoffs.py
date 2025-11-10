from langgraph_swarm import create_handoff_tool

# Handoff tools
transfer_to_checkout = create_handoff_tool(
    agent_name="checkout_agent",
    description="Transfer to the checkout agent when the customer is ready to finalize their order.",
)

transfer_to_sales = create_handoff_tool(
    agent_name="sales_agent",
    description="Transfer back to the sales agent if the customer wants to modify their order.",
)