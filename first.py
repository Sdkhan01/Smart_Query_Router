from langgraph.graph import StateGraph , START, END
from typing import TypedDict

class mystate(TypedDict):
    name : str
    greet : str

def namee(state : mystate) ->dict :
    raw_name = state['name']
    
    final_name= raw_name.strip().title()
    return{"name": final_name}

def greeting(state : mystate)-> dict :
    f_name = state['name']
    gr = f"Hello {f_name}, Welcome to Eligent AI"
    return {"greet": gr}

graph = StateGraph(mystate)
#node
graph.add_node("name", namee)
graph.add_node("greet", greeting)

#Edges
graph.add_edge(START,"name")
graph.add_edge("name", "greet")
graph.add_edge("greet", END)

comp = graph.compile()
result = comp.invoke({"name": "Shadab","greet": ""})
print(result)