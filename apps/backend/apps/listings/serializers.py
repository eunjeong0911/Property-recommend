from rest_framework import serializers
from .models import Land

class LandSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='land_id')
    title = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    temperature = serializers.FloatField(default=0.0)
    deposit = serializers.SerializerMethodField()
    monthly_rent = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    region = serializers.CharField(source='address')
    transaction_type = serializers.CharField(source='deal_type')
    
    # Detail fields
    land_num = serializers.CharField()
    address = serializers.CharField()
    building_type = serializers.CharField()
    floor = serializers.SerializerMethodField()
    room_count = serializers.SerializerMethodField()
    area_supply = serializers.SerializerMethodField()
    area_exclusive = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()
    parking = serializers.SerializerMethodField()
    move_in_date = serializers.SerializerMethodField()
    maintenance_fee = serializers.SerializerMethodField()
    heating_method = serializers.SerializerMethodField()
    elevator = serializers.SerializerMethodField()
    description = serializers.CharField()
    agent_info = serializers.JSONField()

    class Meta:
        model = Land
        fields = [
            'id', 
            'title', 
            'image', 
            'images',
            'temperature', 
            'deposit', 
            'monthly_rent', 
            'price',
            'region',
            'transaction_type',
            'building_type',
            'land_num',
            'address',
            'floor',
            'room_count',
            'area_supply',
            'area_exclusive',
            'direction',
            'parking',
            'move_in_date',
            'maintenance_fee',
            'heating_method',
            'elevator',
            'description',
            'agent_info'
        ]

    def get_title(self, obj):
        if obj.listing_info and isinstance(obj.listing_info, dict):
            return obj.listing_info.get('title', obj.land_num)
        return obj.land_num

    def get_image(self, obj):
        if obj.images and isinstance(obj.images, list) and len(obj.images) > 0:
            return obj.images[0]
        return None

    def get_images(self, obj):
        if obj.images and isinstance(obj.images, list):
            return obj.images
        return []

    def get_deposit(self, obj):
        if obj.trade_info and isinstance(obj.trade_info, dict):
            return obj.trade_info.get('deposit', 0)
        return 0

    def get_monthly_rent(self, obj):
        if obj.trade_info and isinstance(obj.trade_info, dict):
            return obj.trade_info.get('monthly_rent', 0)
        return 0

    def get_price(self, obj):
        deposit = self.get_deposit(obj)
        monthly_rent = self.get_monthly_rent(obj)
        if deposit is None: deposit = 0
        if monthly_rent is None: monthly_rent = 0
        return f"월세 {deposit:,} / {monthly_rent:,}"

    def _get_listing_info_field(self, obj, field_name):
        if obj.listing_info and isinstance(obj.listing_info, dict):
            return obj.listing_info.get(field_name, '-')
        return '-'

    def get_floor(self, obj): return self._get_listing_info_field(obj, 'floor')
    def get_room_count(self, obj): return self._get_listing_info_field(obj, 'room_count')
    def get_area_supply(self, obj): return self._get_listing_info_field(obj, 'area_supply')
    def get_area_exclusive(self, obj): return self._get_listing_info_field(obj, 'area_exclusive')
    def get_direction(self, obj): return self._get_listing_info_field(obj, 'direction')
    def get_parking(self, obj): return self._get_listing_info_field(obj, 'parking')
    def get_move_in_date(self, obj): return self._get_listing_info_field(obj, 'move_in_date')
    def get_maintenance_fee(self, obj): return self._get_listing_info_field(obj, 'maintenance_fee')
    def get_heating_method(self, obj): return self._get_listing_info_field(obj, 'heating_method')
    def get_elevator(self, obj): return self._get_listing_info_field(obj, 'elevator')
