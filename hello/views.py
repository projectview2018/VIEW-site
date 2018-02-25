from django.shortcuts import render
from django.http import HttpResponse

from .models import Greeting, Vehicles
from django.views.decorators.http import require_http_methods
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

@require_http_methods(["POST"])
def addvehicle(request, fullvin, partialvin, vmake, vmodel, vgvwr):
	v = Vehicles(fullvin, partialvin, vmake, vmodel, vgvwr)
	v.save()


