#!/usr/bin/env python
"""Debug script to test API serializer"""
import os
import sys
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.listings.models import Land, PriceClassificationResult
from apps.listings.serializers import LandSerializer

print("Testing Serializer...")

# Get queryset
lands = Land.objects.with_images().select_related('landbroker')[:5]
print(f"Got {len(lands)} lands")

# Get context
price_predictions = {p.land_num: p for p in PriceClassificationResult.objects.all()}
context = {'request': None, 'price_predictions': price_predictions}
print(f"Got {len(price_predictions)} price predictions")

# Test serializer
try:
    serializer = LandSerializer(lands, many=True, context=context)
    data = serializer.data
    print(f'SUCCESS: {len(data)} items serialized')
    print(f'First item id: {data[0].get("id") if data else "N/A"}')
except Exception as e:
    print(f'ERROR: {e}')
    traceback.print_exc()
