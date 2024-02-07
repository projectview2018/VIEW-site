from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import ScanForm


def index(request):
    return render(request, 'lidar/index.html', {})


def add_vehicle(request):
    return render(request, 'lidar/add-vehicle.html', {})


def data_upload(request):
    if request.method == 'POST':
        form = ScanForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/add_vehicle')
    else:
        form = ScanForm()
    return render(request, 'lidar/data-upload.html', {'form': form})


def faq(request):
    return render(request, 'lidar/faq.html', {})


def vehicle_database_loading(request):
    return render(request, 'lidar/vehicle-database-loading.html', {})


def vehicle_database_table(request):
    return render(request, 'lidar/vehicle-database-table.html', {})
