# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Land(models.Model):
    land_id = models.AutoField(primary_key=True)
    landbroker_id = models.IntegerField(blank=True, null=True)
    land_num = models.CharField(unique=True, max_length=20)
    building_type = models.CharField(max_length=20)
    address = models.CharField(max_length=200, blank=True, null=True)
    like_count = models.IntegerField(blank=True, null=True)
    view_count = models.IntegerField(blank=True, null=True)
    deal_type = models.CharField(max_length=50, blank=True, null=True)
    user_profiles_id = models.IntegerField(blank=True, null=True)
    url = models.TextField(blank=True, null=True)
    images = models.JSONField(blank=True, null=True)
    trade_info = models.JSONField(blank=True, null=True)
    listing_info = models.JSONField(blank=True, null=True)
    additional_options = models.TextField(blank=True, null=True)  # This field type is a guess.
    description = models.TextField(blank=True, null=True)
    agent_info = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'land'
