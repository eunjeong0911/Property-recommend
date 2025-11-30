import os
from langchain_community.graphs import Neo4jGraph
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from common.state import RAGState

def search(state: RAGState):
    """
    Search Neo4j database using GraphCypherQAChain
    """
    question = state["question"]
    
    # Initialize Neo4j Graph
    # We use environment variables for connection details
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
        username=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password")
    )
import os
from langchain_community.graphs import Neo4jGraph
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from common.state import RAGState

def search(state: RAGState):
    """
    Search Neo4j database using GraphCypherQAChain
    """
    question = state["question"]
    
    # Initialize Neo4j Graph
    # We use environment variables for connection details
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
        username=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password")
    )

    # Initialize LLM (GPT-5-nano)
    llm = ChatOpenAI(model="gpt-5-nano", temperature=0)

    # Create Cypher QA Chain
    # This chain converts natural language to Cypher queries
    from langchain_core.prompts import PromptTemplate

    CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

The user is looking for real estate properties.
When the user asks for "house", "home", "room", "property", or "listing", you MUST query the `Property` node.
To find properties near a specific location type, use the following relationships:
- Near Subway Station: (:Property)-[:NEAR_SUBWAY]->(:SubwayStation)
- Near University/College: (:Property)-[:NEAR_COLLEGE]->(:College)
- Near Hospital: (:Property)-[:NEAR_GENERAL_HOSPITAL]->(:GeneralHospital) or (:Property)-[:NEAR_HOSPITAL]->(:Hospital)
- Near Park: (:Property)-[:NEAR_PARK]->(:Park)
- Near Convenience Store: (:Property)-[:NEAR_CONVENIENCE]->(:Convenience)

Example 1: "Find a house near Gangnam Station"
MATCH (p:Property)-[:NEAR_SUBWAY]->(s:SubwayStation)
WHERE s.name CONTAINS 'Gangnam'
RETURN p.address, p.bldg_type, p.trade_type_raw, s.name as station_name
LIMIT 5

Example 2: "Find a property near Yonsei University"
MATCH (p:Property)-[:NEAR_COLLEGE]->(c:College)
WHERE c.name CONTAINS 'Yonsei'
RETURN p.address, p.bldg_type, p.trade_type_raw, c.name as college_name
LIMIT 5

The question is:
{question}"""

    CYPHER_GENERATION_PROMPT = PromptTemplate(
        input_variables=["schema", "question"], 
        template=CYPHER_GENERATION_TEMPLATE
    )

    chain = GraphCypherQAChain.from_llm(
        llm, 
        graph=graph, 
        verbose=True,
        allow_dangerous_requests=True,
        cypher_prompt=CYPHER_GENERATION_PROMPT
    )

    try:
        # Run the chain
        result = chain.invoke({"query": question})
        return {"graph_results": [result["result"]]}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in Neo4j search: {e}")
        return {"graph_results": [f"Error executing graph search: {e}"]}
