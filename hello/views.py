from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse

from .models import Greeting, Vehicles
from django.views.decorators.http import require_http_methods
from django.core import serializers
from .blindspotcalc import *
import json
# from rest_framework.test import APIClient
# from rest_framework import status
# from django.core.urlresolvers import reverse


# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, 'index.html')

def getinfo(request):
    # return HttpResponse('Hello from Python!')
    return render(request, 'getinfo.html')

def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, 'db.html', {'greetings': greetings})

@require_http_methods(["POST"])
def addvehicle(request, fullvin, partialvin, vmake, vmodel, vgvwr, perc_vis):
	v = Vehicles(fullvin=fullvin, partialvin=partialvin, vmake=vmake, vmodel=vmodel, vgvwr=vgvwr, perc_vis=perc_vis)
	v.save()
	return HttpResponse("thanks")

@require_http_methods(["GET"])
def getbyvgvwr(request, vgvwr):
	vgvwr = "Class " + vgvwr 
	q = serializers.serialize("json", Vehicles.objects.filter(vgvwr=vgvwr))
	return JsonResponse({"data": q})

@require_http_methods(["GET"])
def getbyperc(request, perc):
	q = serializers.serialize("json", Vehicles.objects.filter(perc_vis__gte=perc))
	return JsonResponse({"data": q})

@require_http_methods(["GET"])
def getbyfullvin(request, fullvin):
    q = serializers.serialize("json", Vehicles.objects.filter(fullvin=fullvin))
    return JsonResponse({"data": q})

@require_http_methods(["GET"])
def getbypartialvin(request, partialvin):
    partialvin = partialvin[:10]
    q = serializers.serialize("json", Vehicles.objects.filter(partialvin=partialvin))
    return JsonResponse({"data": q})

@require_http_methods(["GET"])
def getbyvmake(request, vmake):
    q = serializers.serialize("json", Vehicles.objects.filter(vmake=vmake))
    return JsonResponse({"data": q})

@require_http_methods(["GET"])
def getmakes(request):
    q = list(Vehicles.objects.order_by().values_list('vmake', flat=True).distinct())
    return JsonResponse({"data": q})

@require_http_methods(["POST"])
def getinterestarea(request):
    json_data = json.loads(request.body.decode("utf-8"))
    angles = json_data['phis']
    c = json_data['c']
    d = json_data['d']
    interest_area = find_total_truck_interest_area(angles, c, d)
    return JsonResponse({"data": interest_area})

@require_http_methods(["POST"])
def getblindarea(request):
    json_data = json.loads(request.body.decode("utf-8"))
    NVPs = json_data['NVPs']
    angles = json_data['phis']
    DH = json_data['DH']
    c = json_data['c']
    d = json_data['d']
    blind_area = find_total_truck_blind_area(NVPs, angles, DH, c, d)
    return JSONResponse({"data" : blind_area})