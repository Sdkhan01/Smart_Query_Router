import asyncio
from dotenv import load_dotenv
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import StreamPart  # ← NEW in v1.1: type-safe StreamPart
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

def agent_node(state: MessagesState) -> dict:
    return {"messages": [llm.invoke(state["messages"])]}

memory = MemorySaver()
builder = StateGraph(MessagesState)
builder.add_node("agent", agent_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)
graph = builder.compile(checkpointer=memory)

# ── PATTERN 1: stream(version="v2") — Type-safe StreamPart output (NEW in v1.1) ──
print("=== PATTERN 1: stream(version='v2') — Type-safe StreamPart ===")
config1 = {"configurable": {"thread_id": "s1"}}
for chunk in graph.stream(
    {"messages": [HumanMessage(content="Explain LangGraph in 2 sentences")]},
    config=config1,
    version="v2"        # ← NEW: har chunk ab typed StreamPart hai
):
    # chunk ab StreamPart TypedDict hai: {type, ns, data} keys hain
    # type: "updates" | "values" | "messages" | "events" etc.
    print(f"[type={chunk['type']}] ns={chunk.get('ns', [])}")
    if chunk["type"] == "updates":
        for node_name, state_update in chunk["data"].items():
            if "messages" in state_update:
                print(f"  Node '{node_name}' response: {state_update['messages'][-1].content[:60]}...")

# ── PATTERN 2: stream(version="v2", stream_mode="values") — Full typed state ──
print("\n=== PATTERN 2: stream_mode='values' + version='v2' ===")
config2 = {"configurable": {"thread_id": "s2"}}
for chunk in graph.stream(
    {"messages": [HumanMessage(content="What is a state machine?")]},
    config=config2,
    stream_mode="values",
    version="v2"        # ← same version param, different mode
):
    # chunk["type"] == "values" hoga, chunk["data"] mein full state hai
    if chunk.get("type") == "values":
        last = chunk["data"]["messages"][-1]
        print(f"[{last.__class__.__name__}] {last.content[:60]}...")

# ── PATTERN 3: astream_events(version="v2") — Token-by-token (same as before) ──
async def token_streaming():
    print("\n=== PATTERN 3: Token-by-Token astream_events ===")
    print("Agent: ", end="", flush=True)
    config3 = {"configurable": {"thread_id": "s3"}}
    async for event in graph.astream_events(
        {"messages": [HumanMessage(content="Write a short poem about AI agents")]},
        config=config3,
        version="v2"    # ← v2 was already here, unchanged
    ):
        if event.get("event") == "on_chat_model_stream":
            token = event["data"]["chunk"].content
            if token:
                print(token, end="", flush=True)
    print()

asyncio.run(token_streaming())

# ── BONUS: invoke(version="v2") — GraphOutput object (NEW in v1.1) ──
print("\n=== BONUS: invoke(version='v2') — GraphOutput ===")
config4 = {"configurable": {"thread_id": "s4"}}
result = graph.invoke(
    {"messages": [HumanMessage(content="Hello!")]},
    config=config4,
    version="v2"        #  NEW: returns GraphOutput object
)
# result ab GraphOutput hai — .value aur .interrupts attributes
print(f"Response: {result.value['messages'][-1].content}")
print(f"Interrupts (agar koi ho): {result.interrupts}")
# result["messages"] bhi kaam karta hai (backward compatible dict-style access)