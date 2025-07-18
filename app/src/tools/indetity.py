from langchain_core.tools import tool


@tool
def identity(query):
    """This is the identity function return whatever user pass in query."""
    return query
