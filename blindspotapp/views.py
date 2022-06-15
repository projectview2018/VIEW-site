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

# pandas imports
import pandas as pd

# Create your views here.

def home(request):
    return render(request, "home.html")

def index(request):
    return render(request, "index.html")

def visualize(request):
    return render(request, "visualize.html")

def FAQs(request):
    return render(request, "faq.html")

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
    perc_front = None;
    perc_side = None;
    if user_data is not None:
        perc_data = at.match('ID', user_data)
        if perc_data != {}:
            if "Percent Visible Volume in Front" in perc_data["fields"].keys():
                perc_front = perc_data["fields"]["Percent Visible Volume in Front"]
            if "Percent Visible Volume in Passenger Side" in perc_data["fields"].keys():
                perc_side = perc_data["fields"]["Percent Visible Volume in Passenger Side"]

            make = perc_data["fields"]["Make"]
            model = getmodel(perc_data)
            year = getyear(perc_data)

            # perc_data is analagous to vehicle
            percentile = getpercentile(perc_data, vehicles)
            # changing perc_data to be percent visible volume instead of a dictionary
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
                    text='<b>This Vehicle</b>',
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
        title_text="Histogram of Overall Vehicle Percent Visible Volumes", title_x=0.5,
        yaxis_title="Number of Entries in Database",
        xaxis_title="Overall Visibility (%)",
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
    return (plt_div, user_data, perc_front, perc_side, percentile, make, model, year)


def compress_image_url(img_url):
    #This function adds 'q_auto:eco' to cloudinary urls for compression
    urll = img_url.split('/')
    urll.insert(6, 'q_auto:eco')
    urll = '/'.join(urll)
    return(urll)

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
        panor_img = compress_image_url(panor_img)


    #if there is nothing in there, it is a previous entry that can be ignored
    if 'Front Image String' in vehicle['fields']:
        front_img = vehicle['fields']['Front Image String']
        front_img = compress_image_url(front_img)

    if 'Side Image String' in vehicle['fields']:
        side_img = vehicle['fields']['Side Image String']
        side_img = compress_image_url(side_img)

    if 'Overhead Image String' in vehicle['fields']:
        top_img = vehicle['fields']['Overhead Image String']
        top_img = compress_image_url(top_img)
        #print (top_img)
    return( panor_img, front_img, side_img, top_img )

# generates two sentences at the top of the getinfo page describing the vehicle, and generates the vehicle images
def getinfo(request, user_data=None):
    plot_div, percen, front_percen, side_percen, percentile, make, model, year = makehistogram(user_data)

    """
    img = Image.new('RGB', (10, 10), (255, 0, 0) )
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    """
    #iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAEklEQVR4nGP8z4APMOGVHbHSAEEsAROxCnMTAAAAAElFTkSuQmCC
    if user_data is not None and percen is not None:

        user_results = ""
        # add vehicle identifier information for make/model/year
        # check if year exists or not, otherwise page will error
        if year == "N/A":
            user_results += "This is a {} {}. This vehicle has an overall percent visible volume of {}%".format(make, model, percen)
        else:
            user_results += "This is a {} {} {}. This vehicle has an overall percent visible volume of {}%".format(year, make, model, percen)

        if front_percen and side_percen:
            user_results += ", a front visibility score of {}%".format(front_percen)
            user_results += ", and a side visibility score of {}%".format(side_percen)
        elif side_percen:
            user_results += " and a side visibility score of {}%".format(side_percen)
        elif front_percen:
            user_results += " and a front visibility score of {}%".format(front_percen)
        user_results += ". "

        # percentile ends in 1
        if (percentile % 10 == 1):
            user_results += "This vehicle's overall visibility sits at the {}st percentile relative to all other vehicles in the same body class.".format(percentile)
        # percentile ends in 2
        elif (percentile % 10 == 2):
            user_results += "This vehicle's overall visibility sits at the {}nd percentile relative to all other vehicles in the same body class.".format(percentile)
        # all other cases
        else:
            user_results += "This vehicle's overall visibility sits at the {}th percentile relative to all other vehicles in the same body class.".format(percentile)

        panor_img, front_img, side_img, top_img = get_images_from_airtable(user_data)
        return render(request, "getinfo.html", context={'plot_div': plot_div, 'user_results': user_results, 'id_num':user_data, 'panor_img': panor_img, 'front_img':front_img, 'side_img': side_img, 'top_img':top_img, 'percen': percen})

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
    bodyclass = json_data['bodyclass']
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
        drawing_URL  = "https://res.cloudinary.com/usdot/image/upload/v1641395694/sample.jpg"
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
                "Year": vyear, "Body Class": bodyclass, "Percent Visible Volume": perc_vis[0], 'a':a, "b": b,'c':c, "d": d, "Radial Distance": radial_distance,
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
                'Image':[image], 'Image URL':image_URL, 'Drawing':[drawing], 'Phis and NVPS json':phis_and_nvps, 'Overhead Image String':overhead_string,
                "Overall Vis Elem":perc_vis[2], "Front Vis Elem":perc_front[2], "Side Vis Elem":perc_passenger[2],
                "Overall Vis Adult":perc_vis[3], "Front Vis Adult":perc_front[3], "Side Vis Adult":perc_passenger[3]}
    # print(record)
    inserted_record = at.insert(record)

    id_num = inserted_record['fields']['ID']
    if perc_vis[0] < 60 :
        strs = getvehicleimages(id_num, 5)

    else:
        strs = getvehicleimages(id_num, 1)
    strs[0] = upload_to_cloudinary(strs[0], id_num, "Front")
    strs[1] = upload_to_cloudinary(strs[1], id_num, "Side")

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
    interest_area = [0, 0, 0, 0]
    for i in range(4):
        interest_area[i] = find_total_truck_interest_area(angles, b, d, i)
    print("starting stick figure")
    preschool_children, grade_school_children, grade_school_bicyclists, wheelchair_users,adult_bicyclists, adults = do_stick_figure_analyses(a,c,d)
    print("finished stick figure")
    return JsonResponse({"data": interest_area,
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
    blind_area = [0, 0, 0, 0]
    interest_area = [0, 0, 0, 0]
    for i in range(4):
        blind_area[i] = find_total_truck_blind_area(NVPs, angles, DH, b, d, i)
        interest_area[i] = find_total_truck_interest_area(angles, b, d, i)
    return JsonResponse({"data": blind_area, "total_volume":interest_area})

#
@require_http_methods(["POST"])
def getddata(request):
    json_data = json.loads(request.body.decode("utf-8"))
    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR') # base key, table name, API key
    vehicles = at.get_all()

    # each element in scores is a dictionary of [overall visibility, front visibility, side visibility, make, model, year, body class, weight class, image, front, side, overhead, ID]
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
                bodyclass = getbodyclass(vehicle)
                weight_class = getweightclass(vehicle)
                image = getimage(vehicle)
                front = getfront(vehicle)
                side = getside(vehicle)
                overhead = getoverhead(vehicle)
                percentile = getpercentile(vehicle, vehicles)

                value = { 'Date Added' : vehicle['fields']['Date Added'],
                            'Overall Visibility': vehicle['fields']['Percent Visible Volume'], 'Front Visibility': front_visible,
                'Side Visibility': side_visible, 'Make': vehicle['fields']['Make'], 'Model': model,
                'Year': year, 'Body Class': bodyclass, 'Weight Class': weight_class, 'Image': image, 'Front': front, 'Side': side,
                'Overhead': overhead, 'ID': vehicle['fields']['ID'], 'Percentile': percentile}
                # print(value)
                scores.append( value )
            else:
                wclass = vehicle['fields']['Weight Class']
                # gets all vehicles of WEIGHT class and that have a year
                if wclass is not None and wclass == 'Class ' + str(weight):
                    if vehicle['fields']['Year'] != "Please select a year":
                        value = { 'Date Added' : vehicle['fields']['Date Added'],
                            'Overall Visibility': vehicle['fields']['Percent Visible Volume'], 'Front Visibility': vehicle['fields']['Percent Visible Volume in Front'],
                        'Side Visibility': vehicle['fields']['Percent Visible Volume in Passenger Side'], 'Make': vehicle['fields']['Make'], 'Model': vehicle['fields']['Model'],
                        'Year': vehicle['fields']['Year'], 'Weight Class': vehicle['fields']['Weight Class'], 'Image': vehicle['fields']['Image URL'] }
                        scores.append( value )
        except:
            pass
            #print(vehicle['fields'])

    return JsonResponse({"data": scores})

@require_http_methods(["POST"])
def getunduplicateddata(request):
    json_data = json.loads(request.body.decode("utf-8"))
    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR') # base key, table name, API key
    vehicles = at.get_all()

    #return JsonResponse({"data": vehicles})
    print(vehicles[0])
    vehicles_df = pd.DataFrame.from_records((v['fields'] for v in vehicles))
    print(vehicles_df)
    agg_dict = {
        'ID': 'first',
        'Percent Visible Volume': 'median',
        'Percent Visible Volume in Front': 'median',
        'Percent Visible Volume in Passenger Side': 'median',
        'Body Class': 'first',
        'Weight Class': 'first',
        'Image URL': 'first',
        'Front Image String': 'first',
        'Side Image String': 'first',
        'Overhead Image String': 'first',
        'Make': 'first',
        'Model': 'first',
        'Year': 'first'
    }

    rename_dict = {
        'Percent Visible Volume': 'Overall Visibility',
        'Percent Visible Volume in Front': 'Front Visibility',
        'Percent Visible Volume in Passenger Side': 'Side Visibility',
        'Image URL': 'Image',
        'Front Image String': 'Front',
        'Side Image String': 'Side',
        'Overhead Image String': 'Overhead'
    }

    make_clean = vehicles_df['Make'].str.lower().str.strip().str.replace(' ', '')
    model_clean = vehicles_df['Model'].str.lower().str.strip().str.replace(' ', '')
    year_clean = vehicles_df['Year']
    vehicles_df['Make Clean'] = make_clean
    vehicles_df['Model Clean'] = model_clean
    vehicles_df['Year Clean'] = year_clean

    grouped_df = vehicles_df.groupby(["Make Clean", "Model Clean", "Year Clean"], as_index=False).agg(agg_dict)
    grouped_df = grouped_df.rename(columns=rename_dict)
    grouped_df = grouped_df.drop(['Make Clean', 'Model Clean', 'Year Clean'], 1)
    grouped_df['Percentile'] = 0 # placeholder for now

    # classifies body classes into the categories we defined
    grouped_df['Body Class'] = grouped_df['Body Class'].replace({
    'Convertible/Cabriolet': 'Passenger', 'Coupe': 'Passenger', 'Hatchback/Liftback/Notchback': 'Passenger', 'Roadster': 'Passenger', 'Sedan/Saloon': 'Passenger', 'Wagon': 'Passenger',
    'Sport Utility Vehicle (SUV)/Multi-Purpose Vehicle (MPV)': 'SUV', 'Crossover Utility Vehicle (CUV)': 'SUV',
    'Minivan': 'Minivan',
    'Van': 'Van', 'Cargo Van': 'Van',
    'Pickup': 'Pickup Truck',
    'Truck': 'Commercial Truck', 'Trailor': 'Commercial Truck', 'Truck-Tractor': 'Commercial Truck',
    'Bus': 'Bus', 'Bus - School Bus': 'Bus',
    'No VIN': 'N/A', '': 'N/A', 'Incomplete - Chassis Cab (Number of Cab Unknown)': 'N/A'})

    # replace NaN front/side visibility scores with 0, because otherwise the code errors
    grouped_df['Front Visibility'] = grouped_df['Front Visibility'].fillna(0)
    grouped_df['Side Visibility'] = grouped_df['Side Visibility'].fillna(0)

    # dataframes are not JSON serializable, so convert to a list of dictionaries
    grouped_df_list = grouped_df.to_dict('records')
    #print(grouped_df_list[0])

    return JsonResponse({"grouped_data": grouped_df_list})

def getfrontvisible(vehicle):
    if ('Percent Visible Volume in Front' not in vehicle['fields']):
        return 0
    else:
        return vehicle['fields']['Percent Visible Volume in Front']

def getsidevisible(vehicle):
    if ('Percent Visible Volume in Passenger Side' not in vehicle['fields']):
        return 0
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

# gets vPIC body class and classifies it into one of our seven labels (N/A, passenger, SUV, minivan, van, pickup, commercial truck, or bus)
def getbodyclass(vehicle):
    # for vehicles with no vin, though we could manually add the body class for these vehicles
    if ('Body Class' not in vehicle['fields']):
        return 'N/A'
    # passenger
    elif (vehicle['fields']['Body Class'] in ['Convertible/Cabriolet', 'Coupe', 'Hatchback/Liftback/Notchback', 'Roadster', 'Sedan/Saloon', 'Wagon']):
        return 'Passenger'
    # SUV
    elif (vehicle['fields']['Body Class'] in ['Sport Utility Vehicle (SUV)/Multi-Purpose Vehicle (MPV)', 'Crossover Utility Vehicle (CUV)']):
        return 'SUV'
    # minivan
    elif (vehicle['fields']['Body Class'] in ['Minivan']):
        return 'Minivan'
    # van
    elif (vehicle['fields']['Body Class'] in ['Van', 'Cargo Van']):
        return 'Van'
    # pickup truck
    elif (vehicle['fields']['Body Class'] in ['Pickup']):
        return 'Pickup Truck'
    # commercial truck
    elif (vehicle['fields']['Body Class'] in ['Truck', 'Trailor', 'Truck-Tractor']):
        return 'Commercial Truck'
    # bus
    elif (vehicle['fields']['Body Class'] in ['Bus', 'Bus - School Bus']):
        return 'Bus'
    # all other categories
    else:
        return 'N/A'

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

# gets vehicle's overall visibility percentile relative to all other vehicles in its body class
def getpercentile(vehicle, vehicles):
    allScores = []
    vehicle_bc = getbodyclass(vehicle)
    # allScores has overall visibility scores for all vehicles with the same body class
    for entry in vehicles:
        if getbodyclass(entry) == vehicle_bc:
            allScores.append(entry['fields']['Percent Visible Volume'])
    count_below = len([i for i in allScores if i < vehicle['fields']['Percent Visible Volume']])
    percentile = round(count_below / len(allScores) * 100)
    #print(percentile, vehicle['fields']['ID'])
    return percentile

# not used at the moment, but returns array with key and value mappings as opposed to just values, like getddata()
@require_http_methods(["POST"])
def getvehicles(request):
    json_data = json.loads(request.body.decode("utf-8"))
    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR')
    vehicles = at.get_all(fields=['Percent Visible Volume', 'Make', 'Model', 'Year', 'Weight Class'])
    return JsonResponse({"data": vehicles})

def getvehicleimages(index, vru = 1):

    strs = create_easy_images(index, 5, vru)
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
        print(json_data)

        if vru == json_data['default']:
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
                print( str(e))
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
        #try:
        image_string = create_overhead_only(json_string, 2, vru)
        """
        except Exception as e:
            print(str(e))
            return JsonResponse( {'data': str(e) } )
        """
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

def upload_to_cloudinary(img_string, i, image_index):
    #Project VIEW Cloudinary
#    cloudinary.config(
#      cloud_name = "dkrq49vzq",
#      api_key = "733231156826462",
#      api_secret = "tf4ebuGXPE1AS5ZlGqG6WkQWTXU",
#      secure = True
#    )

    #Eric Cloudinary
    cloudinary.config(
    cloud_name = "usdot",
    api_key = "848361382832925",
    api_secret = "-YnQbZxMGQfo0EncUOCnOjk7qZs"
    )

    uploaded = cloudinary.uploader.upload("data:image/png;base64," + img_string,
        folder = "generated-images",
        public_id = str(i) + "-" + image_index,
        overwrite = True,
        notification_url = "https://mysite.example.com/notify_endpoint")

    if 'url' in uploaded.keys():
        return uploaded['url']
