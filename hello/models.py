from django.db import models

# Create your models here.
class Greeting(models.Model):
    when = models.DateTimeField('date created', auto_now_add=True)

class Vehicles(models.Model):
	fullvin = models.CharField(max_length=100)
	partialvin = models.CharField(max_length=100)
	vmake = models.CharField(max_length=100)
	vmodel = models.CharField(max_length=100)
	vgvwr = models.CharField(max_length=100)
	perc_vis = models.IntegerField()
	when = models.DateTimeField('date created', auto_now_add=True)

#https://stackoverflow.com/questions/28598676/django-heroku-error-your-models-have-changes-that-are-not-yet-reflected-in-a-mi