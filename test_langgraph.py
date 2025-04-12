from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph
from typing import Dict, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_langgraph_setup():
    """
    Test basic LangGraph functionality with a simple chain
    """
    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Create a simple state type for the graph
    def agent_node(state: Dict) -> Dict:
        messages = state.get("messages", [])
        system_message = SystemMessage(content="You are a helpful assistant.")
        response = llm.invoke([system_message] + messages)
        return {"messages": messages + [response]}

    # Create the graph
    workflow = StateGraph(nodes=[])
    
    # Add the agent node
    workflow.add_node("agent", agent_node)
    
    # Add the starting point
    workflow.set_entry_point("agent")
    
    # Compile the graph
    chain = workflow.compile()
    
    # Test the chain
    result = chain.invoke({
        "messages": [HumanMessage(content="Say hello!")]
    })
    
    print("Test successful! Response:", result)
    return result

if __name__ == "__main__":
    test_langgraph_setup() 