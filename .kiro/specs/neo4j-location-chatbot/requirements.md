# Requirements Document

## Introduction

This document specifies the requirements for a Neo4j-based LLM chatbot that recommends real estate listings based on proximity to various facilities (universities, hospitals, parks, convenience stores, restaurants). The system will use graph database queries to find listings within specified distances and time ranges, then use LLM to provide natural language responses.

## Glossary

- **Chatbot System**: The LangGraph-based conversational AI that processes user queries and returns listing recommendations
- **Neo4j Database**: The graph database storing nodes (listings, facilities) and relationships (proximity, location)
- **Listing**: A real estate property available for rent or sale (data source: data/landData/*.json)
- **Facility**: A point of interest such as a university, hospital, park, bus stop, subway station, or commercial establishment
- **Distance Query**: A Cypher query that calculates spatial distance between two geographic points
- **Intent Parser**: The LLM component that extracts structured parameters from natural language queries (powered by GPT-5-nano)
- **Graph Search Node**: The LangGraph node that executes Neo4j queries based on parsed intent
- **Response Generator**: The LLM component that formats query results into natural language responses (powered by GPT-5-nano)
- **GPT-5-nano**: The OpenAI language model used for intent parsing and response generation
- **University Data**: Educational institution data from data/교육부_대학교 주소기반 좌표정보_20241030.xlsx
- **Hospital Data**: Medical facility data from data/전국 병의원 및 약국 현황 2025.9/*.csv
- **Park Data**: Urban park data from data/서울시_도시공원정보/*.csv
- **Commercial Data**: Store and restaurant data from data/소상공인시장진흥공단_상가(상권)정보_20251030/*.csv
- **Bus Stop Data**: Bus station data from data/국토교통부_전국 버스정류장 위치정보_20241031_utf8.csv
- **Subway Station Data**: Metro station data from data/지하철_노선도.csv

## Requirements

### Requirement 1

**User Story:** As a user, I want to find listings near a specific university within a time range, so that I can live close to campus.

#### Acceptance Criteria

1. WHEN a user provides a university name and time duration THEN the Chatbot System SHALL extract the university name and maximum travel time from the query
2. WHEN the Intent Parser identifies a university proximity query THEN the Chatbot System SHALL convert travel time to distance using walking speed (75 meters per minute)
3. WHEN the Graph Search Node receives university proximity parameters THEN the Chatbot System SHALL execute a Neo4j distance query to find all listings within the calculated distance
4. WHEN multiple listings match the criteria THEN the Chatbot System SHALL return results ordered by distance in ascending order
5. WHEN the Response Generator receives query results THEN the Chatbot System SHALL format the top listings with title, address, deposit, rent, and distance information

### Requirement 2

**User Story:** As a user, I want to find listings near hospitals, so that I can access medical facilities easily.

#### Acceptance Criteria

1. WHEN a user requests listings near hospitals THEN the Chatbot System SHALL identify hospital facilities in the Neo4j Database
2. WHEN hospital facilities are identified THEN the Chatbot System SHALL find all listings within a default proximity range (500 meters) of any hospital
3. WHEN multiple hospitals exist near a listing THEN the Chatbot System SHALL include the count and names of nearby hospitals in the response
4. WHEN the Response Generator formats hospital proximity results THEN the Chatbot System SHALL include hospital names and distances for each recommended listing

### Requirement 3

**User Story:** As a user, I want to find listings near parks suitable for walking, so that I can enjoy outdoor activities.

#### Acceptance Criteria

1. WHEN a user requests listings near parks THEN the Chatbot System SHALL identify park facilities in the Neo4j Database
2. WHEN park facilities are identified THEN the Chatbot System SHALL find all listings within walking distance (800 meters) of parks
3. WHEN multiple parks exist near a listing THEN the Chatbot System SHALL include park names and sizes in the response
4. WHEN the Response Generator formats park proximity results THEN the Chatbot System SHALL describe the walking environment and park accessibility

### Requirement 4

**User Story:** As a user, I want to find listings in areas with many convenience stores and restaurants, so that I can access daily necessities and dining options easily.

#### Acceptance Criteria

1. WHEN a user requests listings near convenience stores or restaurants THEN the Chatbot System SHALL identify commercial facilities from the CommercialFacility nodes within a search radius (300 meters)
2. WHEN commercial facilities are counted THEN the Chatbot System SHALL aggregate the total number of convenience stores and restaurants near each listing using business type codes
3. WHEN listings are ranked THEN the Chatbot System SHALL prioritize listings with higher counts of nearby commercial facilities
4. WHEN the Response Generator formats commercial density results THEN the Chatbot System SHALL include facility counts and describe the convenience level

### Requirement 4.1

**User Story:** As a user, I want to find listings near public transportation, so that I can commute easily.

#### Acceptance Criteria

1. WHEN a user requests listings near subway stations THEN the Chatbot System SHALL find listings within walking distance (700-800 meters) of SubwayStation nodes
2. WHEN a user requests listings near bus stops THEN the Chatbot System SHALL find listings within walking distance (300 meters) of BusStop nodes
3. WHEN multiple transportation options exist THEN the Chatbot System SHALL include both subway and bus accessibility information
4. WHEN the Response Generator formats transportation results THEN the Chatbot System SHALL include station/stop names, lines, and walking distances

### Requirement 5

**User Story:** As a developer, I want the Neo4j database to store facility and listing data with geographic coordinates, so that distance calculations are accurate and performant.

#### Acceptance Criteria

1. WHEN facility data is imported THEN the Neo4j Database SHALL store each facility as a node with name, type, address, and point location properties
2. WHEN listing data is imported THEN the Neo4j Database SHALL store each listing as a node with id, title, address, point location, deposit, rent, area, building type, and floor properties
3. WHEN location-based queries are executed THEN the Neo4j Database SHALL use spatial indexes on location properties for performance optimization
4. WHEN distance calculations are performed THEN the Neo4j Database SHALL use the built-in distance function with point geometries
5. WHEN relationships are created THEN the Neo4j Database SHALL establish NEAR relationships between listings and facilities within defined thresholds

### Requirement 6

**User Story:** As a developer, I want the Intent Parser to extract structured parameters from natural language using GPT-5-nano, so that the system can execute appropriate graph queries.

#### Acceptance Criteria

1. WHEN a user query is received THEN the Intent Parser SHALL use GPT-5-nano to identify the query intent type (university_proximity, hospital_proximity, park_proximity, commercial_density, transportation_proximity)
2. WHEN location entities are mentioned THEN the Intent Parser SHALL use GPT-5-nano to extract facility names, types, and distance/time constraints
3. WHEN time durations are mentioned THEN the Intent Parser SHALL normalize them to minutes and convert to meters using appropriate speed assumptions (walking: 75m/min, transit: varies)
4. WHEN ambiguous queries are received THEN the Intent Parser SHALL use GPT-5-nano to request clarification from the user
5. WHEN parameters are extracted THEN the Intent Parser SHALL output a structured JSON object with intent, target facility, max distance, and facility type

### Requirement 7

**User Story:** As a developer, I want the Graph Search Node to execute optimized Cypher queries, so that results are returned quickly.

#### Acceptance Criteria

1. WHEN the Graph Search Node receives parsed intent THEN the Chatbot System SHALL construct a Cypher query matching the intent type
2. WHEN distance-based queries are executed THEN the Graph Search Node SHALL use the distance function with location points and distance thresholds
3. WHEN facility aggregation is needed THEN the Graph Search Node SHALL count nearby facilities grouped by listing
4. WHEN query results are returned THEN the Graph Search Node SHALL include listing details, distances, and facility information
5. WHEN no results are found THEN the Graph Search Node SHALL return an empty result set with appropriate metadata

### Requirement 8

**User Story:** As a developer, I want the system to integrate with the existing Django backend, so that the chatbot can be accessed via REST API.

#### Acceptance Criteria

1. WHEN the Django backend receives a chatbot query request THEN the system SHALL invoke the LangGraph workflow with the user question
2. WHEN the LangGraph workflow completes THEN the Django backend SHALL return the formatted response as JSON
3. WHEN errors occur during graph queries THEN the Django backend SHALL return appropriate error messages with HTTP status codes
4. WHEN the Neo4j connection is unavailable THEN the Django backend SHALL handle connection errors gracefully and notify the user

### Requirement 9

**User Story:** As a user, I want the chatbot to provide natural, conversational responses using GPT-5-nano, so that the interaction feels intuitive.

#### Acceptance Criteria

1. WHEN the Response Generator receives query results THEN the Chatbot System SHALL use GPT-5-nano to format responses in natural Korean language
2. WHEN multiple listings are returned THEN the Response Generator SHALL use GPT-5-nano to summarize the top 5-10 results with key details
3. WHEN distance information is included THEN the Response Generator SHALL use GPT-5-nano to express distances in user-friendly terms (walking minutes, meters)
4. WHEN no listings match the criteria THEN the Response Generator SHALL use GPT-5-nano to suggest alternative search parameters or nearby areas
5. WHEN facility information is included THEN the Response Generator SHALL use GPT-5-nano to describe the convenience and lifestyle benefits

### Requirement 10

**User Story:** As a developer, I want to import facility data from the data folder into Neo4j, so that the graph database contains comprehensive location information.

#### Acceptance Criteria

1. WHEN university data from data/교육부_대학교 주소기반 좌표정보_20241030.xlsx is imported THEN the system SHALL create University nodes with name, campus, address, latitude, and longitude properties
2. WHEN hospital and pharmacy data from data/전국 병의원 및 약국 현황 2025.9/*.csv is imported THEN the system SHALL create Hospital nodes with name, type, address, and location point properties
3. WHEN park data from data/서울시_도시공원정보/*.csv is imported THEN the system SHALL create Park nodes with name, area, address, and location point properties
4. WHEN commercial facility data from data/소상공인시장진흥공단_상가(상권)정보_20251030/*.csv is imported THEN the system SHALL create CommercialFacility nodes with name, business type code, address, and location point properties
5. WHEN bus stop data from data/국토교통부_전국 버스정류장 위치정보_20241031_utf8.csv is imported THEN the system SHALL create BusStop nodes with name, address, and location point properties
6. WHEN subway station data from data/지하철_노선도.csv is imported THEN the system SHALL create SubwayStation nodes with name, line, address, and location point properties
7. WHEN listing data from data/landData/*.json is imported THEN the system SHALL create Listing nodes with id, title, address, location point, deposit, rent, area, building type, and floor properties
8. WHEN all data import completes THEN the system SHALL create spatial indexes on all location properties for query performance
