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
    print("running addvehicle function")
    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR')
    json_data = json.loads(request.body.decode("utf-8"))
    fullvin = json_data['vin']
    partialvin = json_data['partialvin']
    vmake = json_data['vmake']
    vmodel = json_data['vmodel']
    vgvwr = json_data['vwc']
    vyear = json_data['vyear']
    perc_vis = json_data['perc']
    b = json_data['b']
    d = json_data['d']
    radial_distance = json_data['radial_distance']
    driver_height = json_data['driver_height']
    comments = json_data['comments']
    image_name = json_data['image_name']
    a = json_data['a']
    c = json_data['c']
    image_URL = json_data['image_URL']
    try :
        drawing_URL = json_data['drawing_URL']
    except:
        drawing_URL  = "https://res.cloudinary.com/dkrq49vzq/image/upload/v1591716313/sample.jpg"
    perc_front = json_data['perc_front']
    perc_passenger = json_data['perc_passenger']
    preschool_children = json_data['preschool_children']
    grade_school_children = json_data['grade_school_children']
    grade_school_bicyclists = json_data['grade_school_bicyclists']
    wheelchair_users = json_data['wheelchair_users']
    adult_bicyclists = json_data['adult_bicyclists']
    adults = json_data['adults']
    total_volume_front = json_data['total_volume_front']
    total_volume_passenger = json_data['total_volume_passenger']
    total_volume_between = json_data['total_volume_between']

    print(image_name)

    image = {"url": image_URL}
    drawing = {"url": drawing_URL}

    try:
     # upload image and get url
        # url = uploadimage(image_contents)
        # url = uploadimage(image_name) # no longer needed
        # image = {"url": fileURL}

    #     # add record to database
        record = {"Full VIN": fullvin, "Partial VIN": partialvin, "Make": vmake, "Model": vmodel, "Weight Class": vgvwr,
               "Year": vyear, "Percent Visible Volume": perc_vis[0], 'a':a, "b": b,'c':c, "d": d, "Radial Distance": radial_distance,
               "Driver Height": driver_height, "Comments":comments,
               'Percent Visible Volume in Front': perc_front[0],
               'Percent Visible Volume in Passenger Side': perc_passenger[0],
               'Preschool Children in Blindzone':preschool_children,
               'Grade School Children in Blindzone':grade_school_children, 'Grade School Child Bicyclists in Blindzone':grade_school_bicyclists,
               'Wheelchair Users in Blindzone':wheelchair_users, 'Bicyclists in Blindzone':adult_bicyclists,
               'Adults in Blindzone':adults,
               'Total Front Volume':total_volume_front,'Total Passenger Volume':total_volume_passenger,
               'Total A Pillar Volume':total_volume_between,
               "Percent Visible Volume (Metric Standard)": perc_vis[1],
               'Percent Visible Volume in Front (Metric Standard)': perc_front[1],
               'Percent Visible Volume in Passenger Side (Metric Standard)': perc_passenger[1],
               'a (cm)': int(a * 2.54), 'b (cm)': int(b * 2.54), 'c (cm)': int(c * 2.54), 'd (cm)': int(d * 2.54),
               'Image':[image], 'Image URL':image_URL, 'Drawing':[drawing]}
        # print(record)
        at.insert(record)
    except:
        print("failed to upload image; adding truck to db without image")
        # add record to database

        record = {"Full VIN": fullvin, "Partial VIN": partialvin, "Make": vmake, "Model": vmodel, "Weight Class": vgvwr,
                      "Year": vyear, "Percent Visible Volume": perc_vis[0], 'a':a, "b": b,'c':c, "d": d, "Radial Distance": radial_distance,
                      "Camera height above ground": driver_height, "Comments":comments,
                    'Percent Visible Volume in Front': perc_front[0],
                    'Percent Visible Volume in Passenger Side': perc_passenger[0],
                    'Preschool Children in Blindzone':preschool_children,
                    'Grade School Children in Blindzone':grade_school_children, 'Grade School Child Bicyclists in Blindzone':grade_school_bicyclists,
                    'Wheelchair Users in Blindzone':wheelchair_users, 'Bicyclists in Blindzone':adult_bicyclists,
                    'Adults in Blindzone':adults,
                    'Total Front Volume':total_volume_front,'Total Passenger Volume':total_volume_passenger,
                    'Total A Pillar Volume':total_volume_between,
                    "Percent Visible Volume (Metric Standard)": perc_vis[1],
                    'Percent Visible Volume in Front (Metric Standard)': perc_front[1],
                    'Percent Visible Volume in Passenger Side (Metric Standard)': perc_passenger[1],
                   'a (cm)': int(a * 2.54), 'b (cm)': int(b * 2.54), 'c (cm)': int(c * 2.54), 'd (cm)': int(d * 2.54),
                    'Image':[image], 'Image URL':image_URL, 'Drawing':[drawing]}

        # print(record)
        at.insert(record)
    return "Thank you. This record has been added."

# this method should upload an image to Cloudinary and return the URL of where it is stored

def uploadimage(image):
    # configure cloudinary
    print("starting uploadimage function")
    cloudinary.config(
         cloud_name="dkrq49vzq",
         api_key="733231156826462",
         api_secret="tf4ebuGXPE1AS5ZlGqG6WkQWTXU"
    )

    print('successfully connected to cloudinary')
    #     upload image to cloudinary

    response = cloudinary.uploader.upload(image, folder="blindspot-app")
    # print(response)
#    response = cloudinary.uploader.upload("..\Peterbilt_stand_iphone_michael_2.JPG", folder="blindspot-app")
    image_url = response['url']

    #     returns temporary url for testing purposes
    return image_url
#     returns test image of flower
#    return "https://res.cloudinary.com/dkrq49vzq/image/upload/v1591716313/sample.jpg"


@require_http_methods(["POST"])
def getinterestarea(request):
    print("starting getinterestarea")
    json_data = json.loads(request.body.decode("utf-8"))
    angles = json_data['phis']
    b = json_data['b']
    d = json_data['d']
    a = json_data['DH']
    c = json_data['c']
    print("c: ", c)
    print("b: ", b)
    print("a: ", a)
    print("d: ", d)
    print("starting find_total_truck_interest_area")
    interest_area = find_total_truck_interest_area(angles, b, d)
    interest_area_1 = find_total_truck_interest_area(angles, b, d, 1)
    print("starting stick figure")
    preschool_children, grade_school_children, grade_school_bicyclists, wheelchair_users,adult_bicyclists, adults = do_stick_figure_analyses(a,c,d)
    print("finished stick figure")
    return JsonResponse({"data": interest_area, "data_1": interest_area_1,
                        "preschool_children": preschool_children,
                        "grade_school_children": grade_school_children,
                        "grade_school_bicyclists": grade_school_bicyclists,
                        "wheelchair_users": wheelchair_users,
                        "adult_bicyclists": adult_bicyclists, "adults": adults})


@require_http_methods(["POST"])
def getblindarea(request):
    json_data = json.loads(request.body.decode("utf-8"))
    NVPs = json_data['NVPs']
    angles = json_data['phis']
    DH = json_data['DH']
    b = json_data['b']
    d = json_data['d']
    blind_area = find_total_truck_blind_area(NVPs, angles, DH, b, d)
    interest_area = find_total_truck_interest_area(angles, b, d)
    blind_area_1 = find_total_truck_blind_area(NVPs, angles, DH, b, d, 1)
    interest_area_1 = find_total_truck_interest_area(angles, b, d, 1)
    return JsonResponse({"data": blind_area, "total_volume":interest_area, "data_1": blind_area_1, "total_volume_1": interest_area_1})
