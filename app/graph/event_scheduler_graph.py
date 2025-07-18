from typing import Annotated,Sequence
import operator
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from app.src.utils.event_scheduler_function import agent_node
import functools
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from app.src.agents.event_scheduler_agent import (
    comparison,
    colortrend,
    greet_agent,
    prechat_agent,
    fallback_agent,
    scheduler_agent,
    feedback_agent,
)

from app.src.utils.event_scheduler_supervisor import (

supervisor_chain,greeting_chain,members
)
memory = MemorySaver()


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

    next: str


comparison_node = functools.partial(agent_node, agent=comparison, name="comparison")

colortrend_node = functools.partial(agent_node, agent=colortrend, name="colortrend")

greet_node = functools.partial(agent_node, agent=greet_agent, name="greet_agent")

prechat_node = functools.partial(agent_node, agent=prechat_agent, name="prechat_agent")

feedback_node = functools.partial(
    agent_node, agent=feedback_agent, name="feedback_agent"
)

scheduler_node = functools.partial(
    agent_node, agent=scheduler_agent, name="scheduler_agent"
)

fallback_node = functools.partial(
    agent_node,agent = fallback_agent, name = "fallback_agent"
)


workflow = StateGraph(AgentState)
workflow.add_node("comparison", comparison_node)
workflow.add_node("colortrend", colortrend_node)
workflow.add_node("greeting_chain", greeting_chain)
workflow.add_node("greet_agent", greet_node)
workflow.add_node("supervisor", supervisor_chain)
workflow.add_node("prechat_agent", prechat_node)
workflow.add_node("feedback_agent", feedback_node)
workflow.add_node("scheduler_agent", scheduler_node)
workflow.add_node("fallback_agent", fallback_node)

for member in members:
    if member == "greeting_chain":
        continue
    workflow.add_edge(member, END)

workflow.add_edge("greet_agent", END)
workflow.add_edge("greet_agent", "greeting_chain")

conditional_map = {k: k for k in members}

workflow.add_conditional_edges(
    "greeting_chain",
    lambda x: x["next"],
    {"prechat_agent": "prechat_agent", "greet_agent": "greet_agent", "FINISH": END},
)
workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)

workflow.add_edge(START, "supervisor")

graph = workflow.compile(checkpointer=memory)