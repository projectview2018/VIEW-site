from django.shortcuts import render
from django.http import JsonResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.template import loader

from .models import Vehicles
from django.views.decorators.http import require_http_methods
from django.core import serializers
from .blindspotcalc import *
import json
from blindspotapp.Airtable import Airtable

# plotly imports
from plotly.offline import plot
import plotly.graph_objs as go

# cloudinary imports
import cloudinary
import cloudinary.uploader

# Create your views here.

def home(request):
    return render(request, "home.html")

def index(request):
    return render(request, "index.html")

# Generates a histogram of truck data, including user's own data if applicable
# if included, user_data should be an int, the perc_vis of the user's truck

def makehistogram(user_data=None):
    # load the data from Airtable
    print("user_data: " + str(user_data))
    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR')
    vehicles = at.get_all()
    perc_vis = [vehicle['fields']['Percent Visible Volume']
                for vehicle in vehicles]

    # make the figure
    fig = go.Figure()
    histogram = go.Histogram(x=perc_vis,
                             name='perc_vis_hist',
                             opacity=0.8, marker_color="#2196F3")
    fig.add_trace(histogram)
    # if applicable, add user's truck as a dotted line on top of histogram
    if user_data is not None:
        fig.add_shape(
            go.layout.Shape(type='line', xref='x', yref='paper',
                            x0=user_data, y0=0, x1=user_data, y1=0.95, line={'dash': 'dash', 'color': 'black'}),
        )

        fig.add_annotation(
                x=user_data+1,
                y=27,
                xref="x",
                yref="y",
                text='<b>Your Vehicle</b>',
                showarrow=True,
                align="center",
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                ax=40,
                ay=-50,
                )

    # update layout with title and labels
    fig.update_layout(
        title="Histogram of Vehicle Percent Visible Volumes",
        yaxis_title="Number of Entries",
        xaxis_title="Percent Visible",
        showlegend=False,
        font=dict(
            family="Helvetica",
            size=18,
            color="#000000"
        )
    )
    config = {'staticPlot': True}
    plt_div = plot(fig, output_type='div', include_plotlyjs=False, config=config)
    # return HttpResponse(plt_div)
    return plt_div


def getinfo(request, user_data=None):
    plot_div = makehistogram(user_data)
    if user_data is not None:
        user_results = "Your vehicle's percent visible volume is {}%.".format(
            user_data)
        return render(request, "getinfo.html", context={'plot_div': plot_div, 'user_results': user_results})
    else:
        return render(request, "getinfo.html", context={'plot_div': plot_div})

@require_http_methods(["POST"])
def addvehicle(request):
    # set up Airtable base and unpack data
    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR')
    json_data = json.loads(request.body.decode("utf-8"))
    fullvin = json_data['vin']
    partialvin = json_data['partialvin']
    vmake = json_data['vmake']
    vmodel = json_data['vmodel']
    vgvwr = json_data['vwc']
    vyear = json_data['vyear']
    perc_vis = json_data['perc']
    c = json_data['c']
    d = json_data['d']
    radial_distance = json_data['radial_distance']
    driver_height = json_data['driver_height']
    comments = json_data['comments']
    # image_name = json_data['image_name']
    # print(image_name)

    # try:
    #     # upload image and get url
    #     url = uploadimage(image_name)
    #     image = {"url": url}

    #     # add record to database
    #     record = {"Full VIN": fullvin, "Partial VIN": partialvin, "Make": vmake, "Model": vmodel, "Weight Class": vgvwr,
    #               "Year": vyear, "Percent Visible Volume": perc_vis, "c": c, "d": d, "Radial Distance": radial_distance,
    #               "Driver Height": driver_height, "Image": [image]}
    # except:
    #     print("failed to upload image; adding truck to db without image")
        # add record to database
    record = {"Full VIN": fullvin, "Partial VIN": partialvin, "Make": vmake, "Model": vmodel, "Weight Class": vgvwr,
                  "Year": vyear, "Percent Visible Volume": perc_vis, "c": c, "d": d, "Radial Distance": radial_distance,
                  "Camera height above ground": driver_height, "Comments":comments}
    print(record)
    at.insert(record)
    return "Thank you. This record has been added."

# this method should upload an image to Cloudinary and return the URL of where it is stored


# def uploadimage(image):
#     # configure cloudinary
#     cloudinary.config(
#         cloud_name="dkrq49vzq",
#         api_key="733231156826462",
#         api_secret="tf4ebuGXPE1AS5ZlGqG6WkQWTXU"
#     )

#     upload image to cloudinary

#     response = cloudinary.uploader.upload(image, folder="blindspot-app")
#     response = cloudinary.uploader.upload("..\Peterbilt_stand_iphone_michael_2.JPG", folder="blindspot-app")

#     image_url = response['url']

#     returns temporary url for testing purposes
#     return image_url
#     returns test image of flower
#     return "https://res.cloudinary.com/dkrq49vzq/image/upload/v1591716313/sample.jpg"


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
    return JsonResponse({"data": blind_area})
