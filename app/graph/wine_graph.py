"""
Merged graph construction and traversal logic from the original app_2 codebase.
"""

from langgraph.graph import StateGraph, END
from app.src.agents.wine_agents import (
    analyze_query_node,
    vector_search_node,
    vision_analysis_node,
    ocr_analysis_node,
    answer_synthesis_node,
    fallback_node
)

def build_agent_graph():
    workflow = StateGraph(dict)
    workflow.add_node("analyze_query", analyze_query_node)
    workflow.add_node("vector_search", vector_search_node)
    workflow.add_node("vision_analysis", vision_analysis_node)
    workflow.add_node("ocr_analysis", ocr_analysis_node)
    workflow.add_node("answer_synthesis", answer_synthesis_node)
    workflow.add_node("fallback", fallback_node)
    workflow.set_entry_point("analyze_query")
    workflow.add_edge("analyze_query", "vector_search")
    workflow.add_edge("vector_search", lambda state: state.get("__next__"), {
        "answer_synthesis": "answer_synthesis",
        "vision_analysis": "vision_analysis"
    })
    workflow.add_edge("vision_analysis", lambda state: state.get("__next__"), {
        "answer_synthesis": "answer_synthesis",
        "ocr_analysis": "ocr_analysis"
    })
    workflow.add_edge("ocr_analysis", "answer_synthesis")
    workflow.add_edge("answer_synthesis", lambda state: state.get("__next__"), {
        "fallback": "fallback",
        None: END
    })
    workflow.add_edge("fallback", END)
    return workflow.compile()
