#!/usr/bin/env python
"""Quick test for ES search"""
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])

# Test Korean text search
r = es.search(index='realestate_listings', query={'match': {'search_text': '강남'}}, size=2)
print(f"Korean text search '강남': {r['hits']['total']['value']} hits")

# Test style_tags search
r = es.search(index='realestate_listings', query={'terms': {'style_tags': ['풀옵션']}}, size=2)
print(f"Style tag '풀옵션': {r['hits']['total']['value']} hits")

# Test price range
r = es.search(index='realestate_listings', query={'range': {'deposit': {'gte': 1000, 'lte': 3000}}}, size=2)
print(f"Deposit 1000-3000: {r['hits']['total']['value']} hits")

# Test geo search (Seoul area)
r = es.search(index='realestate_listings', query={
    'geo_distance': {
        'distance': '5km',
        'location': {'lat': 37.5665, 'lon': 126.9780}
    }
}, size=2)
print(f"Geo search (Seoul center 5km): {r['hits']['total']['value']} hits")

print("\nES indexing verification complete!")
