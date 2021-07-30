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
from .GenerateVehicleImages import *
import json
from blindspotapp.Airtable import Airtable
from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont

# plotly imports
from plotly.offline import plot
import plotly.graph_objs as go

# cloudinary imports
import cloudinary
import cloudinary.uploader
import cloudinary.api
# Create your views here.

def home(request):
    return render(request, "home.html")

def index(request):
    return render(request, "index.html")

def visualize(request):
    return render(request, "visualize.html")

# Generates a histogram of truck data, including user's own data if applicable
# if included, user_data should be an int, the perc_vis of the user's truck

"""
front_URL = json_data['front_URL']
    side_URL = json_data['side_URL']
    top_URL = json_data['top_URL']

,
                'Front Image':[front], 'Side Image':[side], 'Overhead Image':[top]
"""
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
        perc_data = at.match('ID', user_data)
        if perc_data != {}:
            perc_data = perc_data['fields']['Percent Visible Volume']
            print("record " + str(perc_data))
            user_data = perc_data
            fig.add_shape(
                go.layout.Shape(type='line', xref='x', yref='paper',
                                x0=perc_data, y0=0, x1=perc_data, y1=0.95, line={'dash': 'dash', 'color': 'black'}),
            )
            #help
            fig.add_annotation(
                    x=perc_data+1,
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
        else:
            user_data = None

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
    #print(plt_div)
    return (plt_div, user_data)


def get_images_from_airtable(id_num):
    print("user_data: " + str(id_num))
    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR')
    vehicle = at.match('ID', id_num)
    panor_img = ""
    front_img = ""
    side_img = ""
    top_img = ""
    """ there are 2 states this field can be in: base64 image string, an https string  """

    if 'Image URL' in vehicle['fields']:

        panor_img = vehicle['fields']['Image URL']


    #if there is nothing in there, it is a previous entry that can be ignored
    if 'Front Image String' in vehicle['fields']:
        front_img = vehicle['fields']['Front Image String']
    if 'Side Image String' in vehicle['fields']:
        side_img = vehicle['fields']['Side Image String']

    if 'Overhead Image String' in vehicle['fields']:
        top_img = vehicle['fields']['Overhead Image String']
        #print (top_img)


    return( panor_img, front_img, side_img, top_img )
def getinfo(request, user_data=None):
    plot_div, percen = makehistogram(user_data)

    """
    img = Image.new('RGB', (10, 10), (255, 0, 0) )
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    """
    #iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAEklEQVR4nGP8z4APMOGVHbHSAEEsAROxCnMTAAAAAElFTkSuQmCC
    if user_data is not None and percen is not None:
        user_results = "Your vehicle's percent visible volume is {}%.".format(percen)

        panor_img, front_img, side_img, top_img = get_images_from_airtable(user_data)
        return render(request, "getinfo.html", context={'plot_div': plot_div, 'user_results': user_results, 'id_num':user_data, 'panor_img': panor_img, 'front_img':front_img, 'side_img': side_img, 'top_img':top_img, 'percen': percen })

    else:

        return render(request, "getinfo.html", context={'plot_div': plot_div,'panor_img':"", 'front_img':"", 'side_img': "", 'top_img':""})

@require_http_methods(["POST"])
def addvehicle(request):
    # set up Airtable base and unpack data sent from index.html
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
    agency = json_data['agency']
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
    phis_and_nvps = json_data['phis_and_nvps']
    overhead_string = json_data['top_string']

    print(image_name)
    image = {"url": image_URL}
    drawing = {"url": drawing_URL}

    # add record to database
    record = {"Full VIN": fullvin, "Partial VIN": partialvin, "Make": vmake, "Model": vmodel, "Weight Class": vgvwr,
                "Year": vyear, "Percent Visible Volume": perc_vis[0], 'a':a, "b": b,'c':c, "d": d, "Radial Distance": radial_distance,
                "Camera height above ground": driver_height, "Comments": comments, "Agency": agency,
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
                'Image':[image], 'Image URL':image_URL, 'Drawing':[drawing], 'Phis and NVPS json':phis_and_nvps, 'Overhead Image String':overhead_string}
    # print(record)
    inserted_record = at.insert(record)

    id_num = inserted_record['fields']['ID']
    if perc_vis[0] < 60 :
        strs = getvehicleimages(id_num, 5)
    else:
        strs = getvehicleimages(id_num, 1)


    #print( inserted_record['id'] )
    at.update(  inserted_record['id'], {'Front Image String':strs[0]} )
    at.update(  inserted_record['id'], {'Side Image String' :strs[1]} )
    #at.update( [{'id': inserted_record, 'fields':{ strs_dict }} ])


    return JsonResponse({"message":"Thank you, your vehicle has been added to the database.", "redirect":id_num})

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

#
@require_http_methods(["POST"])
def getddata(request):
    json_data = json.loads(request.body.decode("utf-8"))
    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR')
    vehicles = at.get_all()

    #return JsonResponse({"data": vehicles})

    # each element in scores is a dictionary of [percent visible, front visibility, side visibility, make, model, year, weight class]
    scores = []
    # this is the weight class the user chooses
    weight = json_data["weight"]
    for vehicle in vehicles:
        try:
            if weight == "0":
                #print( vehicle['fields']['Year'] )
                # gets all vehicles
                front_visible = getfrontvisible(vehicle)
                side_visible = getsidevisible(vehicle)
                model = getmodel(vehicle)
                year = getyear(vehicle)
                weight_class = getweightclass(vehicle)
                image = getimage(vehicle)
                front = getfront(vehicle)
                side = getside(vehicle)
                overhead = getoverhead(vehicle)
                value = { 'Overall Visibility': vehicle['fields']['Percent Visible Volume'], 'Front Visibility': front_visible,
                'Side Visibility': side_visible, 'Make': vehicle['fields']['Make'], 'Model': model,
                'Year': year, 'Weight Class': weight_class, 'Image': image, 'Front': front, 'Side': side, 'Overhead': overhead }
                # print(value)
                scores.append( value )
            else:
                wclass = vehicle['fields']['Weight Class']
                # gets all vehicles of WEIGHT class and that have a year
                if wclass is not None and wclass == 'Class ' + str(weight):
                    if vehicle['fields']['Year'] != "Please select a year":
                        value = { 'Overall Visibility': vehicle['fields']['Percent Visible Volume'], 'Front Visibility': vehicle['fields']['Percent Visible Volume in Front'],
                        'Side Visibility': vehicle['fields']['Percent Visible Volume in Passenger Side'], 'Make': vehicle['fields']['Make'], 'Model': vehicle['fields']['Model'],
                        'Year': vehicle['fields']['Year'], 'Weight Class': vehicle['fields']['Weight Class'], 'Image': vehicle['fields']['Image URL'] }
                        scores.append( value )
        except:
            pass
            #print(vehicle['fields'])

    #print(scores)
    return JsonResponse({"data": scores})

def getfrontvisible(vehicle):
    if ('Percent Visible Volume in Front' not in vehicle['fields']):
        return "N/A"
    else:
        return vehicle['fields']['Percent Visible Volume in Front']

def getsidevisible(vehicle):
    if ('Percent Visible Volume in Passenger Side' not in vehicle['fields']):
        return "N/A"
    else:
        return vehicle['fields']['Percent Visible Volume in Passenger Side']

def getmodel(vehicle):
    if ('Model' not in vehicle['fields']):
        return "N/A"
    else:
        return vehicle['fields']['Model']


def getyear(vehicle):
    if ('Year' not in vehicle['fields'] or vehicle['fields']['Year'] == "Please select a year"):
        return "N/A"
    else:
        return vehicle['fields']['Year']

# if vehicle doesn't have weight class, assign weight class as "N/A", otherwise return weight class value
def getweightclass(vehicle):
    if ('Weight Class' not in vehicle['fields'] or vehicle['fields']['Weight Class'] == "Please select a class"):
        return "N/A"
    else:
        return vehicle['fields']['Weight Class']

# if vehicle doesn't have image, assign image as "N/A", otherwise return image
def getimage(vehicle):
    if ('Image URL' not in vehicle['fields']):
        return ""
    else:
        return vehicle['fields']['Image URL']

def getfront(vehicle):
    if ('Front Image String' not in vehicle['fields']):
        return ""
    else:
        return vehicle['fields']['Front Image String']

def getside(vehicle):
    if ('Side Image String' not in vehicle['fields']):
        return ""
    else:
        return vehicle['fields']['Side Image String']

def getoverhead(vehicle):
    if ('Overhead Image String' not in vehicle['fields']):
        return ""
    else:
        return vehicle['fields']['Overhead Image String']

# not used at the moment, but returns array with key and value mappings as opposed to just values, like getddata()
@require_http_methods(["POST"])
def getvehicles(request):
    json_data = json.loads(request.body.decode("utf-8"))
    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR')
    vehicles = at.get_all(fields=['Percent Visible Volume', 'Make', 'Model', 'Year', 'Weight Class'])
    return JsonResponse({"data": vehicles})

def getvehicleimages(index, vru = 1):

    strs = create_easy_images(index, 2, vru)
    #print(strs)
    #return JsonResponse({"front":strs[0], "side":strs[1], "top":strs[2] })
    return strs

@require_http_methods(["POST"])
def getvehicleimages_vruchanged(request):
        #try:
        json_data = json.loads(request.body.decode("utf-8"))
        index = int(json_data['id_num'])
        vru = int(json_data['vru'])
        print("the vru is " + str(vru) )

        if vru == 1:
            at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR')
            vehicle = at.match('ID', index)['fields']
            #print(vehicle)
            try:
                strs = [ vehicle['Front Image String'], vehicle['Side Image String'], vehicle['Overhead Image String'] ]
            except:
                strs = [ vehicle['Front Image String'], "" ]

        else:
            try:
                if int(json_data['onlyeasy']) == 1:
                    strs = getvehicleimages(index, vru)
                else:
                    strs = list( create_all_images(index, 2, vru) );
            except Exception as e:
                return JsonResponse( {'data': [str(e)] } )

        return JsonResponse( {'data': strs, 'vru': vru} )
        """
        except Exception as e:
            return JsonResponse({"data": "PYTHON ERROR: " + str(e)})
        """
@require_http_methods(["POST"])
def getspecificimage(request):
    json_data = json.loads(request.body.decode("utf-8"))

    json_string = json_data['json_string']
    index = json_data['index']
    mode = json_data['mode']
    vru = json_data['vru']

    if mode == 0:
        image_string = create_specific_image(json_string, 2, vru, index)
        image_string = image_string.decode()
    elif mode == 1:
        try:
            image_string = create_overhead_only(json_string, 2, vru)
        except Exception as e:
            return JsonResponse( {'data': str(e) } )

    return JsonResponse({"data": image_string, "vru": vru})
@require_http_methods(["POST"])
def uploadimages(request):
    json_data = json.loads(request.body.decode("utf-8"))
    id_num = json_data['id_num']
    url = json_data['url']
    field = json_data['field']


    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR')
    vehicle = at.match('ID', id_num)['id']

    #print(vehicle)

    at.update(  vehicle, { field + ' Image String' : url } )


    return HttpResponse("Done")
