from django.db import models

# Create your models here.
class Greeting(models.Model):
    when = models.DateTimeField('date created', auto_now_add=True)

class Vehicles(models.Model):
	fullvin = models.IntegerField()
	partialvin = models.IntegerField()
	vmake = models.CharField(max_length=100)
	vmodel = models.CharField(max_length=100)
	vseries = models.CharField(max_length=100)
	vgvwr = models.CharField(max_length=100)
	when = models.DateTimeField('date created', auto_now_add=True)