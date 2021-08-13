from PIL import Image, ImageDraw, ImageFont, ImageOps
import sys
import base64
from plotly.offline import plot
import plotly.graph_objs as go
from io import BytesIO
from sympy import * #probably not necessary anymore, should probably be taken out?
from math import pow
import requests
import json
from blindspotapp.Airtable import Airtable
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
# preschool children, grade school children, grade school bicycle, wheelchair, adult bicycle, adult
#shoulder height, width, person height
people = [ (28,9, 34), (37,12, 45), (35, 12, 45), (39,26, 49), (47,16, 58), (49,16, 60) ]

#general notes

#in this document, many of the debugging print statements have been commented out. this is to improve runtime
#with overhead image generation, a lot of attention was paid to improving runtime as much as possible because it is often the slowest one
#   there should be a document in the development channel that goes over the ways that i improved runtime
#there is a separate repository with image generation related scripts, mainly for making renders for reports and updating old records with new images
#   talk to Eric or Brian to get access to this
#   whenever a significant update to this script is made, the methods should be copied over to the "image_generation.py" file. then, the asset locations need to be changed
#the driver height is an important value because the type of car drawn on the images is determined by driver height when there is no vin
#   either < 70 is a car and other than that it's a truck, or <60 is a sedan, <70 is a sedan, and >= 70 is a truck
#   these are hardcoded based off of the airtable values at the time of development (summer 2021)
#   if you ever want to change these, i would suggest having setting a global array/dictionary for cutoff values
#the static images used as assets were created by the following methods
#   front image cars: downloaded from the vpic database https://vpic.nhtsa.dot.gov/decoder/Decoder and then colored using adobe photoshop / photopea.com
#   side image car old: generated via polygons and a bunch of calculations
#   side image car new: stock images from 123rf.com
#   top image: car was from google images, truck was a stock image from 123rf.com
#   vrus for front and side: microsoft office cutout people with a white color overlay applied in photoshop / photopea. for vrus with bicycles, the stock 3d model of a bicycle was posed so that you only see its front. then, cutout people who were sitting down were superimposed. some pixels were removed, and the color overlay was applied
#   full versions of the 123rf images can be found in the generate image github repository (should be shared with Eric and Brian)
#whenever text is needed, you have to include a .ttf or .otf (font file format) within the website github repository. if you try to use just any font, you'll get a python error.
#   right now, there is an arial.ttf font that can be used. in fact, the arial.ttf font is used as a default because it was the first font i thought of. feel free to look up better fonts for low-res screens
#   one big consideration with fonts is how much horizontal space they take up; you need to be able to fit "999 elementary school children on bicycles" in the space given
#image scale / compression
#   a higher scale = more pixels to draw = slower, but with readability is also important. hopefully in the future the scale can be doubled to 5 with .png compression
#   for mockup renders (like for official reports), the code in the respository should be used with a scale of 5+
#there is a new create side image thing that uses stock photos - ask Eric / Alex to switch to this if you think it looks better
#for debugging purposes, comment out the lines relating to resizing and cropping the image. this will allow you to look at an image that uses the same pixel values as the code



#airtable interface

#get values for front view
def get_data_front(id_num):
    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR')
    vehicle = at.match('ID', id_num)
    try:
        json_string = vehicle['fields']['Phis and NVPS json']
        data = json.loads(json_string)

        if not "processed" in data.keys() or data['processed'] == 0:
            phis = data['pf']
            nvps = data['gf']
        else:
            phis = data['phis']
            nvps = data['nvps']

        index = 0
        min_diff = 0
        if 90 in phis:
            index = phis.index(90)
        else:
            #find the closest value to 90, but immediately settle for anything within 1
            #has some errors with accuracy / matching up with the overhead view on first pass
            for i in range( len(phis) ) :
                if  abs(phis[i] - 90) <= 1:
                    index = i
                    break

                if min_diff > abs(phis[i]):
                    index = i
                    min_diff = abs(phis[i])
        c = round(nvps[index])
    except:
        #if the entry is old, use the c value and assume that it was taken 12 inches from the ground.
        c = vehicle['fields']['c']
        c = round( -1 * c / ( 12/vehicle['fields']['a'] - 1) )

    return_vals = [ vehicle['fields']['a'], c, vehicle['fields']['d'] ]

    if vehicle['fields']['Full VIN'] != "NA":
        return_vals.append(vehicle['fields']['Full VIN'])
    return return_vals
# get values for side view
def get_data_side(id_num):
    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR')
    vehicle = at.match('ID', id_num)
    #print("got vehicle")
    try:
        json_string = vehicle['fields']['Phis and NVPS json']
        data = json.loads(json_string)
        #print(not "processed" in data.keys() or data['processed'] == 0)
        if not "processed" in data.keys() or data['processed'] == 0:
            phis = data['pp']
            nvps = data['gp']

        else:
            phis = data['phis']
            nvps = data['nvps']

        min_diff = 0
        index = 0
        if 0 in phis:
            index = phis.index(0)
        else:
            #find the closest value to 0, but immediately settle for anything within 1
            for i in range( len(phis) ) :
                if abs(phis_p[i]) <= 1 :
                    index = i
                    break

                if min_diff > abs(phis[i]):
                    index = i
                    min_diff = abs(phis[i])


        nvp = nvps[index]


        a = vehicle['fields']['a']
        b = vehicle['fields']['b']
        return (a, b, nvp)
    except Exception as e:
        print( str(e))
        return None
#get values for overhead
def get_data_top(id_num):
    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR')
    vehicle = at.match('ID', id_num)
    try: #this is basically for the accesses to vehicle['fields'].
        json_string = vehicle['fields']['Phis and NVPS json']
        data = json.loads(json_string)

        abd = ( vehicle['fields']['a'], vehicle['fields']['b'], vehicle['fields']['d'])

        return get_data_top_combined( abd, data, id_num)
    except:
        return None
#parse json string for datavalues - this was used when overhead image generation was attempted during step 11, but now is basically unused.
def get_data_top_json(json_string):

    data = json.loads(json_string)

    abd = ( data['a'], data['b'], data['d'])
    return get_data_top_combined( abd, data, id_num)

#put in its own menthod in case the "generate overhead image upon step 10 being done" is ever re-implemented
def get_data_top_combined( abd, data, id_num):

    # if the data has not been processed yet, then process it and reupload it to the airtable. if the string has already been processed, we can skip this step, dramatically helping runtime
    if not "processed" in data.keys() or data['processed'] == 0:
        #set up a main list with length 360 (maybe 2, to keep track of how many repeats there are) - one for each degree. then, array assignments could be made based off the values.
        #hopefully, this can get rid of the need for sorting (nlogn). additionally, there would only need to be 1 pass through phis_f and phis_p (to add the values to the main list), then 1 pass through the main list for averaging repeated values and/or making the gaps the "max" value
        #this could make the averaging and removing duplicates function less janky
        #a futher advantage would be that when finding adding vrus, it will be faster to be like data[bot_left] ( o(1) ) instead of the binary search ( o(lg(n)) )
        #of course, this will mess with accuracy
        #the old code is left as a comment

        main_list = [0] * 360
        num_dupl = [0] * 360

        #get and round the front phis / nvps
        # in the future, when all phis are rounded to the closest integer, these can simply be phis_f = data['pf'], which will speed stuff up
        phis_f = [int(round(x,0)) for x in data['pf']]
        nvps_f = data['gf']

        #get and round the passenger phis / nvps
        phis_p = [int(round(x,0)) for x in data['pp']]
        nvps_p = data['gp']

        #get the max values
        max_f = max(nvps_f)
        max_p = max(nvps_p)
        max_rad = max(max_f, max_p) #for a pillar nvps, later


        measured = max(phis_f) - min(phis_p)
        #print(max(phis_f), min(phis_p))
        #print(measured)

        for i in range( len(phis_f) ):

            main_list[ phis_f[i] ] += nvps_f[i]
            num_dupl[ phis_f[i] ] += 1
        for i in range( len(phis_p) ):
            main_list[ phis_p[i] ] += nvps_p[i]
            num_dupl[ phis_p[i] ] += 1

        for i in range( len(main_list) ):

            if num_dupl[i] == 0:
                main_list[i] = max_rad
            elif num_dupl[i] > 1:
                main_list[i] = main_list[i] / num_dupl[i]


        #print("process indiv arrays")
        #rotate the list so that the "measured" values are first
        min_meas_phi = min(phis_p)
        #print(min_meas_phi)
        main_list = main_list[min_meas_phi:] + main_list[: min_meas_phi]
        phis_data = list( range(min_meas_phi, min_meas_phi + 360 ) )

        #print(main_list)
        #print(phis_data)


        #new_dictionary = { "phis": phis_p, "nvps": nvps_p, "measured": measured, "other": (abd[1], abd[2], max_rad, abd[0]), 'processed':1 }
        new_dictionary = { "phis": phis_data, "nvps": main_list, "measured": measured, "other": (abd[1], abd[2], max_rad, abd[0]), 'processed':1 }
        json_new_string =  json.dumps(new_dictionary, separators=(',', ':'))
        upload_json_to_airtable(id_num, json_new_string) #comment this line out if you don't wanna update airtable (for debugging purposes)

        return [ phis_data, main_list , measured, (abd[1], abd[2], max_rad, abd[0])]
    else:
        phis_p = data['phis']
        nvps_p = data['nvps']
        measured = data['measured']
        other_data = data['other']
        #print(other_data)
        return [ phis_p, nvps_p , measured, other_data]

def upload_json_to_airtable(id_num, json_string):
    at = Airtable('appeO848S1Ia1icdL', 'VEHICLES', 'keyk5gsH5fD2iJrrR')
    vehicle = at.match('ID', id_num)['id']
    at.update(  vehicle, { "Phis and NVPS json" : json_string } )

# basic math functions - most of these are not used anymore, especially the ones relating to arcs.

# get the intersection of two lines
def get_line_intersection(a, c, x0, y0, x1, y1):
    m1 = float(-1 * a) / c
    b1 = a

    m2 = float( (y1 - y0) / (x1 - x0) )
    b2 = y0 - m2 * x0

    x = x0
    while (x < x1 ):
        if (m1 * x + b1) - (m2 * x + b2) <= .05:
            return [x, m1 * x + b1]
        x += 1
# get the intersection of an arc with a line
def get_arc_intersection(a, c, x0, y0, x1, y1, mode = 0):

    #print(str(x0) + " " + str(y0) + " " + str(x1) + " " + str(y1));


    #a = a * s
    #c = c * s

    m = float(-1 * a) / c
    s = a

    #print(str(a) + " " + str(c) + " " + str(m) + " " + str(s) )

    b = abs (y0 - y1 )
    a = x1 - x0

    h = x0;
    k = y1;

    #print(str(a) + " " + str(b) + " " + str(h) + " " + str(k) )


    x = Symbol('x')
    ans = solve( ( 1 - ( (x-h) / a) ** 2) ** .5 * b + k - (m *x + s) , x)
    #print(ans)
    if mode == 0:
        if len(ans) > 1:
            x_val = max(ans[0], ans[1] )
        else:
            x_val = ans[0]
        y_val = m * x_val + s
        return [ int(x_val), int(y_val) ]
    else:
        return ans
# get the shift needed to make a line tangent to an arc
def get_arc_shift(a, c,  x0, y0, x1, y1, ans):
    #a = a * s
    #c = c * s
    m = float(-1 * a) / c
    s = a
    b = abs (y0 - y1 )
    a = x1 - x0
    h = x0;
    k = y1;

    x = ans[0]
    max_diff = 0

    if ( len(ans) == 1) :
        x = x0
        while x < x1:
            arc = ( 1 - ( (x-h) / a) ** 2) ** .5 * b + k
            line = (m *x + s)
            max_diff = max( arc - line, max_diff)
            x = x + 1
        return max_diff
    else:

        while x < ans[1]:
            arc = ( 1 - ( (x-h) / a) ** 2) ** .5 * b + k
            line = (m *x + s)
            max_diff = max( arc - line, max_diff)
            x = x + 1
        return max_diff
# get the y value for a certain x value on a line
def get_hood_height(a, c, d):
    # 0, a and c, 12
    #a = s * a
    #c = s * c
    #d = s * d
    m = float(-1 * a) / c
    b = a
    return int( (m * d + b) )
#get the x value for a certain y value on a line
def get_ws_width(a, c, y):
    # 0, a and c, 12
    #a = s * a
    #c = s * c
    m = float(-1 * a) / c
    b = a
    return int( (y - b) / m )
#return a box for an arc given two corners
def arc_box( x0, y0, x1, y1):
    return [ 2 * x0 - x1, y0, x1, 2 * y1 - y0 ]
#return a line given two points
def get_line( x0, y0, x1, y1):
    m = (y1 - y0) / (x1 - x0)
    b = y0 - m * x0
    return (m , b)
#return a line that intersects a given line
def get_window_height(a, b, nvp, s, ceiling):
    (m1,b1) = get_line(0, a, nvp, 0)

    for x in range(b,  round(nvp) ):
        y = m1 * x + b1
        (m2, b2) = get_line(x, y, 5 * x / 6, ceiling )
        if m2 * b + b2 - a < 1:
            reserved = (x * s, y * s)
            if m2 * b + b2 - a < .1:
                return (x * s, y * s)
    return reserved

# VRU helper functions

#get a better bounding box for the overhead view
def improve_box( data, box_indices, index):
    box = [0, 0, 0, 0]
    a = data[3][3]

    #for each maximum point, find the maximum number of children. the number of children in each of the four directions will determine the size of the box
    for i in range( 4 ):
        if i % 2 == 0: #x values - grab cos
            distance = abs( cos(data[0][box_indices[i]] * 3.14 / 180) * data[1][box_indices[i]] )
        else:
            distance = abs( sin(data[0][box_indices[i]] * 3.14 / 180) * data[1][box_indices[i]] )
        box[i] = int(  round( find_number_in_blind_zone(a, distance, 0, index) ) + 1 )
    box[0] = -1 * box[0]
    box[1] = -1 * box[1]

    return box
#get the maximum points for the phis - a bounding box of sorts
def get_whole_box(phis, nvps, measured):

    min_x = 0
    min_x_i = 0
    min_y = 0
    min_y_i = 0
    max_x = 0
    max_x_i = 0
    max_y = 0
    max_y_i = 0

    #iterate through all the measured values and find the min/max x/y
    for i in range( measured) :
        #print(i, measured, len(phis) )
        curr_x = cos(phis[i] * 3.14 / 180) * nvps[i]
        if curr_x > max_x:
            max_x = curr_x
            max_x_i = i
        elif curr_x < min_x:
            min_x, min_x_i = curr_x, i

        curr_y = sin(phis[i] * 3.14 / 180) * nvps[i]
        if curr_y > max_y:
            max_y, max_y_i = curr_y, i
        elif curr_y < min_y:
            min_y, min_y_i = curr_y, i
    return ( min_x_i, min_y_i, max_x_i, max_y_i)

# VRU drawing functions

# add vrus to the overhead image
def add_VRU_top(fig, data, scale,s, index = 0, fast = True):
    #s is the main image scale, while scale is the local scale for the image based off the max nvp

    #all this is done on a new image which will then be placed on the figure
    img = Image.new("RGBA", (200 * s, 200 *s), (255, 255, 255, 0))
    p_width = people[index][1]
    p_height = people[index][0]

    #other methods of grid generation exist and each give different results. This has been found to be the quickest so far
    box_indices = get_whole_box(data[0], data[1], data[2] )
    bounding_box = improve_box( data, box_indices, index )

    width_boxes = bounding_box[2] - bounding_box[0]
    height_boxes = bounding_box[3] - bounding_box[1]

    for i in range( len (bounding_box)):
        bounding_box[i] *= p_width

    num_people = 0
    a = data[3][3]
    data[0] = data[0][0:data[2]]

    min_phi = data[0][0]
    max_phi = data[0][-1]

    #print(data[0])
    data[1] = data[1][0:data[2]]
    rotate_by = data[0].index(0)
    #print(rotate_by)
    #data[0] = data[0][rotate_by:] + data[0][: rotate_by]
    data[1] = data[1][rotate_by:] + data[1][: rotate_by]
    #print(data[0])



    #this checks stop calculations from being done if they are already deemed to be impossible. if a calculation for a box is done, and it has shown to not fit the vru, then any other further box using the same angle is guaranteed to also not show anything.
    no_phi = []
    #iterate through each box in the grid
    for i in range(width_boxes):
        #possible_y = True
        for j in range(height_boxes):

            #get the box and bot_left, which is the angle of the bottom left hand corner of the box
            #only the height at the left hand corner will be tested for speed reasons. in the top right quadrant, this means that we will overestimate the number of vrus, which probably makes for a better visual. this will underestimate the number of vrus in not the top right quadrant
            box = [ bounding_box[0] + i * p_width,  bounding_box[1] + j * p_width, int( bounding_box[0] + (i + 1) * p_width), int( bounding_box[1] + (j + 1) * p_width )]
            #print(box)

            #this calculates the bot_left angle - there are some edge cases
            if box[0] == 0:
                bot_left = 90
            else:
                bot_left = atan(box[1] / box[0] ) * 180 / 3.14

            if box[0] < 0 :
                bot_left += 180

            #this is to see if the box is within the bounds of the vehicle picture
            if (not int(bot_left) in no_phi) and ( box[1] > data[3][1] or box[0] > data[3][0]):


                bot_left_h = -1

                #checks to see if the angle of the bottom left hand corner is within the range of what is measured
                if bot_left < min_phi:
                    bot_left_h = 0
                    #print(i, j, bot_left)
                elif bot_left > max_phi:
                    bot_left_h = 0
                    #print(i, j, bot_left)
                else:

                    bot_left = int(round(bot_left))

                    """
                    #do a binary search for the smallest angle larger than the current one
                    k = int(data[0][ len(data[0]) // 2])

                    low = 0
                    high = data[2]
                    while low != high:
                        if (data[0][k] <= bot_left):
                            low = k + 1;
                        else:
                            high = k;
                        k = int((low + high) // 2)

                    k = low
                    """
                    curr_nvp = data[1][bot_left]
                    radius = (box[1] ** 2 + box[0] ** 2   )**.5
                    bot_left_h = a * ( (curr_nvp - radius) / curr_nvp )
                    bot_left_h = max(bot_left_h, 0)
                    #print(i, j, radius, bot_left_h, k, data[0][k])
                    #print(i, j, box)
                #print(bot_left_h)
                if bot_left_h > p_height:
                    img = draw_person(img, scale, box, index, 0)
                    num_people += 1
                else:
                    #if the box's x value is positive, check whether or not the value is in the nophi list. this only applies to values less than 90 degress (right degrees) due to the order in which boxes are tested
                    if bot_left <= 90:
                        no_phi.append(int(bot_left))
                    #print("lower")
                    #img = draw_person(img, scale, box, index, 1)
            else:
                pass
                #img = draw_person(img, scale, box, index, 2)
            #z_height = calc_height(a, data[0][k:l], data[1][k:l], box)

    #add legend
    drawing = ImageDraw.Draw(img)
    drawing.rectangle( (0, .65 * img.height - 8 * s, img.width, .65 * img.height + 10 * s), fill = "white")
    font = ImageFont.truetype("blindspotapp/static/car_images/arial.ttf", int(5 * s) )
    if num_people == 1:
        vru_names = ["preschool child", "elementary school child", "elementary school child on a bicycle", "adult in a wheelchair", "adult on a bicycle", "adult"]
    else:
        vru_names = ["preschool children", "elementary school children", "elementary school children on bicycles", "adults in wheelchairs", "adults on bicycles", "adults"]
    drawing.text( (img.width * .35, .65 * img.height - 5 * s), str(num_people) + " " + vru_names[index] + " in blind zone", font = font, fill = "black" )


    legend_x = img.width - 40 * s
    drawing.rectangle( (legend_x, 2 * s, legend_x + 25 * s, 14 * s), fill = "white" )

    lab_h_delta = 6 * s

    legend_y = 0

    drawing.ellipse( (legend_x + 3 *s, legend_y , legend_x + 7 * s, legend_y  + 4 * s), fill = "white",outline = "black")
    drawing.text( (legend_x + 8 * s, legend_y - 1 * s), "VRU", font = font, fill = "black")

    legend_y += lab_h_delta

    drawing.rectangle( (legend_x + 3 *s, legend_y, legend_x + 7 * s, legend_y  + 4 * s), fill = "#00ff00")
    drawing.text( (legend_x + 8 * s, legend_y - 1 * s), "Visible Zone", font = font, fill = "black")

    legend_y += lab_h_delta

    drawing.rectangle( (legend_x + 3 *s, legend_y, legend_x + 7 * s, legend_y  + 4 * s), fill = "#111111")
    drawing.text( (legend_x + 8 * s, legend_y - 1 * s), "Blind Zone", font = font, fill = "black")

    legend_y += lab_h_delta

    drawing.rectangle( (legend_x + 3 *s, legend_y, legend_x + 7 * s, legend_y  + 4 * s), fill = "#888888")
    drawing.text( (legend_x + 8 * s, legend_y - 1 * s), "Unmeasured", font = font, fill = "black")

    fig.add_layout_image(dict(
        source=img,
        xref="paper",
        yref="paper",
        x = .5,
        y = .5,
        sizex = 1, sizey = 1,
        xanchor="center", yanchor="middle",
        layer="above")
    )

    return img
# add vrus to the side views
def add_VRU_side(data, hood_width, s, index, mode, img):
    #mode 0 is front view, mode 1 is side view
    if mode == 0:
        if len(data) == 3:
            (a, c, d) = data
        else:
            (a, c, d, nvp) = data
        w_o = 12 * s
        children = int( find_number_in_blind_zone(a, c, d, index) )
    else:
        w_o = 4 * s
        (a, b, nvp) = data
        children = int( find_number_in_blind_zone(a, nvp, hood_width * .75 / s, index) )

    print(children)
    img = draw_children(img, w_o+ hood_width, children, s, index)

    return img, children
#find the number of VRUS in the blind zone - used by all 3. this is legacy code copied more or less from blindspotcalc
def find_number_in_blind_zone(a,c,d, index = 0):
    height = people[index][0]
    width = people[index][1]
    count = ((c-d-(height*c/a))/width)
    if count <0:
        count = 0
    return count
#draw VRUS for side view
def draw_children(img, start_width, children,  s = 10, index = 0):


    drawing = ImageDraw.Draw(img)

    person_height = people[index][2] * s;
    person_width = people[index][1] * s;

    draw_height = int( img.height - person_height)
    draw_width = int( start_width )

    if index == 0:
        person = Image.open("blindspotapp/static/car_images/people/preschool.png").convert("RGBA")
    elif index == 1:
        person = Image.open("blindspotapp/static/car_images/people/gradeschool.png").convert("RGBA")
    elif index == 2:
        person = Image.open("blindspotapp/static/car_images/people/childbicycle.png").convert("RGBA")
    elif index == 3:
        person = Image.open("blindspotapp/static/car_images/people/wheelchair.png").convert("RGBA")
    elif index == 4:
        person = Image.open("blindspotapp/static/car_images/people/bicycle.png").convert("RGBA")
    elif index == 5:
        person = Image.open("blindspotapp/static/car_images/people/adult.png").convert("RGBA")
    person = person.convert("RGBA")
    person = person.resize( ( person_width, person_height ))

    #index will always be less than 6, what is in the else statement is legacy for this one image of "distance away from the furthest vru, and also only show the furthest vru"
    if index < 6:
        for i in range(0, int(children)):
            #drawing.rectangle( [draw_width, draw_height, draw_width + person_width, img.height], outline = "black", fill = "orange", width = 20)
            if draw_width < img.width:
                img.paste(person, (draw_width, draw_height), person)
                draw_width += person_width
            else:
                break
    """
    else:
        for i in range(0, int(children - 1)):
            #drawing.rectangle( [draw_width, draw_height, draw_width + person_width, img.height], outline = "black", fill = "orange", width = 20)
            #img.paste(person, (draw_width, draw_height), person)
            draw_width += person_width
        img.paste(person, (draw_width, draw_height), person)
    """
    """
    drawing = ImageDraw.Draw(img)
    font = ImageFont.truetype("blindspotapp/static/car_images/arial.ttf", int(10 * s) )
    if children == 1:
        drawing.text( (000, 000), str(children) + " VRU in blind zone", font = font, fill = "black" )
    else:
        drawing.text( (000, 000), str(children) + " VRUs in blind zone", font = font, fill = "black" )
    """
    return img
#draw for overhead
def draw_person(img, scale, box, index, higher):
    origin = (img.width // 2, img.height // 2)
    drawing = ImageDraw.Draw(img, "RGBA")


    for i in range(len(box) ):
        box[i] = box[i] * scale

    coords = [ box[0] + origin[0] + 1, origin[1] - box[3] + 1 , box[2] + origin[0] - 1, origin[1] - box[1] - 1 ]
    #print(coords)

    drawing = ImageDraw.Draw(img)

    if higher == 0:
        drawing.ellipse( coords, fill = "white" )
    elif higher == 1:
        drawing.ellipse( coords, fill = "green" )

    else:
        pass
        #drawing.ellipse( coords, fill = "purple" )

    return img

#front view vin specific functions

# get the car image and the appriopriate values relating to it
def get_car_img(model_type):
    #might be possible to put in external text file if you're not worried about it changing too often
    response = requests.get("https://vpic.nhtsa.dot.gov/api/vehicles/getVehicleVariableValuesList/Body%20Class?format=json")
    data = json.loads(response.text)
    body_id = 7;
    for bodyclass in data['Results']:
        #print(bodyclass)
        if bodyclass['Name'] == model_type:
            body_id = bodyclass['Id']
            break
    if body_id == 64:
        body_id = 66
    try:
        img = Image.open("blindspotapp/static/car_images/stock_photos/" + str(body_id) + ".png")
        #print(body_id)
        # car id ( driver width, driver height, hood width, window height)
        #all meausrements are from the bottom left hand corner
        driver_placements = [ (1, (210, 140, 355, 110) ), (2, (265, 135, 405, 110) ), (3, (310, 145, 380, 115)), (5, (200, 150, 375, 125)), (7, (260, 145, 366, 116)), (8, (240, 155, 375, 130)), (9, (315, 150, 430, 125)), (10, (220, 150, 380, 120)), (11, (355, 135, 415, 125)), (13, (260, 135, 380, 110)),(15, (255, 130, 385, 110)), (16, (450, 110, 485, 85)), (60, (285, 150, 400, 130)), (62, (350, 140, 415, 125)), (63, (350, 130, 415, 125)), (66, (355, 140, 415, 125)), (68, (445, 85, 500, 60)), (73, (435, 105, 500, 100)), (74, (353, 140, 415, 125)), (95, (310, 155, 430, 125)) ]

        for tup in driver_placements:
            if tup[0] == body_id:
                car_img_info = tup[1]
                break
        return (img, car_img_info)
    except:
        return None
# get the amount of pixels by which the hood must be decreased for the sight line to not intersect with the hood
def get_hood_scaling( img, to_hood, a, c, s):
    a = a * s
    c = c * s
    m = float(-1 * a) / c
    b = a

    #we want to limit the pixels that we iterate over. the -20 for the end_x is to account for the padding in front of each car and the bumper
    start_x = round(to_hood)
    end_x = img.width - 20
    #img.convert(mode = "RGB").save("hood.jpg")

    max_y = 0
    max_diff = -1 * img.height
    min_diff = img.height
    min_y = 0
    for x in range(start_x, end_x):
        #for each pixel on the line, find the y-coord of the pixel
        y = int(m * x + b)
        orig_y = y
        diff = 0

        r, g, bl, a = img.getpixel( (x,  img.height - y) )

        # if the original pixel lands on a solid car pixel, you need to find how many pixels is there until you get to the top of the hood (from below)
        if a > 254:
            while a > 128:
                diff += 1
                y += 1
                r, g, bl, a = img.getpixel( (x, img.height - y ) )
            if diff > max_diff:
                #print (x, diff)
                max_y = orig_y
                max_diff = diff
        #if the original pixel lands on a transparent car pixel, you need to find how many pixels are there until you get to the top of the hood (from above)
        else:
            while a < 250:
                diff += 1
                y -= 1
                r, g, bl, a = img.getpixel( (x, img.height - y ) )
            if diff < min_diff:
                #print (x, diff)
                min_y = orig_y
                min_diff = diff

    #if all pixels tested were above the hood, we need to scale the hood up, so return the min_diff. if not, the hood needs to be scaled up
    if max_diff ==  -1 * img.height:
        #print( -1 * min_diff, min_y)
        return -1 * min_diff, min_y
    return max_diff, max_y

#get the stock image for the side view image
def get_car_side_img( a):
    #driver width, driver height, pixels to side of car, pixels from driver to top of window, pixels from driver to bottom of window
    if a < 70:
        img = Image.open( "blindspotapp/static/car_images/car_front.png")
        tup = (540, 1050, 110, 150, 160)
    else:
        img = Image.open("blindspotapp/static/car_images/truck_front.png")
        tup = (420, 1080, 132, 220, 230)

    return img, tup

#main image creation

# start image for side views
def start_image(a, s = 1):
    w_o = 12 * s
    height = ( 180 + 8 ) * s
    h = height
    width = 364 * s + w_o

    img = Image.open("blindspotapp/static/car_images/sky.jpg")
    img = img.resize( (width, height) )
    #img = img.convert("RGBA")

    #based on actual research - this block of code is repeated in multiple places - may make its own function
    tire_rad = int( 14) #14 is around the radius of most passenger car tires
    if a > 70:
        tire_rad = int( 21 ) #21 is around the radius of most truck tires
    elif a > 180:
        tire_rad = int( 74) #this is around the radius of most mining truck tires
    tire_rad *= s

    #draw the road height based off the tire radius
    drawing = ImageDraw.Draw(img, "RGBA")
    drawing.rectangle( [0, h - 1.5 * tire_rad , width, h], fill = (66,66,66))
    return img
# main image creation for front view no vin - not used anymore, but here for legacy
def create_image_front(data, s = 1):
    (a, c, d) = data
    car_color = "white"
    w_o = 12 * s #width_offset - the distance from the left edge to the driver point

    if a > 180:
        s = int( s * 180 / a ) #if the truck is too big, lower the scale

    tire_rad = int( 14) #14 is around the radius of most passenger car tires
    if a > 70:
        tire_rad = int( 21 ) #21 is around the radius of most truck tires
    elif a > 180:
        tire_rad = int( 74) #this is around the radius of most mining truck tires
    tire_rad *= s

    hood_width = int(d * s)

    img = start_image(a, s)
    h = img.height
    width = img.width

    dh_pixels = int(a * s)
    one_segment = s * (a - tire_rad / s) / 5
    dh_top = min( dh_pixels + one_segment, h * 180 / 188)
    dh_bot = dh_pixels - one_segment

    hood_width = int(d * s)
    l_w = s
    if get_ws_width(a * s, c * s, dh_bot* s) < hood_width :
        dh_bot = get_hood_height(a * s, c* s, d* s)


    hood_height = get_hood_height(a* s, c* s, d* s)
    drawing = ImageDraw.Draw(img, "RGBA")
    #windshield + hood
    if d <= 48: #windshield reaches to the end of the hood, box style

        ws_width = hood_width
        ws_horiz  = int (ws_width / 1.5) + w_o
        ws_width += w_o

        #top part
        drawing.line( [ (0, h - dh_top) ,  (w_o, h - dh_top) ], fill = car_color, width = 2 * s)
        drawing.line( [(w_o, h - dh_top), (ws_horiz, h -  dh_top ),], fill = car_color, width = 2 * s)
        #actual window
        drawing.line( [ (ws_horiz, h - dh_top), (ws_horiz, h - dh_top), (ws_width, h - dh_bot), (ws_width, h - dh_bot)], fill = car_color, width = 2 * s)

        #no need for hood
    else : #vehicles with a hood
        hood_height = get_hood_height(a* s, c* s, d* s)
        hood_height = min(hood_height, dh_bot)
        if a > 70: #truck with hood - draw windshield box style
            ws_width = int(hood_width / 2)
            ws_horiz = int(ws_width / 2) + w_o
            ws_width += w_o
            #top part
            drawing.polygon( [ (0, h - dh_top - l_w), (0, h - dh_top + l_w), (w_o, h - dh_top + l_w), (w_o, h - dh_top - l_w) ], fill = car_color)
            drawing.polygon( [(w_o, h - dh_top + l_w), (w_o, h - dh_top - l_w), (ws_horiz, h - dh_top - l_w), (ws_horiz, h - dh_top + l_w)], fill = car_color)
            #actual window
            drawing.line( [ (ws_horiz, h - dh_top), (ws_width, h - dh_bot)], fill = car_color, width = 2 * l_w)

            # get the point where the sight line intersects with the windshield
            win_inter = get_line_intersection(a* s, c* s, ws_horiz, dh_top, ws_width, dh_bot)
            hood_arc_start = win_inter[1]

            end_degree = 360
            average = (hood_arc_start + hood_height) / 2
            hood_arc_start = average + (hood_arc_start - average) / 2
            hood_height = average - (average - hood_height) / 2
            test_values = get_arc_intersection(a* s, c* s,  win_inter[0], hood_arc_start, hood_width,hood_height, 1)


        else:
            #normal car



            ws_width = int(hood_width / 2)
            ws_horiz = int (ws_width / 6) + w_o
            ws_width += w_o
            drawing.arc( arc_box(0 , h - dh_top, ws_width, h - dh_bot), 270, 360,fill = car_color, width = 2* s)

            # get the point where the sight line intersects with the windshield
            win_inter = get_arc_intersection(a* s, c* s, -.5 * ws_width, dh_top, ws_width - w_o, dh_bot)
            hood_arc_start = win_inter[1]

            end_degree = 360

            #the arc will interesct with the sight line, so get the shift needed so that the arc is tangent to the sight line
            test_values = get_arc_intersection(a* s, c* s,  win_inter[0], hood_arc_start, hood_width,hood_height, 1)

            #fill in
            drawing.polygon( [ (ws_width,  dh_bot), (ws_width,hood_height), (w_o + hood_width, hood_height)], fill = car_color);
        y_shift = get_arc_shift(a* s, c* s, win_inter[0], hood_arc_start, hood_width,hood_height, test_values)

        hood_arc_start = int (hood_arc_start - y_shift)
        hood_arc_end = int( hood_height - y_shift )

        #arced hood
        drawing.pieslice( arc_box( win_inter[0] + w_o, h - hood_arc_start, w_o + hood_width, h - hood_arc_end ), 270, end_degree, fill = car_color, width = win_inter[1])
        #fill in to the left of the arc
        drawing.rectangle( [0, h - hood_arc_start, win_inter[0] + w_o, h - hood_arc_end], fill = car_color )
        #fill in under the arc
        drawing.rectangle( [w_o, h - hood_arc_end, w_o + hood_width, h - tire_rad ], fill = car_color);

    #car body
    drawing.rectangle( [0, h - dh_bot, ws_width, h - tire_rad], fill = car_color)



    #tire
    if a > 70: #truck
        tire_x = hood_width + w_o - 1.25 *  tire_rad #the CENTER of the tire
    else:
        tire_x = min( int( (w_o + hood_width) - (1.5 * tire_rad)) , w_o + ws_width)
    tire = Image.open("blindspotapp/static/car_images/tire.png");
    tire = tire.resize( (int(tire_rad * 2), int( tire_rad * 2)) );
    img.paste( tire, [ int( tire_x - tire_rad),int( h - 2 * tire_rad)], tire)

    img = add_final_elements(data, s, 0, img)

    return (img, hood_width)
# main image creation for front view no vin
def create_new_image_front(data, s = 1):
    (a, c, d) = data
    img = start_image(a, s)


    # we assume the body type of the car based off the driver height. of course, this is not complete nor 100% accurate, but it seems to work, based off the airtable
    # in the future, this could be improved by adding in the d measurement as well
    if a < 60:
        car_img_data = get_car_img("Sedan\/Saloon")
    elif a < 70:
        car_img_data = get_car_img("Sport Utility Vehicle (SUV)\/Multi-Purpose Vehicle (MPV)")
    else:
        car_img_data = get_car_img("Incomplete - Cutaway")

    img, hood_width = create_front_combined(data, s, img, car_img_data)


    return (img,hood_width )

# initial image creation for front view with vin
def create_image_vin( data, s = 1, vin = "WBA8A9C55GK616123"):
    (a, c, d, vin) = data
    img = start_image(a, s)
    height = img.height
    width = img.width
    w_o = 12 * s

    # get the proper image - api call
    response = requests.get("https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValues/" + vin + "?format=json");
    try:
        json_data = json.loads(response.text)
        car_img_data = get_car_img(json_data['Results'][0]['BodyClass'])

        img, hood_width = create_front_combined(data, s, img, car_img_data)
        return img, hood_width
    except:
        return None, None

#do the car scaling for the front view for vin and no vin
def create_front_combined(data, s, img, car_img_data) :
    #unpack the data passed in
    if len(data) == 4:

        (a, c, d, vin) = data
    else:
        (a, c, d) = data
    w_o = 12 * s #width_offset - distance from the left end of the image to the driver point
    car_img = car_img_data[0]
    d_width = car_img_data[1][0]
    d_height = car_img_data[1][1]
    to_hood = car_img_data[1][2]
    to_window = car_img_data[1][3]

    dh_pixels = int( a * s ) #driver_height
    hood_width = int( d * s )

    #do an initial scaling based off getting the driver position to be okay

    img_w = int( -d * s * car_img.width / (d_width - car_img.width) )
    img_h = int( a * s * car_img.height / d_height )

    w_scale = img_w / car_img.width
    h_scale = img_h / car_img.height
    car_img = car_img.resize( (img_w, img_h) )

    #now, the car is lined up with the a and c points. however, we need to manually adjust the vertical scaling of the car body and of the window so that the lines don't intersect.

    hood = car_img.crop( ( d_width * w_scale, car_img.height - d_height * h_scale, car_img.width, car_img.height )  )
    max_diff, max_y = get_hood_scaling( hood, (to_hood - d_width) * w_scale, a, c,s)
    #print(max_diff, max_y)
    if max_y + max_diff == 0:
        hood_y_scale = 1
    else:
        hood_y_scale = (max_y ) / (max_y + max_diff)
    hood = car_img.crop((0, car_img.height - to_window * h_scale, car_img.width, car_img.height))
    hood = hood.resize( (hood.width, int(hood_y_scale * hood.height) ) )
    img.paste(hood, (-1 * int(img_w - (w_o + d * s)), img.height - hood.height), hood)

    #now that the hood is pasted, move onto the lower window - hood to driver point
    window = car_img.crop( (0,  car_img.height - dh_pixels, car_img.width, car_img.height - to_window * h_scale) )
    if window.height + max_diff > 0:
        #now that the hood is pasted, move onto the lower window - hood to driver point
        #wh_scale = (max_diff + old_diff) / old_diff
        window = window.resize( (window.width, window.height + max_diff) )
    img.paste( window, (-1 * int(img_w - (w_o + d * s)), img.height - hood.height - window.height), window)

    #now, do the very top of the car, which is not scaled further
    ceil = car_img.crop( (0, 0, car_img.width, car_img.height - dh_pixels) )
    img.paste(ceil, ( -1 * int(img_w - (w_o + d * s)), img.height - hood.height - window.height - ceil.height), ceil)

    img = add_final_elements(data, s, 0, img)

    return (img,hood_width )

# main image creation for side view
def create_image_side(data, s = 1):
    #this image is drawn with the car on the left and then flipped, for convenience

    (a, b, nvp) = data
    car_color = "red"


    c_o = 4 * s #car_offset - the distance from the left edge to the car point

    if a > 180:
        s = round( s * 180 / a ) #if the truck is too big, lower the scale

    #get the tire radius again
    tire_rad =  14 #14 is around the radius of most passenger car tires
    tire_width = 10
    if a > 70:
        tire_rad = 21  #21 is around the radius of most truck tires
        tire_width = 15
        car_color = "white"
    elif a > 180:
        tire_rad = 74 #this is around the radius of most mining truck tires
        tire_width = 24
        car_color = "white"
    tire_rad *= s
    tire_width *= s

    img = start_image(a, s)
    h = img.height
    w = img.width

    dh_pixels = int(a * s)
    one_segment = s * (a - tire_rad / s) / 5

    dh_top = min( dh_pixels + one_segment, h * 180 / 188)

    #draw the windshield based off the type of car
    drawing = ImageDraw.Draw(img, "RGBA")
    if a < 70: #car - slanted cab
        #get the x and y values where a slanted line (side window) intersects the sight line
       (dh_x, dh_bot) = get_window_height(a, b, nvp, s, dh_top / s)

       #get the length of the entire car
       car_len =  round( dh_x * 4 / 3)
       #top of car
       drawing.line( [int( c_o + car_len / 8), h-  dh_top, int( c_o + 7 * car_len / 8), h- dh_top], fill = car_color, width = 2 * s )
       #driver side a-pillar
       drawing.line( [ c_o + s, h - dh_bot, c_o + car_len / 8, h-dh_top], fill = car_color, width = 2 * s )
       #passenger side a-pillar
       drawing.line( [ c_o + car_len - s, h-dh_bot, round(c_o + 7 * car_len/ 8), h-dh_top], fill = car_color, width = 2 * s )

    else: #truck - straight cab
       #get the y value where the sight line intersects with the bottom of the passenger side window
       dh_bot = get_hood_height(a * s, nvp* s, b* s)
       car_len = 4 * b * s / 3
       drawing.line( [int( c_o), h-  dh_top, int( c_o + car_len), h- dh_top], fill = car_color, width = 2 * s )
       drawing.line( [ c_o + s, h - dh_bot, c_o + s, h-dh_top], fill = car_color, width = 2 * s )
       drawing.line( [ c_o + car_len - s, h-dh_bot, c_o + car_len - s, h-dh_top], fill = car_color, width = 2 * s )

    w_o = car_len / 4

    #car body
    drawing.rectangle( [ c_o, h - dh_bot, c_o + car_len, h - tire_rad], fill = car_color)

    # tire stuff
    drawing.rectangle( [c_o, h-tire_rad, c_o + tire_width, h], fill = "black")
    drawing.rectangle( [c_o + car_len - tire_width, h-tire_rad, c_o + car_len, h], fill = "black")

    #upper part of the vision zone - while we have the one_segment
    slope,intercept = get_line(0, dh_pixels, car_len * 5 /8 , dh_top)
    x_start = int(c_o + w_o)

    extra_height = int( slope * nvp * s )
    drawing.polygon( [ (x_start, int( h- dh_pixels)), (x_start + nvp * s, int( h- dh_pixels)), (x_start + nvp * s, h - extra_height - dh_pixels)], fill = (0, 255, 0,255))

    if nvp < 180 + car_len * .75:   #fill in the rest of the box if needed
        start_x = int(c_o + w_o + nvp * s)
        start_y = int( h - extra_height - dh_pixels)
        width_x = int ((180 + car_len * .375 - nvp) * s)
        width_y = extra_height
        drawing.rectangle( (start_x, start_y, start_x + width_x, start_y + extra_height), fill = (0, 255, 0,255) )

    img = add_side_details( a, car_len, dh_bot, s, img)
    img = add_final_elements((data[0], data[2], data[1], car_len), s, 1, img)


    return (img, car_len)
# side view stuff, but with stock car images. unused for now
def create_image_side_new(data, s = 1):
    (a, b, nvp) = data

    c_o = 4 * s #car_offset - the distance from the left edge to the car point

    if a > 180:
        s = round( s * 180 / a ) #if the truck is too big, lower the scale

    img = start_image(a, s)
    h = img.height
    w = img.width

    car_img, driver = get_car_side_img(a)

    dh_pixels = int(a * s)


    dh_img_top = driver[1] + driver[3]
    dh_img_bot = driver[1] - driver[4]


    #a bunch of weird math - do an initial resize to get the width correct
    #rn this is just to the side of the car, which is not entirely accurate for the card image due to the way it's drawn. to improve this, a new parameter should be given to improve the scaling
    new_car_scale = b * s / (car_img.width - driver[0] - driver[2])
    car_img = car_img.resize( (int(car_img.width * new_car_scale), car_img.height) )

    #for the height, split up the car image in 3 parts
    car_ceiling = car_img.crop( (0, 0, car_img.width, car_img.height - driver[1] ) )
    windshield = car_img.crop( (0, car_img.height - driver[1], car_img.width, (car_img.height - driver[1]) + driver[4]) )
    body = car_img.crop( (0, (car_img.height - driver[1]) + driver[4], car_img.width, car_img.height) )

    car_length = b * s * (car_img.width - driver[2] ) / (car_img.width - 2 * driver[2] )

    #scale the body so that it is tangent to the sight line
    drawing = ImageDraw.Draw(img, "RGBA")
    if a < 70: #car - slanted cab
       (dh_x, dh_bot) = get_window_height(a, b, nvp, s, dh_img_top / s)
       diff = body.height - dh_bot
       body = body.resize( (body.width, int(dh_bot)) )

    else: #truck - straight cab
       dh_bot = get_hood_height(a * s, nvp* s, b* s)
       diff = body.height - dh_bot
       body = body.resize( (body.width, dh_bot) )
    diff = diff - windshield.height
    #print(diff)
    diff2 = windshield.height + diff / windshield.height
    #windshield = windshield.resize( (windshield.width, int(windshield.height + diff)) )
    windshield = windshield.resize( (windshield.width, int(dh_pixels - body.height)) )

    car_ceiling = car_ceiling.resize( (car_ceiling.width, int(car_ceiling.height * new_car_scale) ) )

    shift_x = c_o - int( new_car_scale * driver[2] )

    img.paste( body, (shift_x, h - body.height), body )
    img.paste( windshield, (shift_x, h - dh_pixels), windshield )
    img.paste( car_ceiling, (shift_x, h - dh_pixels - car_ceiling.height), car_ceiling)


    car_len = body.width - 2 * new_car_scale * driver[2]


    w_o = int(driver[0] * new_car_scale) + shift_x
    #print(w_o)
    dh_top = dh_pixels + int( driver[3] * new_car_scale )
    #upper part of the vision zone - while we have the one_segment
    slope,intercept = get_line(0, dh_pixels, car_len * 5 /8 , dh_top)

    x_start = int(c_o + w_o)

    extra_height = int( slope * nvp * s )
    drawing.polygon( [ (w_o, int( h- dh_pixels)), (w_o + nvp * s, int( h- dh_pixels)), (w_o + nvp * s, h - extra_height - dh_pixels)], fill = (0, 255, 0,255))

    if nvp < 180 + car_len * .75:   #fill in the rest of the box
        start_x = int(w_o + nvp * s)
        start_y = int( h - extra_height - dh_pixels)
        width_x = int ((180 + car_len * .375 - nvp) * s)
        width_y = extra_height
        drawing.rectangle( (start_x, start_y, start_x + width_x, start_y + extra_height), fill = (0, 255, 0,255) )

    #img.paste( car_img, ( c_o - int( new_car_scale * driver[2]), h - car_img.height), car_img )

    drawing = ImageDraw.Draw(img, "RGBA")
    nvp = int(nvp * s)
    p_r = int(1.5 * s);
    #sight line
    drawing.line( [w_o , h - dh_pixels , nvp+ w_o, h], fill = "green", width = p_r)
    #driver point
    drawing.ellipse([w_o - p_r, h - dh_pixels - p_r  , w_o + p_r, h - dh_pixels + p_r ] , fill =  "orange")
    #c point
    drawing.ellipse([nvp+ w_o - p_r, h - p_r , nvp + w_o + p_r, h + p_r] , fill =  "orange")

    car_end = car_img.width - new_car_scale * driver[2] - shift_x
    img = add_final_elements((data[0], data[2], data[1], (car_end, w_o)), s, 1, img)
    #img = add_side_details( a, car_len, dh_bot, s, img)

    #hood_width (from driver to end of car), w_o (from image to driver)
    return (img, (car_end - w_o, w_o) )

# extra stuff drawing for front and side views
def add_final_elements(data, s, mode, img):
    #mode 0 is for front view, mode 1 is for side view
    #unpack data
    if mode == 0:
        if len(data) == 3:
            (a, c, d) = data
        else:
            (a, c, d, nvp) = data
        w_o = 12 * s
        hood_width = int(d * s)
    else:
        (a, c, d, car_len) = data
        c_o = int(4 * s)
        c = int(c)
        w_o = int(car_len // 4) + c_o
        hood_width = int(car_len * .75)

    c = int(round(c * s, 0))
    drawing = ImageDraw.Draw(img, "RGBA")

    h = img.height
    width = img.width
    dh_pixels = int(a * s)


    #fields of view
    intersect_y = get_hood_height(a* s, c, hood_width) #y intersect of the sight line into the area of interest
    #draw the visible zone area
    #for the front view, make the triangle go above and below the driver. for the side view, only do below the driver because above the driver has been done.
    if mode == 0:
        drawing.polygon( [ (w_o, h - dh_pixels), (w_o + c, h), (w_o + c, h - (2 * dh_pixels) ) ], fill =  (0, 255, 0,255) )
        start_x = hood_width + w_o

    else:
        drawing.polygon( [ (w_o, h - dh_pixels), (w_o + c, h), (w_o + c, h - dh_pixels)  ], fill =  (0, 255, 0,255) )
        start_x = int(car_len + c_o)
    #draw the blind zone
    drawing.polygon( [(start_x, h-intersect_y), (start_x, h), (start_x + c - hood_width, h) ], fill =  (0, 0, 0,255) )

    #if the pure triangles will not fill the area of interest, fill the rest of it with a green box
    if c < 180 * s + hood_width :
        diff =  int ( (180 - c / s) * s + hood_width )
        if mode == 0:
            drawing.rectangle( ( c + w_o, h - 2 * dh_pixels, c + w_o + diff, h), fill = (0, 255, 0,255) )
        else:
            drawing.rectangle( ( c + w_o, h - dh_pixels, c + w_o + diff, h), fill = (0, 255, 0,255) )

    p_r = int(1.5 * s);
    #sight line
    drawing.line( [w_o , h - dh_pixels , c+ w_o, h], fill = "green", width = p_r)
    #driver point
    drawing.ellipse([w_o - p_r, h - dh_pixels - p_r  , w_o + p_r, h - dh_pixels + p_r ] , fill =  "orange")
    #c point
    drawing.ellipse([c+ w_o - p_r, h - p_r , c + w_o + p_r, h + p_r] , fill =  "orange")

    return img
# more extra stuff drawing for side view
def add_side_details( a, car_len, dh_bot, s, img):
    #this basically draws the stuff on the front of the car
    drawing = ImageDraw.Draw(img)

    tire_rad =  14 #14 is around the radius of most passenger car tires
    tire_width = 10

    car_color = "red"
    light_color = "white"

    height = img.height

    if a > 70:
        tire_rad = 21  #21 is around the radius of most truck tires
        tire_width = 15
        car_color = "white"
        light_color = "yellow"
    elif a > 180:
        tire_rad = 74 #this is around the radius of most mining truck tires
        tire_width = 24
        car_color = "white"
        light_color = "yellow"
    tire_rad *= s
    tire_width *= s

    c_o = 4 * s

    mid_car = c_o + car_len // 2
    car_h = (dh_bot - tire_rad)


    #bumper - depends on driver height, huh
    if a < 70:
        #c_o off the ground, centered in the middle, total length of .5 car_len
        b_w2 = car_len // 2.75
        b_w1 = car_len // 2.5
        b_h = car_h // 7
        b_o = int(2 * s)

        b_top = b_o + tire_rad + b_h

        drawing.polygon( [ (mid_car - b_w1, height - b_top), (mid_car + b_w1,height - b_top),(mid_car + b_w2, height -( b_o + tire_rad)), (mid_car - b_w2, height -( b_o + tire_rad))], fill = "black")

        tb_top = b_top + b_o + b_h
        tb_bot = b_top + b_o

        #drawing.polygon( [ (mid_car - b_w2, height - tb_top), (mid_car + b_w2, height - tb_top), (mid_car + b_w1, height - tb_bot), (mid_car - b_w1, height - tb_bot)], fill = "black")

    else:
        b_w = car_len // 3
        b_h = car_h // 2.5
        drawing.rectangle( [ mid_car - b_w, img.height - (c_o + tire_rad + b_h), mid_car + b_w, img.height - ( c_o + tire_rad)], fill = "gray")

    #headlights

    hl_height = (dh_bot - tire_rad) // 6
    hl_width = 1.5 * tire_width

    hl_y = (tire_rad + dh_bot)/2
    drawing.rectangle( (c_o + 2 *s, img.height - (hl_y + hl_height) , c_o + 2 * s + hl_width, img.height - (hl_y) ), fill = light_color)

    drawing.rectangle( (c_o + car_len - 2*s - hl_width, img.height - (hl_y + hl_height) , c_o + car_len - 2 *s, img.height - (hl_y) ), fill = light_color)


    #license place
    lp_width = 6 * s
    lp_y = 6 * s

    drawing.rectangle( ( mid_car - lp_width, img.height - ( lp_y + tire_rad), mid_car + lp_width,  img.height - tire_rad), fill = "white", outline = "black", width = s)

    #sideview mirrors
    if a < 70:
        drawing.rectangle( [car_len + s, img.height - (dh_bot + tire_rad //2 ), car_len +s + tire_width, img.height - dh_bot ], fill = car_color )
        drawing.rectangle( [0, img.height - (dh_bot + tire_rad //2 ), c_o + s, img.height - dh_bot ], fill = car_color )

    return img
# crop image for side views so that the image ends after the area of interest
def crop_image(a, car_len, mode, s, img):
    (w, h) = (img.width, img.height)
    dh_pixels = int(a * s)

    if mode == 0:
        w_o = 12 * s
    else:
        w_o = 4 * s

    w_scale =  (dh_pixels + 12 * s) / h
    h_scale =  (w_o + car_len + 181 * s) / w
    scaling = max(w_scale, h_scale)
    img = img.crop( (0, h - int(h * scaling), scaling * w , h) )
    img = img.resize( ( 400 * s, 200 * s ) )

    return img
#create polar chart using plotly
def create_polar(data, s):
    labels = ['A Pillar Blindzone', 'A Pillar Blindzone', 'Side View', 'Front View']
    radius = data[1]
    # theta corresponds to the angle of the center of each slice
    theta = data[0]
    #width = [1] * data[2] + [2] * (len(data[1]) -  data[2])
    colors = ['#111111'] * data[2] + ['#888888'] * (len(data[1]) -  data[2])

    #make the tick values. we don't know how big the blindzones are gonna be, so let's draw 8 of them, guaranteed
    max_val = max(data[1])
    tick_vals = []
    tick_text = []
    tick_inc = round( max_val / 8 )
    for i in range( 8 ):
        tick_vals.append( int(tick_inc  * i) )
        tick_text.append( str(int(tick_inc  * i / 12)) + " ft." )


    layout_options = {
                  "plot_bgcolor": "rgba(255, 255, 255, 255)",
                  "showlegend": False,
                  "xaxis_visible": False,
                  "yaxis_visible": False,
                  "polar_bgcolor": "rgba(0, 255, 0, 255)",
                  "polar_radialaxis_showticklabels": True,
                  "polar_radialaxis_ticksuffix": " ft.",
                  "polar_radialaxis_range": [0, max(radius)],
                  "polar_radialaxis_tickvals" : tick_vals,
                  "polar_radialaxis_ticktext" : tick_text,
                  "polar_radialaxis_tickfont_size" : 5 * s,
                  "polar_radialaxis_tickfont_color" : "#ff0000" ,
                  "polar_radialaxis_showline" : False,
                  "polar_radialaxis_tickangle" : -90,
                  "polar_angularaxis_ticks": "",
                  "polar_angularaxis_showticklabels": True,
                  "polar_angularaxis_tickfont_size" : 5 * s,
                  "width" : 200 * s,
                  "height" : 200 * s,
                  "margin": { "l":10 * s, "b":10 * s, "t":10 * s, "r":10 * s }
                  }

    #barpolar_plots = [go.Barpolar(r=[r], theta=[t], width=[w], marker_color=[c], marker_line_width = 0) for r, t, w, c in zip(radius, theta, width, colors)]
    barpolar_plots = [go.Barpolar(r=[r], theta=[t], width=[2], marker_color=[c], marker_line_width = 0) for r, t, c in zip(radius, theta, colors)]
    fig = go.Figure(barpolar_plots)

    fig.update_layout(**layout_options)
    #fig.show()

    return fig
#add in car/ truck
def create_image_top(fig, bd, s):
    #this is the image that our car image will be pasted on. the size is matches that of the figure because it makes it easier for the image to be added to the figure later
    #it is completely white with complete transparency so that it doesn't look weird when pasted on
    img = Image.new("RGBA", (200 * s, 200 *s), (255, 255, 255, 0))
    #graphImg = Image.open(BytesIO(img_bytes)).convert("RGBA")

    #the x,y are the x and y pixel coordinates of where i think a driver's head would be on the image. x and y are from the lower left hand corner
    #right now, there are only two images: for a sports car and a truck. in the future, different overhead images can be added (perhaps, like the front view no vin, 3 pictures for < 60, 60 <= x < 70, > 70
    #of course, the vin could always be used to get a specific body type, but i'm not sure if that's really necessary
    if bd[3] > 70:
        carImg = Image.open("blindspotapp/static/car_images/truck.png")
        x,y = 30, 110
    else:
        carImg = Image.open("blindspotapp/static/car_images/car.png")
        x,y = 110, 325

    scale = 90 * s / bd[2] #pixels per inch. the 90 comes from width // 2 - margin, as defined in create_polar above
    #print("local scale" + str(scale))
    new_width = int(carImg.width * bd[0]* scale / (carImg.width - x))
    new_height = int(bd[1] * scale * carImg.height / y)
    w_scale = new_width / carImg.width
    h_scale = new_height / carImg.height
    #print(new_width, new_height)
    carImg = carImg.resize(( new_width, new_height))

    # paste the car image in the center of the new image
    img.paste(carImg, (img.width // 2 - int(x * w_scale),img.height // 2 - int(y * h_scale) ), carImg)

    #this is the only way i can get the image to be vaguely centered on the chart
    #some of the plotly documentations on this online are kinda wrong (especially about xref and yref both being paper), so it was hard to find
    fig.add_layout_image(dict(
        source=img,
        xref="paper",
        yref="paper",
        x = .5,
        y = .5,
        sizex = 1, sizey = 1,
        xanchor="center", yanchor="middle",
        layer="above")
    )

    # img = img.convert("RGBA")

    return (fig, scale)
# create the legend for side views
def legend_creation(img, s, children, index, mirrored = False):
    # the legend is done for accessibility - may or may not slightly intersect with other parts of the image, but that's fine
    width = img.width
    height = img.height
    drawing = ImageDraw.Draw(img)

    #mirrored is for side view, not mirrored is front view
    #legend creation
    if not mirrored:
        text_width = width - 45 * s
        img_width = text_width - 15 * s
    else:
        text_width = 20 * s
        img_width = 5 * s
        width  = 65 * s
    lab_height = 2 * s
    lab_h_delta = 16 * s #vertical distance between each elements in the legend

    drawing.rectangle( [img_width - 5 * s, 0, width, 50 * s], fill = "white", outline = "black", width = s )
    font = ImageFont.truetype("blindspotapp/static/car_images/arial.ttf", 6 * s)

    drawing.line( [ width - 50 * s, lab_height, width - 50* s, lab_height + 12 * s], fill = "brown", width = int( 2*s) );
    drawing.text((text_width, lab_height + 2 * s), "1 foot, for scale", font=font, fill=(0,0,0, 255))

    lab_height += lab_h_delta

    drawing.rectangle( (img_width, lab_height, img_width + 12 * s, lab_height + 12 * s), fill=(0,255,0, 255) )
    drawing.text((text_width,lab_height + 2 * s), "Visible Zone", font=font, fill=(0,0,0, 255))

    lab_height += lab_h_delta

    drawing.rectangle( (img_width, lab_height, img_width + 12 * s, lab_height + 12 * s), fill=(0,0,0, 255) )
    drawing.text((text_width, lab_height + 2 * s), "Blind Zone", font=font, fill=(0,0,0, 255))

    #add in the label at the bottom of the image
    if index > -1:
        #this is done here because it's easier to have the image be scaled / cropped / flipped before text is done
        new_img = Image.new("RGB", (img.width, img.height + 12 * s),  "white" )
        new_img.paste( img, (0, 0) )
        drawing = ImageDraw.Draw(new_img)

        font = ImageFont.truetype("blindspotapp/static/car_images/arial.ttf", 10 * s)
        #create text string
        text = ""
        if mirrored:
            text += "Side "
        else:
            text += "Front "
        text += "Blind Zone extends out by " + str(children) + " "
        if children == 1:
            vru_names = ["preschool child", "elementary school child", "elementary school child on a bicycle", "adult in a wheelchair", "adult on a bicycle", "adult"]
        else:
            vru_names = ["preschool children", "elementary school children", "elementary school children on bicycles", "adults in wheelchairs", "adults on bicycles", "adults"]
        text += vru_names[index]

        inches = children * people[index][1]
        feet = str(int(inches / 12))
        inches = str(inches % 12)

        text += " (" + feet + "' " + inches + '")'

        drawing.text((0,new_img.height - 11 * s), text, font=font, fill=(0,0,0, 255))
        return new_img
    else:
        return img

def upload_to_cloudinary(img_string):
    cloudinary.config(
      cloud_name = "dkrq49vzq",
      api_key = "733231156826462",
      api_secret = "tf4ebuGXPE1AS5ZlGqG6WkQWTXU",
      secure = True
    )

    uploaded = cloudinary.uploader.upload("data:image/png;base64," + img_string,
        folder = "generated-images",
        overwrite = True,
        notification_url = "https://mysite.example.com/notify_endpoint")

    if 'url' in uploaded.keys():
        return uploaded['url']

# interfaces with views.py

# create front and side images only - used right after initial airtable upload
# for readability, it might be nice to have one function for each image that the interfaces with views.py script interacts with
# the create_all_images function only will be commented in detail because that encompasses the rest of them
def create_easy_images(id_num, scale, index):
    #create front
    data = get_data_front(id_num)
    children = -1
    if len(data) == 4: #if there is a vin
        (front_img, width) = create_image_vin(data, scale, data[3] )
        if front_img == None:
            (front_img, width) = create_new_image_front((data[0], data[1], data[2]), scale )
    else:
        (front_img, width) = create_new_image_front(data, scale  )

    if index >= 0:
        front_img, children = add_VRU_side( data, width, scale, index, 0, front_img)
    front_img = crop_image( data[0], width, 0, scale, front_img)
    front_img = legend_creation(front_img, scale, children,index, False)

    buffered = BytesIO()
    front_img = front_img.convert("RGB")
    front_img.save(buffered, format="jpeg")
    front_str = base64.b64encode(buffered.getvalue()).decode()

    print("finished with front image")

    #create side

    data = get_data_side(id_num)
    if data is not None:
        (side_img, width) = create_image_side(data, scale)
        if index >= 0:
            side_img, children = add_VRU_side( data, width, scale, index, 1, side_img)
        side_img = crop_image( data[0], width, 1, scale, side_img)
        side_img = ImageOps.mirror(side_img)
        side_img = legend_creation( side_img, scale, children,index, True)

        buffered = BytesIO()
        side_img = side_img.convert("RGB")
        side_img.save(buffered, format="jpeg")
        side_str = base64.b64encode(buffered.getvalue()).decode()
        #side_img.save("side_view.jpg")
        print("finished with side image")
    else:
        side_str = ""
        print("side image failed")


    return [front_str, side_str]
#create all images - used for vru changes when the overhead image has not started to be generated
def create_all_images(id_num, scale, index):
    #create front
    data = get_data_front(id_num)
    children = 0
    #print("index " + str(index) )
    if len(data) == 4: #means a vin was return
        (front_img, width) = create_image_vin(data, scale, data[3] ) # if none is returned (like through an invalid body type), run the normal creation script
        if front_img == None:
            (front_img, width) =create_new_image_front((data[0], data[1], data[2]), scale ) #as opposed to create_image_front, which does draws the car via polygons
    else:
        (front_img, width) = create_new_image_front(data, scale  )

    if index >= 0: #seen in all image creation blocks - if there are vrus, add them
        front_img, children = add_VRU_side( data, width, scale, index, 0, front_img)
    # when you need to debug pixel - relevant stuff, comment out the next two lifes
    front_img = crop_image( data[0], width, 0, scale, front_img) #crops the image past the volume of interest. also scales it back
    front_img = legend_creation(front_img, scale, children,index, False) #add the legend and the label for number of vrus

    #seen in all blocks - gets a string that can be passed via json from views.py to getinfo.html
    buffered = BytesIO()
    front_img.save(buffered, format="jpeg")
    front_str = base64.b64encode(buffered.getvalue()).decode()

    print("finished with front image")

    #create side
    # same as the front, basically
    data = get_data_side(id_num)
    children = 0
    if data is not None:
        (side_img, width) = create_image_side(data, scale)
        if index >= 0:
            side_img, children = add_VRU_side( data, width, scale, index, 1, side_img)
        side_img = crop_image( data[0], width, 1, scale, side_img)
        side_img = ImageOps.mirror(side_img) #the biggest change, in this function - we mirror because drawing unmirrored is easier, but needed to be mirrored in the end
        #perhaps in the future, the unit of input (inches / centi) can be uploaded to the airtable or the region can be detected so that mirroring (on this image and the front image) can be done or not
        side_img = legend_creation( side_img, scale, children,index, True)

        buffered = BytesIO()
        side_img = side_img.convert("RGB") #might not be necessary?
        side_img.save(buffered, format="jpeg")
        side_str = base64.b64encode(buffered.getvalue()).decode()
        #side_img.save("side_view.jpg")
    else:
        side_str = ""

    print("finished with side image")

    #create overhead
    data = get_data_top(id_num)
    if data is not None:
        fig = create_polar(data, scale) #make main plotly plot (back / gray bars with green background)

        #img_bytes = fig.to_image(format="png")
        (fig, s) = create_image_top(fig, data[3], scale) #add the car/truck image (to the figure)
        if index >= 0:
            add_VRU_top(fig, data, s, scale , index, True) #the "True" can be taken out as the option for the "slow" vru calculations is not an option anymore
        #top_str = fig

        #this next line (when running this program locally) is the main time sink. if a way to pass back plotly plots to getinfo.html can be found, then this stop can be avoided.
        #it would affect the add_vru_top function because that assumes the crop
        # a way to crop plotly plots (as figures) was looked for, but never  - maybe an html thing is possible
        top_img = fig.to_image(format="jpeg")
        top_img = Image.open(BytesIO(top_img)).convert("RGB")
        top_img = top_img.crop( (top_img.width * .35, 0, top_img.width, top_img.height * .65  ) )
        top_img = top_img.resize( ( int(200 *scale), int(200 *scale)) )

        buffered = BytesIO()
        top_img = top_img.convert("RGB")
        top_img.save(buffered, format="jpeg")
        top_str = base64.b64encode(buffered.getvalue()).decode()
        #top_img.save("top_view.jpg")

    else:
        top_str = ""


    return (front_str, side_str, top_str)
# used to create overhead upon submitting the main form - currently unused
def create_specific_image(json_string, scale, index, whichone):

    if whichone == 3: #for single image generation, there only exists the need for overhead
        data = get_data_top_json(json_string)
        fig = create_polar(data, scale)

        #img_bytes = fig.to_image(format="png")
        (fig, s) = create_image_top(fig, data[3], scale)
        if index >= 0:
            fast = True
            add_VRU_top(fig, data, s, scale , index, fast)

        top_img = fig.to_image(format="jpeg")
        top_img = Image.open(BytesIO(top_img)).convert("RGB")
        top_img = top_img.crop( (top_img.width * .35, 0, top_img.width, top_img.height * .65  ) )
        top_img = top_img.resize( ( int(200 *scale), int(200 *scale)) )

        buffered = BytesIO()
        top_img = top_img.convert("RGB")
        top_img.save(buffered, format="jpeg")
        top_str = base64.b64encode(buffered.getvalue())
        return top_str
# used to create overhead upon 3rd page load
def create_overhead_only(id_num, scale, index):
    #create overhead
    scale = int(scale)
    data = get_data_top(id_num)
    if data is not None:
        fig = create_polar(data, scale)

        (fig, s) = create_image_top(fig, data[3], scale)
        if index >= 0:
            fast = True
            add_VRU_top(fig, data, s, scale , index, fast)

        top_img = fig.to_image(format="jpeg")
        top_img = Image.open(BytesIO(top_img)).convert("RGB")
        top_img = top_img.crop( (top_img.width * .35, 0, top_img.width, top_img.height * .65  ) )
        top_img = top_img.resize( ( int(200 *scale), int(200 *scale)) )

        buffered = BytesIO()
        top_img = top_img.convert("RGB")
        top_img.save(buffered, format="jpeg")
        top_str = base64.b64encode(buffered.getvalue()).decode()
        #top_img.save("top_view.jpg")
    else:
        top_str = ""


    return top_str



    #return (front_str, side_str, top_str)
"""
if __name__ == "__main__":
    id_num = int(sys.argv[1])
    if len(sys.argv) > 2:
        scale = int(sys.argv[2])
        index = int(sys.argv[3])
    else:
        scale = 5
        index = -1

    strs = create_all_images(id_num, scale, index)
""" 
