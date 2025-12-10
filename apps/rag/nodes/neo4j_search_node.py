import os
import json
from typing import List, Optional, Dict
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

# --- Helper for common query structure ---
def execute_hybrid_query(location_keyword: str, facility_labels: str, facility_rel: str, 
                         facility_name_key: str, sort_strategy: str = "dist"):
    """
    Executes a standard "Anchor Location + Target Facility" query.
    
    Args:
        location_keyword: User's location query (e.g. "Hongdae")
        facility_labels: Neo4j labels for target facility (e.g. "Hospital:Pharmacy")
        facility_rel: Relationship type to target (e.g. "NEAR_HOSPITAL|NEAR_PHARMACY")
        facility_name_key: Key for formatting details (e.g. "med_details")
        sort_strategy: "dist" (closest) or "count" (most connections)
    """
    
    # [Revert]: Removed Python-side sanitization (clean_keyword) per user request.
    # We now handle matching logic purely in Cypher for robustness.
    print(f"[Debug] Search: '{location_keyword}' | Facility: {facility_labels}")
    
    # 1. Find Anchor Location (Subway, University, etc.)
    # We allow the anchor to be ANY valid POI type
    # [Fix]: Do NOT limit anchors immediately. We must check for connectivity first.
    # [Fix]: Prioritize SubwayStation via Score Boost later.
    # [Fix]: Bidirectional Matching. 
    #   - Case A: Keyword "Hongdae" matches Name "Hongdae Entrance" (Name CONTAINS Keyword)
    #   - Case B: Keyword "Hongdae Station" matches Name "Hongdae" (Keyword CONTAINS Name)
    anchor_match = """
    MATCH (anchor) 
    WHERE (anchor.name CONTAINS $keyword OR $keyword CONTAINS anchor.name)
      AND (anchor:SubwayStation OR anchor:College OR anchor:Hospital OR anchor:GeneralHospital OR anchor:Park)
    """
    
    # 2. Find Property connected to Anchor AND Target Facility
    # We join directly to ensure only Connected Anchors are used.
    core_query = f"""
    {anchor_match}
    MATCH (p:Property)-[r_anchor]-(anchor)
    WHERE type(r_anchor) STARTS WITH 'NEAR_'
    
    MATCH (p)-[r_fac:{facility_rel}]->(target)
    WHERE (
        '{facility_labels}' = 'ANY' OR
        any(label in labels(target) WHERE label IN split('{facility_labels}', ':'))
    )
    
    // Prioritize SubwayStation anchors for distance calculation if multiple exist for the same property?
    // No, usually a property is near ONE anchor relevant to the search.
    
    WITH p, anchor, r_anchor, target, r_fac
    """
    
    scoring = ""
    if sort_strategy == "count":
        # Safety strategy: Count connections
        score_logic = """
        WITH p, anchor, r_anchor, count(DISTINCT target) as fac_count, 
             collect({name: target.name, dist: coalesce(toInteger(r_fac.distance), 9999), time: coalesce(toInteger(r_fac.walking_time), 9999)})[..5] as fac_details
        WITH p, anchor, r_anchor, fac_count, fac_details, 
             (fac_count * 300) as fac_score
        """
    else:
        # Distance strategy: Closest one wins
        score_logic = """
        WITH p, anchor, r_anchor, target, r_fac ORDER BY coalesce(toInteger(r_fac.distance), 99999) ASC
        WITH p, anchor, r_anchor, count(DISTINCT target) as fac_count,
             collect({name: target.name, dist: coalesce(toInteger(r_fac.distance), 9999), time: coalesce(toInteger(r_fac.walking_time), 9999)}) as all_details
        WITH p, anchor, r_anchor, fac_count, all_details[..3] as fac_details,
             CASE WHEN size(all_details) > 0 THEN (5000 - all_details[0].dist) ELSE 0 END as fac_score
        """
        
    final_return = f"""
    {score_logic}
    
    // Total Score = Anchor Proximity + Facility Score + Anchor Priority (Subway Bonus)
    // [Fix]: Score Boost for SubwayStation to satisfy user preference for "Station" search
    WITH p, anchor, r_anchor, fac_count, fac_details, fac_score, (5000 - coalesce(toInteger(r_anchor.distance), 5000)) as anchor_score,
         CASE WHEN 'SubwayStation' IN labels(anchor) THEN 500 ELSE 0 END as priority_score
         
    WITH p, anchor, fac_count, fac_details, (anchor_score + fac_score + priority_score) as total_score,
         {{name: anchor.name, dist: coalesce(toInteger(r_anchor.distance), 9999), time: coalesce(toInteger(r_anchor.walking_time), 9999)}} as anchor_info
    
    RETURN p.id as id, p.address as address, total_score, 
           [anchor_info] as poi_details,
           fac_details as {facility_name_key}
    ORDER BY total_score DESC LIMIT 300
    """
    
    full_cypher = core_query + final_return
    return get_graph().query(full_cypher, params={"keyword": location_keyword})


# --- DOMAIN TOOLS ---

@tool
def search_properties_near_subway(location_keyword: str):
    """
    Find properties near a specific Subway Station (Transportation).
    Use this when user asks for "Subway", "Station", "Transport".
    """
    # For subway, Anchor IS the Target.
    # We modify the query slightly: Finding properties connected to the Subway node.
    query = """
    MATCH (s:SubwayStation) WHERE (s.name CONTAINS $keyword OR $keyword CONTAINS s.name)
    WITH s LIMIT 3
    MATCH (p:Property)-[r:NEAR_SUBWAY]->(s)
    
    WITH p, s, r, (5000 - coalesce(toInteger(r.distance), 5000)) as total_score
    RETURN p.id as id, p.address as address, total_score,
           collect({name: s.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)}) as poi_details,
           collect({name: s.name, dist: coalesce(toInteger(r.distance), 9999), time: coalesce(toInteger(r.walking_time), 9999)}) as trans_details
    ORDER BY total_score DESC LIMIT 300
    """
    return get_graph().query(query, params={"keyword": location_keyword})

@tool
def search_properties_near_hospital(location_keyword: str, general_only: bool = False):
    """
    Find properties near Hospitals.
    Args:
        location_keyword: The location name (e.g. "Hongdae")
        general_only: If True, searches ONLY 'GeneralHospital/UniversityHospital'. If False, searches all hospitals/pharmacies.
    """
    if general_only:
        # Strict: GeneralHospital
        return execute_hybrid_query(location_keyword, "GeneralHospital", "NEAR_GENERAL_HOSPITAL", "gen_hosp_details", "dist")
    else:
        # Broad: Hospital, GeneralHospital (EXCLUDE Pharmacy)
        return execute_hybrid_query(location_keyword, "ANY", "NEAR_HOSPITAL|NEAR_GENERAL_HOSPITAL", "med_details", "dist")

@tool
def search_properties_near_pharmacy(location_keyword: str):
    """
    Find properties near Pharmacies.
    """
    return execute_hybrid_query(location_keyword, "Pharmacy", "NEAR_PHARMACY", "pharmacy_details", "dist")

@tool
def search_properties_near_convenience(location_keyword: str):
    """
    Find properties near Convenience Stores.
    """
    return execute_hybrid_query(location_keyword, "Convenience", "NEAR_CONVENIENCE", "conv_details", "dist")

@tool
def search_properties_near_park(location_keyword: str):
    """
    Find properties near Parks or Walking areas.
    """
    return execute_hybrid_query(location_keyword, "Park", "NEAR_PARK", "park_details", "dist")

@tool
def search_properties_near_university(location_keyword: str):
    """
    Find properties near Universities/Colleges.
    Uses a specialized query that ONLY matches College nodes as anchors.
    Returns: poi_details = nearby subway station, edu_details = searched university only
    """
    query = """
    MATCH (anchor:College) 
    WHERE (anchor.name CONTAINS $keyword OR $keyword CONTAINS anchor.name)
    
    MATCH (p:Property)-[r_anchor:NEAR_COLLEGE]->(anchor)
    
    // 가장 가까운 지하철역 조회 (역 접근성용)
    OPTIONAL MATCH (p)-[r_sub:NEAR_SUBWAY]->(sub:SubwayStation)
    
    WITH p, anchor, r_anchor, sub, r_sub,
         (5000 - coalesce(toInteger(r_anchor.distance), 5000)) as total_score
    
    RETURN p.id as id, p.address as address, total_score,
           CASE WHEN sub IS NOT NULL 
                THEN [{name: sub.name, dist: coalesce(toInteger(r_sub.distance), 9999), time: coalesce(toInteger(r_sub.walking_time), 9999)}]
                ELSE [] 
           END as poi_details,
           [{name: anchor.name, dist: coalesce(toInteger(r_anchor.distance), 9999), time: coalesce(toInteger(r_anchor.walking_time), 9999)}] as edu_details
    ORDER BY total_score DESC LIMIT 300
    """
    print(f"[Debug] University Search: '{location_keyword}'")
    return get_graph().query(query, params={"keyword": location_keyword})


@tool
def search_properties_with_safety(location_keyword: str):
    """
    Find properties with GOOD SAFETY infrastructure.
    Returns:
    - CCTV/Bell counts (e.g., "CCTV 5개")
    - Police/Fire distance and time (e.g., "경찰서 150m, 도보 2분")
    """
    query = """
    MATCH (anchor) 
    WHERE (anchor.name CONTAINS $keyword OR $keyword CONTAINS anchor.name)
      AND (anchor:SubwayStation OR anchor:College OR anchor:Hospital OR anchor:GeneralHospital OR anchor:Park)
    
    MATCH (p:Property)-[r_anchor]-(anchor)
    WHERE type(r_anchor) STARTS WITH 'NEAR_'
    
    // Count-based: CCTV and Emergency Bell
    OPTIONAL MATCH (p)-[:NEAR_CCTV]->(cctv)
    OPTIONAL MATCH (p)-[:NEAR_BELL]->(bell)
    
    // Distance-based: Police and Fire Station
    OPTIONAL MATCH (p)-[r_police:NEAR_POLICE]->(police)
    OPTIONAL MATCH (p)-[r_fire:NEAR_FIRE]->(fire)
    
    WITH p, anchor, r_anchor,
         count(DISTINCT cctv) as cctv_count,
         count(DISTINCT bell) as bell_count,
         collect(DISTINCT {name: police.name, dist: coalesce(toInteger(r_police.distance), 9999), time: coalesce(toInteger(r_police.walking_time), 9999)})[..3] as police_list,
         collect(DISTINCT {name: fire.name, dist: coalesce(toInteger(r_fire.distance), 9999), time: coalesce(toInteger(r_fire.walking_time), 9999)})[..3] as fire_list
    
    // Filter out null entries from police/fire lists
    WITH p, anchor, r_anchor, cctv_count, bell_count,
         [item in police_list WHERE item.name IS NOT NULL] as police_details,
         [item in fire_list WHERE item.name IS NOT NULL] as fire_details
    
    // Score: Count-based (CCTV + Bell) + Distance-based (Police + Fire proximity) + Anchor proximity
    WITH p, anchor, r_anchor, cctv_count, bell_count, police_details, fire_details,
         (cctv_count * 100 + bell_count * 100) as count_score,
         CASE WHEN size(police_details) > 0 THEN (5000 - police_details[0].dist) ELSE 0 END as police_score,
         CASE WHEN size(fire_details) > 0 THEN (5000 - fire_details[0].dist) ELSE 0 END as fire_score,
         (5000 - coalesce(toInteger(r_anchor.distance), 5000)) as anchor_score,
         CASE WHEN 'SubwayStation' IN labels(anchor) THEN 500 ELSE 0 END as priority_score
    
    WITH p, anchor, cctv_count, bell_count, police_details, fire_details,
         (count_score + police_score + fire_score + anchor_score + priority_score) as total_score,
         {name: anchor.name, dist: coalesce(toInteger(r_anchor.distance), 9999), time: coalesce(toInteger(r_anchor.walking_time), 9999)} as anchor_info
    
    RETURN p.id as id, p.address as address, total_score,
           [anchor_info] as poi_details,
           cctv_count, bell_count, police_details, fire_details
    ORDER BY total_score DESC LIMIT 300
    """
    return get_graph().query(query, params={"keyword": location_keyword})

@tool
def search_properties_multi_criteria(
    location_keyword: str,
    convenience: bool = False,
    hospital: bool = False,
    pharmacy: bool = False,
    safety: bool = False,
    park: bool = False
):
    """
    Find properties that satisfy MULTIPLE facility requirements simultaneously.
    Use when user requests 2+ facility types (e.g., "convenience AND safety").
    Returns properties that have ALL requested facilities nearby.
    """
    
    # Base query: Find anchor and properties
    query = """
    MATCH (anchor) 
    WHERE (anchor.name CONTAINS $keyword OR $keyword CONTAINS anchor.name)
      AND (anchor:SubwayStation OR anchor:College OR anchor:Hospital OR anchor:GeneralHospital OR anchor:Park)
    
    MATCH (p:Property)-[r_anchor]-(anchor)
    WHERE type(r_anchor) STARTS WITH 'NEAR_'
    
    // OPTIONAL MATCH for all possible facilities
    OPTIONAL MATCH (p)-[r_conv:NEAR_CONVENIENCE]->(conv:Convenience)
    OPTIONAL MATCH (p)-[r_hosp:NEAR_HOSPITAL|NEAR_GENERAL_HOSPITAL]->(hosp)
    OPTIONAL MATCH (p)-[r_pharm:NEAR_PHARMACY]->(pharm:Pharmacy)
    OPTIONAL MATCH (p)-[:NEAR_CCTV]->(cctv)
    OPTIONAL MATCH (p)-[:NEAR_BELL]->(bell)
    OPTIONAL MATCH (p)-[r_police:NEAR_POLICE]->(police)
    OPTIONAL MATCH (p)-[r_fire:NEAR_FIRE]->(fire)
    OPTIONAL MATCH (p)-[r_park:NEAR_PARK]->(park_node:Park)
    
    WITH p, anchor, r_anchor,
         count(DISTINCT conv) as conv_count,
         collect(DISTINCT {name: conv.name, dist: coalesce(toInteger(r_conv.distance), 9999), time: coalesce(toInteger(r_conv.walking_time), 9999)})[..3] as conv_list,
         count(DISTINCT hosp) as hosp_count,
         collect(DISTINCT {name: hosp.name, dist: coalesce(toInteger(r_hosp.distance), 9999), time: coalesce(toInteger(r_hosp.walking_time), 9999)})[..3] as hosp_list,
         count(DISTINCT pharm) as pharm_count,
         collect(DISTINCT {name: pharm.name, dist: coalesce(toInteger(r_pharm.distance), 9999), time: coalesce(toInteger(r_pharm.walking_time), 9999)})[..3] as pharm_list,
         count(DISTINCT cctv) as cctv_count,
         count(DISTINCT bell) as bell_count,
         collect(DISTINCT {name: police.name, dist: coalesce(toInteger(r_police.distance), 9999), time: coalesce(toInteger(r_police.walking_time), 9999)})[..3] as police_list,
         collect(DISTINCT {name: fire.name, dist: coalesce(toInteger(r_fire.distance), 9999), time: coalesce(toInteger(r_fire.walking_time), 9999)})[..3] as fire_list,
         count(DISTINCT park_node) as park_count,
         collect(DISTINCT {name: park_node.name, dist: coalesce(toInteger(r_park.distance), 9999), time: coalesce(toInteger(r_park.walking_time), 9999)})[..3] as park_list
    
    // Filter nulls
    WITH p, anchor, r_anchor,
         conv_count, [item in conv_list WHERE item.name IS NOT NULL] as conv_details,
         hosp_count, [item in hosp_list WHERE item.name IS NOT NULL] as hosp_details,
         pharm_count, [item in pharm_list WHERE item.name IS NOT NULL] as pharm_details,
         cctv_count, bell_count,
         [item in police_list WHERE item.name IS NOT NULL] as police_details,
         [item in fire_list WHERE item.name IS NOT NULL] as fire_details,
         park_count, [item in park_list WHERE item.name IS NOT NULL] as park_details
    
    // WHERE: Property must satisfy ALL requested conditions
    WHERE
        (NOT $need_conv OR conv_count > 0) AND
        (NOT $need_hosp OR hosp_count > 0) AND
        (NOT $need_pharm OR pharm_count > 0) AND
        (NOT $need_safety OR (cctv_count + bell_count) > 0) AND
        (NOT $need_park OR park_count > 0)
    
    WITH p, anchor, r_anchor,
         conv_details, hosp_details, pharm_details,
         cctv_count, bell_count, police_details, fire_details,
         park_details,
         (5000 - coalesce(toInteger(r_anchor.distance), 5000)) as anchor_score,
         CASE WHEN 'SubwayStation' IN labels(anchor) THEN 500 ELSE 0 END as priority_score
    
    WITH p, anchor, (anchor_score + priority_score) as total_score,
         {name: anchor.name, dist: coalesce(toInteger(r_anchor.distance), 9999), time: coalesce(toInteger(r_anchor.walking_time), 9999)} as anchor_info,
         conv_details, hosp_details, pharm_details,
         cctv_count, bell_count, police_details, fire_details, park_details
    
    RETURN p.id as id, p.address as address, total_score,
           [anchor_info] as poi_details,
           conv_details, hosp_details as med_details, pharm_details as pharmacy_details,
           cctv_count, bell_count, police_details, fire_details,
           park_details
    ORDER BY total_score DESC LIMIT 300
    """
    
    params = {
        "keyword": location_keyword,
        "need_conv": convenience,
        "need_hosp": hospital,
        "need_pharm": pharmacy,
        "need_safety": safety,
        "need_park": park
    }
    
    return get_graph().query(query, params=params)

# --- Agent Function ---

def search(state: RAGState):
    """
    Agentic Search 4.0: Granular Tool Selection
    """
    question = state["question"]
    print(f"[Agent] Starting search for: {question}")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    tools = [
        search_properties_near_subway,
        search_properties_near_hospital,
        search_properties_near_pharmacy,
        search_properties_near_convenience,
        search_properties_near_park,
        search_properties_near_university,
        search_properties_with_safety,
        search_properties_multi_criteria
    ]
    llm_with_tools = llm.bind_tools(tools)

    messages = [
        SystemMessage(content="""
        You are a smart real estate assistant.
        
        **CRITICAL SAFETY RULE** (HIGHEST PRIORITY - CHECK THIS FIRST):
        If the question contains ANY of these safety keywords:
        - Korean: 안전, 치안, CCTV, 경찰서, 소방서, 비상벨, 안심, 안심벨
        - English: safety, secure, police, fire, CCTV, emergency, bell
        
        →  **IMMEDIATELY** call `search_properties_with_safety(location_keyword="...")`
        →  Do NOT consider other tools
        →  Location keyword: Extract from question OR use previous location context
        →  This OVERRIDES all other tool selection logic
        
        Examples:
        - "안전한 방이었으면 좋겠어" → `search_properties_with_safety(location_keyword="홍대입구")`
        - "주변에 CCTV 많은 곳" → `search_properties_with_safety(location_keyword="...")`
        - "치안이 좋은 곳" → `search_properties_with_safety(location_keyword="...")`
        
        **Your Goal**: Select the MOST RELEVANT search tool based on the user's facility requirement.
        
        **Strategy**:
        1. **Identify the Location** in the query (e.g., "Hongdae", "Gangnam").
        2. **Identify the Facility** they are interested in.
        3. **Call the specific tool** for that facility using the Location.
        
        **CRITICAL: Location Disambiguation**:
        - **University Keywords** ("대학교", "대학", "University", "College"):
          → Extract location WITHOUT suffix (e.g., "서울대학교" → "서울대")
          → Use `search_properties_near_university(location_keyword="서울대")`
          → **NEVER** use subway tool for university queries!
        
        - **Station Keywords** ("역", "Station", just location name without suffix):
          → Use location as-is (e.g., "홍대입구", "서울역")
          → Use `search_properties_near_subway(location_keyword="...")`
        
        - **Priority Rule**: If query contains BOTH "대학" AND other facilities → University is the LOCATION, other facility is the TARGET
          Example: "서울대 근처 편의점" → `search_properties_near_convenience(location_keyword="서울대")`
        
        **Tool Guide**:
        - **Single Facility Searches**:
          - **Subway/Station** -> `search_properties_near_subway`
          - **Hospital** -> `search_properties_near_hospital`
             - If "General Hospital" or "University Hospital" mentioned -> Set `general_only=True`.
             - Otherwise -> `general_only=False`.
          - **Pharmacy/Drugstore** -> `search_properties_near_pharmacy`
          - **Convenience Store** -> `search_properties_near_convenience`
          - **Park/Walk** -> `search_properties_near_park`
          - **University/College** -> `search_properties_near_university`
          - **Safety/CCTV/Police/Bell** -> `search_properties_with_safety`
        
        - **Multi-Facility Searches** (2+ requirements):
          - If user requests **MULTIPLE facility types** (e.g., "convenience AND safety", "hospital AND park"):
            -> Use `search_properties_multi_criteria(location_keyword, convenience=True/False, hospital=True/False, pharmacy=True/False, safety=True/False, park=True/False)`
          - Set each facility parameter to `True` if requested, `False` otherwise
          - Example: "홍대 근처 편의점 가깝고 안전한 방" -> `search_properties_multi_criteria(location_keyword="홍대", convenience=True, safety=True)`
        
        **Multi-intent Strategy (Hybrid Queries)**:
        - **"Station + Safety"** (e.g., "Safe room near Hongdae Stn"):
          - The "Station" part is the **Location**.
          - The "Safety" part is the **Priority**.
          - Action: Call `search_properties_with_safety(location_keyword="Hongdae")`. 
          - Why? The tool AUTOMATICALLY scores by distance to the location (Station) AND safety count.
        
        - **"Station + Convenience"** (e.g., "Conv store near Hongdae"):
          - Action: Call `search_properties_near_convenience(location_keyword="Hongdae")`.
        
        **Handling Generic Queries (Room/House Only)**:
        - If user asks for "Room", "House", "One-room", "Listing" + Location (e.g. "Hongdae room", "Recommend room near Gangnam"):
          - **DEFAULT ACTION**: Call `search_properties_near_subway(location_keyword="...")`.
          - Why? "Near a location" usually implies "Near the Station" for that location. The user wants the best properties in that area.
          - Do NOT stop. Do NOT ask for more info. JUST SEARCH.

        **Handling Missing Location**:
        - If the user asks for facilities (e.g., "Safe room", "Near hospital") **WITHOUT mentioning a specific location/station**:
          - **STOP**. Do NOT call any search tool.
          - **Reply**: "어느 지역이나 지하철역 근처를 찾으시나요? (예: 홍대입구역, 강남역)"
          - Reason: A reference point is required to measure distance/connections.
        
        **Rule of Thumb**:
        Always pick the tool that matches the **Facility/Attribute** user asked for. 
        The **Location** (Station/University) is just the input argument for that tool.
        """),
        HumanMessage(content=question)
    ]

    max_steps = 5
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
                t_name = tool_call['name']
                t_args = tool_call['args']
                print(f"[Agent] 🛠️ Calling Tool: {t_name}")
                
                tool_output = None
                
                if t_name == "search_properties_near_subway":
                    tool_output = search_properties_near_subway.invoke(t_args)
                elif t_name == "search_properties_near_hospital":
                    tool_output = search_properties_near_hospital.invoke(t_args)
                elif t_name == "search_properties_near_pharmacy":
                    tool_output = search_properties_near_pharmacy.invoke(t_args)
                elif t_name == "search_properties_near_convenience":
                    tool_output = search_properties_near_convenience.invoke(t_args)
                elif t_name == "search_properties_near_park":
                    tool_output = search_properties_near_park.invoke(t_args)
                elif t_name == "search_properties_near_university":
                    tool_output = search_properties_near_university.invoke(t_args)
                elif t_name == "search_properties_with_safety":
                    tool_output = search_properties_with_safety.invoke(t_args)
                elif t_name == "search_properties_multi_criteria":
                    tool_output = search_properties_multi_criteria.invoke(t_args)
                
                if isinstance(tool_output, list):
                    found_properties.extend(tool_output)
                
                print(f"[Agent]    Output count: {len(tool_output) if isinstance(tool_output, list) else 0}") 
                messages.append(ToolMessage(content=json.dumps(tool_output, default=str), tool_call_id=tool_call["id"]))
        
        except Exception as e:
            print(f"[Agent] Error in loop: {e}")
            break

    # Deduplicate properties (if multiple tools used)
    unique_props = {p['id']: p for p in found_properties}.values() if found_properties else []
    
    return {
        "graph_results": list(unique_props),
        "graph_summary": messages[-1].content
    }
