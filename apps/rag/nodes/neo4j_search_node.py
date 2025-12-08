import os
import json
from typing import List, Optional
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from common.state import RAGState

# Neo4j Connection (Lazy Loading)
_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = Neo4jGraph(
            url=os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
            username=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password")
        )
    return _graph

@tool
def search_poi(keyword: str):
    """
    Search for Points of Interest (POI) by name keyword.
    Useful for identifying Subway Stations, Universities, Parks, etc. mentioned by the user.
    Args:
        keyword: The name to search for (e.g., "홍대", "연세", "서울대")
    Returns: List of matching nodes with id, name, and type.
    """
    query = """
    MATCH (n)
    WHERE n.name CONTAINS $keyword AND (
          n:SubwayStation OR n:College OR n:Hospital OR 
          n:GeneralHospital OR n:Park OR n:PoliceStation OR n:FireStation
    )
    RETURN elementId(n) as id, labels(n)[0] as type, n.name as name
    LIMIT 5
    """
    try:
        results = get_graph().query(query, params={"keyword": keyword})
        # Standardize ID if needed, but elementId or internal ID is fine for matching later
        # Some imported nodes have specific 'id' property, let's try to return that first
        
        refined_results = []
        for r in results:
            # Re-fetch specifically to get the business ID property if it exists
            node_type = r['type']
            name = r['name']
            
            # Dynamic query to get the specific business ID
            id_query = f"MATCH (n:{node_type}) WHERE elementId(n) = $eid RETURN n.id as biz_id"
            id_res = get_graph().query(id_query, params={"eid": r['id']})
            biz_id = id_res[0]['biz_id'] if id_res and id_res[0].get('biz_id') else r['id']
            
            refined_results.append({
                "type": node_type,
                "name": name,
                "id": biz_id, # This ID will be used in match_properties
                "element_id": r['id']
            })
            
        return refined_results
    except Exception as e:
        return f"Error searching POI: {e}"

@tool
def match_properties(poi_ids: List[str], requirements: List[str] = []):
    """
    Find properties that are close to ALL specified POIs (Intersection Search).
    Also considers optional requirements like 'convenience_store', 'cctv', 'pharmacy', 'bus'.
    
    Args:
        poi_ids: List of POI IDs (or names/element_ids from search_poi) to match.
                 The property must be connected to ALL of these POIs.
        requirements: Optional list of other facilities to check (e.g., ['convenience', 'cctv', 'pharmacy', 'bus']).
                      These act as weighted bonuses or soft filters.
    
    Returns: List of properties with total score (lower score = better/closer).
    """
    if not poi_ids:
        return "No POI IDs provided."

    # Dynamic Cypher Construction
    match_clauses = []
    where_clauses = []
    with_clauses = ["p"]
    score_parts = []
    
    # 1. Match Property and POIs
    for i, pid in enumerate(poi_ids):
        # We try to match by ID property first
        # Since we don't know the exact label of the target POI easily without query, 
        # we can match generic node with that ID. 
        # However, our graph schema links Property -> specific Label via specific Relationship.
        # To make this robust, we relax the relationship type or try multiple.
        # BUT, standard approach: Property -> NEAR_* -> Node
        # Let's assume the ID is unique across these specific nodes or we rely on the implementation plan's assumption.
        
        # Optimized approach: We know the relationship types generally start with NEAR_
        # We can use a broad match.
        
        target_var = f"target{i}"
        rel_var = f"r{i}"
        
        # We assume 'pid' is the business ID string.
        match_clauses.append(f"MATCH (p:Property)-[{rel_var}]->({target_var})")
        where_clauses.append(f"({target_var}.id = '{pid}' OR {target_var}.name = '{pid}')") # Fallback to name if ID fails
        where_clauses.append(f"type({rel_var}) STARTS WITH 'NEAR_'")
        
        score_parts.append(f"{rel_var}.distance") # Simple sum of distances
        
        with_clauses.append(target_var)
        with_clauses.append(rel_var)

    # 2. Optional Requirements
    optional_matches = ""
    req_score_adjustments = []
    
    valid_reqs = {
        "convenience": ("NEAR_CONVENIENCE", "Convenience"),
        "cctv": ("NEAR_CCTV", "CCTV"),
        "bell": ("NEAR_BELL", "EmergencyBell"),
        "pharmacy": ("NEAR_PHARMACY", "Pharmacy"),
        "bus": ("NEAR_BUS", "BusStation")
    }
    
    for req in requirements:
        req_key = req.lower()
        if req_key in valid_reqs:
            rel_type, node_label = valid_reqs[req_key]
            # If present, -500 points (bonus)
            # Using count to verify existence
            optional_matches += f"""
            OPTIONAL MATCH (p)-[:{rel_type}]->({req_key}_node:{node_label})
            """
            req_score_adjustments.append(f"(CASE WHEN {req_key}_node IS NOT NULL THEN -500 ELSE 0 END)")

    # Construct final query
    final_query = "\n".join(match_clauses)
    if where_clauses:
        final_query += "\nWHERE " + " AND ".join(where_clauses)
    
    final_query += optional_matches
    
    score_expr = " + ".join(score_parts)
    if req_score_adjustments:
        score_expr += " + " + " + ".join(req_score_adjustments)
        
    final_query += f"\nWITH p, {score_expr} as score"
    final_query += "\nRETURN p.id as id, p.address as address, score\nORDER BY score ASC\nLIMIT 5"
    
    try:
        return get_graph().query(final_query)
    except Exception as e:
        return f"Error matching properties: {e}"

@tool
def find_stations_by_name(keyword: str):
    """
    Search for subway stations by name keyword.
    Returns: List of {name, line, id} for matching stations.
    Useful when you need to find a starting point for location-based search.
    """
    query = """
    MATCH (s:SubwayStation)
    WHERE s.name CONTAINS $keyword
    RETURN s.name as name, s.id as id
    LIMIT 5
    """
    try:
        return get_graph().query(query, params={"keyword": keyword})
    except Exception as e:
        return f"Error finding stations: {e}"

@tool
def find_nearby_properties(station_name: str, max_distance: int = 1500, limit: int = 5):
    """
    Find properties near a specific subway station.
    Args:
        station_name: Exact name of the subway station (e.g., '강남', '홍대입구')
        max_distance: Maximum distance in meters (default: 1500)
        limit: Maximum number of properties to return (default: 5)
    Returns: List of properties with ID, address, and distance info.
    """
    query = """
    MATCH (p:Property)-[r:NEAR_SUBWAY]->(s:SubwayStation)
    WHERE s.name CONTAINS $station_name AND r.distance <= $max_distance
    RETURN p.id as id, p.address as address, s.name as station, r.distance as distance, r.walking_time as walking_time
    ORDER BY r.distance ASC
    LIMIT $limit
    """
    try:
        return get_graph().query(query, params={"station_name": station_name, "max_distance": max_distance, "limit": limit})
    except Exception as e:
        return f"Error finding properties: {e}"

@tool
def find_nearby_facilities(property_id: str):
    """
    Get nearby facilities (Hospital, University, Police, Fire Station, Park, Convenience Store) for a specific property.
    This tool provides general infrastructure information around the property.
    Args:
        property_id: The ID of the property
    Returns: Lists of nearby facilities with distance information.
    """
    # Define facility types and their relationships
    # Using specific defaults as per data import matching logic
    facilities = [
        {"type": "GeneralHospital", "rel": "NEAR_GENERAL_HOSPITAL", "name": "General Hospitals"},
        {"type": "Hospital", "rel": "NEAR_HOSPITAL", "name": "Hospitals"},
        {"type": "Pharmacy", "rel": "NEAR_PHARMACY", "name": "Pharmacies"},
        {"type": "College", "rel": "NEAR_COLLEGE", "name": "Universities"},
        {"type": "PoliceStation", "rel": "NEAR_POLICE", "name": "Police Stations"},
        {"type": "FireStation", "rel": "NEAR_FIRE", "name": "Fire Stations"},
        {"type": "Park", "rel": "NEAR_PARK", "name": "Parks"},
        {"type": "Convenience", "rel": "NEAR_CONVENIENCE", "name": "Convenience Stores"},
        {"type": "BusStation", "rel": "NEAR_BUS", "name": "Bus Stations"}
    ]
    
    results = {}
    graph = get_graph()
    
    for fac in facilities:
        query = f"""
        MATCH (p:Property {{id: $property_id}})-[r:{fac['rel']}]->(f)
        RETURN f.name as name, r.distance as distance, r.walking_time as walking_time
        ORDER BY r.distance ASC
        LIMIT 3
        """
        try:
            res = graph.query(query, params={"property_id": property_id})
            if res:
                results[fac['name']] = res
        except Exception as e:
            results[fac['name']] = f"Error: {e}"
            
    return results

@tool
def get_property_surroundings(property_id: str):
    """
    Get safety information (CCTV, Emergency Bell) for a specific property.
    Args:
        property_id: The ID of the property
    Returns: Counts of safety facilities near the property.
    """
    # Safety (CCTV, Bell)
    safety_query = """
    MATCH (p:Property {id: $property_id})
    OPTIONAL MATCH (p)-[:NEAR_CCTV]->(cctv)
    WITH p, count(DISTINCT cctv) as cctv_count
    OPTIONAL MATCH (p)-[:NEAR_BELL]->(bell)
    RETURN cctv_count, count(DISTINCT bell) as bell_count
    """
    
    try:
        safety_res = get_graph().query(safety_query, params={"property_id": property_id})
        return {
            "safety": safety_res[0] if safety_res else {}
        }
    except Exception as e:
        return f"Error getting surroundings: {e}"

def search(state: RAGState):
    """
    Agentic Search for Neo4j.
    Uses defined tools to explore the graph based on user question.
    """
    question = state["question"]
    print(f"[Agent] Starting search for: {question}")

    # 1. Initialize LLM with Tools
    # Using gpt-4o as it is more capable of complex tool usage
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = [
        search_poi, match_properties, 
        find_stations_by_name, find_nearby_properties, 
        find_nearby_facilities, get_property_surroundings
    ]
    llm_with_tools = llm.bind_tools(tools)

    # 2. Build Messages
    messages = [
        SystemMessage(content="""
        You are a smart real estate assistant with direct access to a graph database via tools.
        Your goal is to find property IDs and key location info to answer the user's request.
        
        Key Strategy for Multi-Condition Search:
        - If the user mentions MULTIPLE locations (e.g., "Near Yonsei Univ AND Sinchon Station"), use the **Intersection Strategy**:
          1. Call `search_poi` for EACH location to get their IDs. (e.g. search_poi("Yonsei"), search_poi("Sinchon"))
          2. Call `match_properties` with the list of collected IDs. This finds properties connected to ALL of them.
        
        - If the user mentions only ONE location (e.g., "Near Gangnam Station"):
          1. Use `find_stations_by_name` (if it's a station) or `search_poi`.
          2. Use `find_nearby_properties` or `match_properties` with single ID.
        
        - ALWAYS check `find_nearby_facilities` for the found properties to enrich the answer with info about hospitals, parks, etc.
        
        Process:
        1. Identify intent & locations.
        2. Execute Search Tools (Intersection Strategy is preferred for complex queries).
        3. Enrich with `find_nearby_facilities` (mandatory) and `get_property_surroundings` (if safety mentioned).
        4. COMPLETE THE TASK by returning a JSON-like summary.

        IMPORTANT:
        - The user wants the 'raw data' feeling, so clearly state what you found from the tools.
        - Your final answer MUST include the list of found property IDs.
        """),
        HumanMessage(content=question)
    ]

    # 3. Agent Loop (Simple ReAct Loop)
    max_steps = 10
    found_properties = []
    
    for step in range(max_steps):
        print(f"--- Step {step + 1} ---")
        try:
            ai_msg = llm_with_tools.invoke(messages)
            messages.append(ai_msg)

            if ai_msg.content:
                print(f"[Agent] 🧠 Thought: {ai_msg.content}")

            if not ai_msg.tool_calls:
                print("[Agent] ⏹️ No more tool calls. Done.")
                break

            for tool_call in ai_msg.tool_calls:
                print(f"[Agent] 🛠️ Calling Tool: {tool_call['name']}")
                print(f"[Agent]    Args: {tool_call['args']}")
                
                tool_output = None
                if tool_call["name"] == "search_poi":
                    tool_output = search_poi.invoke(tool_call["args"])
                elif tool_call["name"] == "match_properties":
                    tool_output = match_properties.invoke(tool_call["args"])
                    if isinstance(tool_output, list):
                        found_properties.extend(tool_output)
                elif tool_call["name"] == "find_stations_by_name":
                    tool_output = find_stations_by_name.invoke(tool_call["args"])
                elif tool_call["name"] == "find_nearby_properties":
                    tool_output = find_nearby_properties.invoke(tool_call["args"])
                    # Collect found properties for final result
                    if isinstance(tool_output, list):
                        found_properties.extend(tool_output)
                elif tool_call["name"] == "find_nearby_facilities":
                    tool_output = find_nearby_facilities.invoke(tool_call["args"])
                    # Merge facility info into found_properties
                    p_id = tool_call["args"].get("property_id")
                    if p_id:
                        for prop in found_properties:
                            # Handle both raw id (int or str) and standardized string logic if needed
                            # The tool returns id as whatever Neo4j returns.
                            if str(prop.get('id')) == str(p_id):
                                prop['facilities'] = tool_output
                                break
                elif tool_call["name"] == "get_property_surroundings":
                    tool_output = get_property_surroundings.invoke(tool_call["args"])
                    # Merge safety info into found_properties
                    p_id = tool_call["args"].get("property_id")
                    if p_id:
                        for prop in found_properties:
                            if str(prop.get('id')) == str(p_id):
                                prop['surroundings'] = tool_output
                                break
                
                print(f"[Agent]    Output: {str(tool_output)[:300]}...") # Log output preview
                messages.append(ToolMessage(content=json.dumps(tool_output, default=str), tool_call_id=tool_call["id"]))
        
        except Exception as e:
            print(f"[Agent] Error in loop: {e}")
            break

    # 4. Final Response Construction
    # We return the collected raw results to be compatible with the rest of the RAG pipeline
    # The 'graph_summary' will be the final AI message which explains what it found.
    
    # Deduplicate properties by ID
    unique_props = {p['id']: p for p in found_properties}.values() if found_properties else []
    
    return {
        "graph_results": list(unique_props),
        "graph_summary": messages[-1].content
    }
