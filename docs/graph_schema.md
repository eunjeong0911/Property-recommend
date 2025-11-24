# Neo4j 그래프 스키마

## Nodes

### Listing
- id
- title
- price
- area

### Facility
- id
- name
- type (subway, school, hospital, etc.)

### District
- id
- name

## Relationships

- (Listing)-[:LOCATED_IN]->(District)
- (Listing)-[:NEAR]->(Facility)
- (Facility)-[:IN_DISTRICT]->(District)
