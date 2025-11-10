# Order Entry Example

A multi-agent order entry system built with LangGraph Swarm. This example demonstrates how agents can collaborate to help customers build and finalize orders.

## Overview

The system consists of specialized agents:
- **Sales Agent**: Helps customers build their order by adding items, asking clarifying questions, and gathering order details
- **Checkout Agent**: Reviews the order, confirms customer information, and finalizes the purchase

These agents can transfer control to each other using handoff tools, maintaining order state throughout the conversation.

## Quickstart

```bash
uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev
```

## Features

- Multi-turn conversations with customers
- Order state management (items, quantities, totals)
- Agent handoff between sales and checkout
- Dynamic context injection based on current order state
- Human-in-the-loop for gathering customer information

## How It Works

1. The system starts with the Sales Agent as the default agent
2. Sales Agent asks customers questions to build their order
3. Customers can add items, modify quantities, and review their order
4. When ready, Sales Agent transfers to Checkout Agent
5. Checkout Agent reviews the order and finalizes the purchase
6. Order state is maintained throughout the entire conversation

