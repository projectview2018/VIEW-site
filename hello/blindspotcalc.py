from math import *

ceiling = 6.16666 # 6'2" which is the 95th percentile male
DH = 4
e = 15
f = 15
c = 7
d = 7

def find_total_truck_interest_area(angles):
    # finds the total interest volume for a truck

    # NVPs is a list of the nearest visible points
    # angles is a list of the  correspnding counterclockwise angular positions of the measurements
    # 0 is straight ahead. Use radians
    # DH is the driver eye height
    # c is the horizontal distance between the driver's eye and the passenger side of the truck
    # d is the horizontal distance between the driver's eye and the front bumper of the truck
    # e is the horizontal length of the area of interest to the right of the passenger side wall
    # f is the horizontal length of the area of interest forward of the bumper

    # initialize total volume counter:
    interest = 0
    angles = angles.split(',')
    angles = list(map(int, angles))
    print(angles)
    # Iterate through the list of slices
    for i in range(0, len(angles) - 1):
        # determine angle
        # currently using the difference between a measurement and the next one
        # ignoring the last slice
        # probably go back and refine this, maybe.
        theta = 0.5 * abs(-angles[i + 1] + angles[i])  # width of slice, divided in half for right angle math
        hood = find_rectangular_coordinate(c, d, angles[i])  # distance of edge of truck
        boundary = find_rectangular_coordinate(c + e, d + f, angles[i])  # distance of edge of interest
        slicevolume = 2 * find_total_slice_volume(hood, boundary, ceiling, theta)  # total volume in slice
        interest += slicevolume

    return interest

def find_total_truck_blind_area(NVPs, angles):
    # finds the total blind volume for a truck dataset

    # NVPs is a list of the nearest visible points
    # angles is a list of the  correspnding counterclockwise angular positions of the measurements
    # 0 is straight ahead. Use radians
    # DH is the driver eye height
    # c is the horizontal distance between the driver's eye and the passenger side of the truck
    # d is the horizontal distance between the driver's eye and the front bumper of the truck
    # e is the horizontal length of the area of interest to the right of the passenger side wall
    # f is the horizontal length of the area of interest forward of the bumper

    # initialize total volume counter:
    blind = 0

    # Iterate through the list of slices
    for i in range(0, len(NVPs) - 1):
        # determine angle
        # currently using the difference between a measurement and the next one
        # ignoring the last slice
        # probably go back and refine this, maybe.
        theta = 0.5 * abs(-angles[i + 1] + angles[i])  # width of slice, divided in half for right angle math
        hood = find_rectangular_coordinate(c, d, angles[i])  # distance of edge of truck
        boundary = find_rectangular_coordinate(c + e, d + f, angles[i])  # distance of edge of interest

        blindvolume = 2 * find_blind_volume(NVPs[i], DH, hood, boundary, ceiling, theta)  # blind volume in slice
        blind += blindvolume

    return blind
