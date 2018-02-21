from django.db import models

# Create your models here.
class Greeting(models.Model):
    when = models.DateTimeField('date created', auto_now_add=True)

class Vehicles(models.Model):
	full_vin = models.IntegerField()
	partial_vin = models.IntegerField()
	v_make = models.CharField(max_length=100)
	v_model = models.CharField(max_length=100)
	v_series = models.CharField(max_length=100)
	v_gvwr = models.CharField(max_length=100)
	when = models.DateTimeField('date created', auto_now_add=True)