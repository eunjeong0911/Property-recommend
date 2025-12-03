import os
from langchain_community.graphs import Neo4jGraph
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from common.state import RAGState

def search(state: RAGState):
    """
    Search Neo4j database using GraphCypherQAChain
    """
    question = state["question"]
    
    # Initialize Neo4j Graph
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
        username=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password")
    )

    # Initialize LLM (GPT-5-mini)
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)

    CYPHER_GENERATION_TEMPLATE = """Task: 사용자 질문을 분석하여 GraphDB 조회 Cypher 쿼리를 생성하세요.

Schema:
{schema}

핵심 원칙:
1. 사용자 질문 분석
   - 질문에서 언급된 모든 조건(역, 시설, 건물 유형 등)을 WHERE 절에 반영
   - 언급된 시설은 OPTIONAL MATCH로 조회

2. 정확성 최우선 (Hallucination 금지)
   - 스키마에 없는 관계나 속성은 절대 사용 금지
   - 확실한 데이터만 조회

3. CCTV/비상벨 집계 (100m 범위 내 노드 개수)
   - **질문에 'CCTV' 또는 '비상벨' 중 하나라도 언급되면, 반드시 두 가지 모두 집계하세요.**
   - 카르테시안 프로덕트 방지: WITH 절로 단계별 집계
   - 패턴:
     ```
     OPTIONAL MATCH (p)-[:NEAR_CCTV]->(cctv)
     WITH p, s, count(DISTINCT cctv) as cctv_count
     OPTIONAL MATCH (p)-[:NEAR_BELL]->(bell)  
     WITH p, s, cctv_count, count(DISTINCT bell) as bell_count
     ```

4. 시설 정보는 3가지 세트 (이름 + 거리 + 도보시간)
   - 반드시: `facility.name, r.distance, r.walking_time` 모두 RETURN
   - 예: `c.name as convenience_name, r2.distance as convenience_dist, r2.walking_time as convenience_time`

5. **지하철역 정보는 항상 조회 (Always retrieve Subway Info)**
   - 사용자가 언급하지 않아도 `OPTIONAL MATCH (p)-[r_sub:NEAR_SUBWAY]->(s:SubwayStation)`을 사용하여 조회하고 반환하세요.
   - 단, 이미 `MATCH (p)-[r:NEAR_SUBWAY]->(s:SubwayStation)`을 사용했다면 중복해서 `OPTIONAL MATCH` 하지 마세요.

6. **'원룸', '자취방' 등 통칭 검색 시 모든 건물 유형 조회 (Relax Building Type Filter)**
   - 사용자가 '원룸', '자취방' 등 주거 형태를 통칭하는 단어를 언급하더라도 `WHERE p.bldg_type = ...` 조건을 추가하지 마세요.
   - 아파트, 오피스텔, 빌라, 원룸 등 모든 건물 유형을 검색 대상에 포함하세요.

7. **우선순위 추천 (Priority Recommendation)**
   - 질문에 특정 시설(역, 편의점, 병원 등)이 언급되면, 해당 시설과 **가까운 순서(거리 또는 도보시간 오름차순)**로 정렬하세요.
   - 상위 **3개** 매물만 추천하세요 (`LIMIT 3`).

필수 RETURN 항목:
- p.id (매물 ID - 필수!)
- p.address, p.bldg_type
- p.trade_type_raw (가격 정보 - "월세 1,000만원/70만원" 형식)
- p.deposit, p.monthly_rent, p.maintenance_fee
- **s.name as subway_station_name, r_sub.distance (or r.distance) as subway_station_dist, r_sub.walking_time (or r.walking_time) as subway_station_time** (지하철 정보 필수)
- 질문에 언급된 시설의 name, distance, walking_time
- cctv_count, bell_count (질문에 언급 시)

Note: Cypher 쿼리만 반환하세요.

예시 1: "강남역 근처 집 찾아줘"
MATCH (p:Property)-[r:NEAR_SUBWAY]->(s:SubwayStation)
WHERE s.name CONTAINS '강남'
RETURN p.id, p.address, p.bldg_type, p.trade_type_raw, p.deposit, p.monthly_rent, p.maintenance_fee, s.name as subway_station_name, r.walking_time as subway_station_time, r.distance as subway_station_dist
ORDER BY r.distance ASC
LIMIT 3

예시 2: "홍대역 근처 도보 10분 이내 원룸 찾아줘"
MATCH (p:Property)-[r:NEAR_SUBWAY]->(s:SubwayStation)
WHERE s.name CONTAINS '홍대' OR s.name CONTAINS '홍익'
AND r.walking_time <= 10
RETURN p.id, p.address, p.bldg_type, p.trade_type_raw, p.deposit, p.monthly_rent, p.maintenance_fee, s.name as subway_station_name, r.walking_time as subway_station_time, r.distance as subway_station_dist
ORDER BY r.walking_time ASC
LIMIT 3

예시 3: "신촌역 도보 15분 이내이고 병원 가까운 원룸 찾아줘"
MATCH (p:Property)-[r1:NEAR_SUBWAY]->(s:SubwayStation)
WHERE s.name CONTAINS '신촌' AND r1.walking_time <= 15
OPTIONAL MATCH (p)-[r2:NEAR_GENERAL_HOSPITAL|NEAR_HOSPITAL]->(h)
RETURN p.id, p.address, p.bldg_type, p.deposit, p.monthly_rent, p.maintenance_fee,
       s.name as subway_station_name, 
       r1.distance as subway_station_dist, 
       r1.walking_time as subway_station_time,  
       h.name as hospital_name, 
       r2.distance as hospital_dist, 
       r2.walking_time as hospital_time
ORDER BY r2.distance ASC, r1.walking_time ASC
LIMIT 3

예시 4: "홍대입구역 근처 편의점 가까운 오피스텔 찾아줘"
MATCH (p:Property)-[r1:NEAR_SUBWAY]->(s:SubwayStation)
WHERE s.name CONTAINS '홍대' AND p.bldg_type = '오피스텔'
OPTIONAL MATCH (p)-[r2:NEAR_CONVENIENCE]->(c)
RETURN p.id, p.address, p.bldg_type, p.deposit, p.monthly_rent, p.maintenance_fee,
       s.name as subway_station_name, 
       r1.distance as subway_station_dist, 
       r1.walking_time as subway_station_time,
       c.name as convenience_name, 
       r2.distance as convenience_dist, 
       r2.walking_time as convenience_time
ORDER BY r2.distance ASC, r1.walking_time ASC
LIMIT 3

예시 5: "보증금 1000만원 이하 월세 찾아줘" (지하철 언급 없음 -> OPTIONAL MATCH 사용)
MATCH (p:Property)
WHERE p.deposit <= 1000 AND p.monthly_rent > 0
OPTIONAL MATCH (p)-[r_sub:NEAR_SUBWAY]->(s:SubwayStation)
RETURN p.id, p.address, p.bldg_type, p.trade_type_raw, p.deposit, p.monthly_rent, p.maintenance_fee,
       s.name as subway_station_name,
       r_sub.distance as subway_station_dist,
       r_sub.walking_time as subway_station_time
ORDER BY p.monthly_rent ASC
LIMIT 3

질문:
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
