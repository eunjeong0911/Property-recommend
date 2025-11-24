# ERD (Entity Relationship Diagram)

## Tables

### listings
- id (PK)
- title
- address
- price
- area
- room_count
- created_at
- updated_at

### listing_embeddings
- id (PK)
- listing_id (FK)
- chunk_text
- embedding (vector)
- created_at

### users
- id (PK)
- username
- email
- created_at

### user_logs
- id (PK)
- user_id (FK)
- listing_id (FK)
- action_type
- created_at
