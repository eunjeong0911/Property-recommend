# Implementation Plan

- [x] 1. Set up Neo4j database schema and spatial indexes


  - Create Cypher script to define all node types (Listing, University, Hospital, Park, CommercialFacility, BusStop, SubwayStation)
  - Create spatial indexes on location properties for all node types
  - Add script to infra/neo4j/init.cypher
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] 2. Implement data import pipeline for facilities and listings
  - [x] 2.1 Create base import utilities


    - Write helper functions for reading CSV, JSON, and Excel files
    - Implement coordinate validation and point geometry creation
    - Create Neo4j batch import utilities
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [x] 2.2 Write property test for coordinate validation


    - **Property 13: Data import completeness**
    - **Validates: Requirements 5.1, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6**

  - [x] 2.3 Implement university data import


    - Parse data/교육부_대학교 주소기반 좌표정보_20241030.xlsx
    - Create University nodes with name, campus, address, location
    - _Requirements: 10.1_

  - [x] 2.4 Implement hospital data import

    - Parse data/전국 병의원 및 약국 현황 2025.9/*.csv files
    - Create Hospital nodes with name, type, address, location
    - _Requirements: 10.2_

  - [x] 2.5 Implement park data import

    - Parse data/서울시_도시공원정보/*.csv files
    - Create Park nodes with name, area, address, location
    - _Requirements: 10.3_

  - [x] 2.6 Implement commercial facility data import

    - Parse data/소상공인시장진흥공단_상가(상권)정보_20251030/*.csv
    - Create CommercialFacility nodes with name, business_type_code, address, location
    - _Requirements: 10.4_

  - [x] 2.7 Implement bus stop data import

    - Parse data/국토교통부_전국 버스정류장 위치정보_20241031_utf8.csv
    - Create BusStop nodes with name, address, location
    - _Requirements: 10.5_

  - [x] 2.8 Implement subway station data import

    - Parse data/지하철_노선도.csv
    - Create SubwayStation nodes with name, line, address, location
    - _Requirements: 10.6_

  - [x] 2.9 Implement listing data import

    - Parse data/landData/*.json files
    - Create Listing nodes with id, title, address, location, deposit, rent, area, building_type, floor
    - _Requirements: 10.7_

  - [x] 2.10 Write property test for listing import completeness


    - **Property 14: Listing import completeness**
    - **Validates: Requirements 5.2, 10.7**

  - [x] 2.11 Create main import script

    - Orchestrate all import functions in scripts/import_graph_data.py
    - Add error handling and progress reporting
    - Create spatial indexes after import completes
    - _Requirements: 10.8_

- [ ] 3. Implement LangGraph state and workflow structure
  - [x] 3.1 Define ChatbotState TypedDict


    - Add fields for question, intent, facility_name, facility_type, max_distance_m, listings, answer, error
    - Update apps/rag/common/state.py
    - _Requirements: 6.1, 6.5_

  - [x] 3.2 Create workflow graph structure


    - Define nodes: parse_intent, search_graph, generate_response
    - Set up edges and conditional routing
    - Update apps/rag/graphs/listing_rag_graph.py
    - _Requirements: 6.1, 7.1_

- [ ] 4. Implement Intent Parser node with GPT-5-nano
  - [x] 4.1 Create intent parsing prompt template


    - Write Jinja2 template for extracting structured parameters
    - Handle intent types: university_proximity, hospital_proximity, park_proximity, commercial_density, transportation_proximity
    - Save to apps/rag/prompts/parse_intent.jinja2
    - _Requirements: 6.1, 6.2_

  - [x] 4.2 Implement parse_intent node function


    - Call GPT-5-nano with prompt template
    - Parse JSON response with intent, facility_name, facility_type, max_time_minutes, max_distance_m
    - Convert time to distance using 75 m/min walking speed
    - Handle ambiguous queries with needs_clarification flag
    - Create apps/rag/nodes/parse_intent_node.py
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 4.3 Write property test for time to distance conversion


    - **Property 1: Time to distance conversion accuracy**
    - **Validates: Requirements 1.2, 6.3**

  - [x] 4.4 Write property test for intent parser JSON structure

    - **Property 16: Intent parser JSON structure**
    - **Validates: Requirements 6.5**

- [ ] 5. Implement Graph Search node with Neo4j queries
  - [x] 5.1 Create Cypher query templates


    - Write query for university proximity
    - Write query for hospital proximity
    - Write query for park proximity
    - Write query for commercial density
    - Write query for transportation proximity
    - _Requirements: 7.1, 7.2_

  - [x] 5.2 Implement search_graph node function

    - Route to appropriate query based on intent
    - Execute Cypher query with Neo4j driver
    - Parse results into listing dictionaries
    - Handle empty results and errors
    - Create apps/rag/nodes/graph_search_node.py
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ] 5.3 Write property test for distance query correctness
    - **Property 2: Distance query correctness**
    - **Validates: Requirements 1.3**

  - [ ] 5.4 Write property test for result ordering
    - **Property 3: Result ordering by distance**
    - **Validates: Requirements 1.4**

  - [ ] 5.5 Write property test for hospital proximity filtering
    - **Property 5: Hospital proximity filtering**
    - **Validates: Requirements 2.2**

  - [ ] 5.6 Write property test for hospital count accuracy
    - **Property 6: Hospital count accuracy**
    - **Validates: Requirements 2.3**

  - [ ] 5.7 Write property test for park proximity filtering
    - **Property 7: Park proximity filtering**
    - **Validates: Requirements 3.2**

  - [ ] 5.8 Write property test for commercial facility filtering
    - **Property 8: Commercial facility distance filtering**
    - **Validates: Requirements 4.1**

  - [ ] 5.9 Write property test for commercial count accuracy
    - **Property 9: Commercial facility count accuracy**
    - **Validates: Requirements 4.2**

  - [ ] 5.10 Write property test for commercial density ranking
    - **Property 10: Commercial density ranking**
    - **Validates: Requirements 4.3**

  - [ ] 5.11 Write property test for subway proximity filtering
    - **Property 11: Subway proximity filtering**
    - **Validates: Requirements 4.1.1**

  - [ ] 5.12 Write property test for bus stop proximity filtering
    - **Property 12: Bus stop proximity filtering**
    - **Validates: Requirements 4.1.2**

  - [ ] 5.13 Write property test for distance function usage
    - **Property 17: Distance function usage in queries**
    - **Validates: Requirements 7.2**

  - [ ] 5.14 Write property test for facility aggregation correctness
    - **Property 18: Facility aggregation correctness**
    - **Validates: Requirements 7.3**

  - [ ] 5.15 Write property test for query result completeness
    - **Property 19: Query result completeness**
    - **Validates: Requirements 7.4**

- [ ] 6. Implement Response Generator node with GPT-5-nano
  - [x] 6.1 Create response generation prompt template


    - Write Jinja2 template for formatting results in Korean
    - Include instructions for summarizing top 5-10 listings
    - Save to apps/rag/prompts/generate_response.jinja2
    - _Requirements: 9.1, 9.2_

  - [x] 6.2 Implement generate_response node function


    - Call GPT-5-nano with query results
    - Format response in natural Korean
    - Handle empty results with suggestions
    - Create apps/rag/nodes/generate_response_node.py
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ] 6.3 Write property test for response field completeness
    - **Property 4: Response contains required fields**
    - **Validates: Requirements 1.5**

  - [ ] 6.4 Write property test for response listing count
    - **Property 20: Response listing count constraint**
    - **Validates: Requirements 9.2**

- [ ] 7. Integrate workflow with Django backend
  - [ ] 7.1 Create chatbot API endpoint
    - Add POST /api/chatbot/query endpoint
    - Accept JSON with "question" field
    - Invoke LangGraph workflow
    - Return formatted response
    - Add to apps/backend/apps/graph/urls.py and views
    - _Requirements: 8.1, 8.2_

  - [ ] 7.2 Implement error handling
    - Handle Neo4j connection errors with retry logic
    - Return appropriate HTTP status codes
    - Format error messages in Korean
    - _Requirements: 8.3, 8.4_

  - [ ] 7.3 Write integration tests for API endpoint
    - Test successful query flow for each intent type
    - Test error handling for connection failures
    - Test empty result handling
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 8. Create optional NEAR relationships for performance
  - [ ] 8.1 Implement relationship creation script
    - Create NEAR relationships between listings and facilities within thresholds
    - Add distance_m property to relationships
    - Create scripts/create_near_relationships.py
    - _Requirements: 5.5_

  - [ ] 8.2 Write property test for NEAR relationship constraints
    - **Property 15: NEAR relationship distance constraint**
    - **Validates: Requirements 5.5**

- [x] 9. Update Docker Compose configuration


  - Add Neo4j service with APOC plugin
  - Configure environment variables for Neo4j connection
  - Update backend and rag services to depend on Neo4j
  - Update docker-compose.yml
  - _Requirements: 8.1_

- [x] 10. Create documentation and usage examples



  - Write README for chatbot usage
  - Document data import process
  - Add example queries in Korean
  - Create docs/neo4j_chatbot.md
  - _Requirements: All_

- [ ] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
