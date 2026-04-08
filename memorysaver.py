from dotenv import load_dotenv
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage , SystemMessage



load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
SYSTEM_PROMPT = "You are a helpful customer support agent for TechFlow SaaS."

def agent_node(state: MessagesState) -> dict:
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
    response = llm.invoke(messages)
    return {"messages": [response]}

builder = StateGraph(MessagesState)
builder.add_node("agent", agent_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)

memory = MemorySaver()  # In-memory checkpointer
graph = builder.compile(checkpointer=memory)  # KEY: checkpointer pass karo

def chat(user_input: str, thread_id: str) -> str:
    config = {"configurable": {"thread_id": thread_id}}  # thread_id mandatory hai
    result = graph.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
    return result["messages"][-1].content

# Thread 1: User A
print("=== USER A (thread: user_001) ===")
qs1 = "User A: Hi, my name is Rahul. I have login issues."
print(qs1)
print(f"Agent: {chat(qs1, 'user_001')}\n")

qs2 = "User A: The reset email is not coming."
print(qs2)
print(f"Agent: {chat(qs2, 'user_001')}\n")

qs3 = "User A: What is my name"
print(qs3)
print(f"Agent: {chat(qs3, 'user_001')}\n")  

snap = graph.get_state({"configurable": {"thread_id": "user_001"}})
print(f"\nThread user_001 message count: {len(snap.values['messages'])}")

# Thread 2: User B — completely isolated
print("\n=== USER B (thread: user_002) ===")
qst1 ="User B: Hello.Need help with the billing."
print(qst1)
print(f"Agent: {chat(qst1, 'user_002')}\n")

qst2 = "User B : 'What was the previous user asking?"
print(qst2)
print(f"Agent: {chat(qst2, 'user_002')}\n")  # No info about thread 1

# State inspection
snap = graph.get_state({"configurable": {"thread_id": "user_002"}})
print(f"\nThread user_002 message count: {len(snap.values['messages'])}")