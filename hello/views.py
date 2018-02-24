from django.shortcuts import render
from django.http import HttpResponse

from .models import Greeting, Vehicles
# from rest_framework.test import APIClient
# from rest_framework import status
# from django.core.urlresolvers import reverse


# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, 'index.html')


def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, 'db.html', {'greetings': greetings})

def addvehicle(request, fullvin, partialvin, vmake, vmodel, vseries, vgvwr):
	v = Vehicles(fullvin, partialvin, vmake, vmodel, vseries, vgvwr)
	v.save()


