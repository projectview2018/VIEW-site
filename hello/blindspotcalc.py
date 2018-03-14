from math import *

ceiling = 74 # 6'2" which is the 95th percentile male
e = 180 # 15 feet
f = 180

def find_total_truck_interest_area(angles, c, d):
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
    # angles = angles.split(',')
    angles = list(map(float, angles))
    c = int(c)
    d = int(d)
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

def find_total_truck_blind_area(NVPs, angles, DH, c, d):
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
    angles = list(map(float, angles))
    NVPs = list(map(float, NVPs))
    DH = float(DH)
    c = int(c)
    d = int(d)

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

# CASE SELECTOR


def find_blind_volume(NVP, DH, hood, boundary, ceiling, theta):
    """
    NVP: horizontal distance to nearest visible point on ground
    DH: driver eye height above ground
    hood: horizontal distance to edge of truck in given direction
    boundary: horixontal distance to outside of area of interest
    ceiling: vertical height of area of interest
    theta: width of half-slice in radians
    """
    # I'm sorry for this pileup, I'm gonna make an illustrated flowchart for it in documentation
    if NVP <= hood:
        # slice has 100% visibility
        # Case A and B
        print('100% visibility')
        volume = find_total_slice_volume(hood, boundary, ceiling, theta)
    elif DH < ceiling and NVP <= boundary:
        # Case D
        print('Case D')
        volume = tetra_donut(hood, NVP, DH, theta)
    elif DH < ceiling and NVP > boundary:
        # Case F
        print('Case F')
        volume = trap_donut(hood, boundary, NVP, DH, theta)
    elif DH > ceiling:
        # find where sight line intersects area of interest
        T = radius(NVP, DH, ceiling)
        if T > boundary:
            # Case J
            print("0% visibility")
            volume = 0
        elif T < hood and NVP < boundary:
            # Case C
            print('Case C')
            volume = tetra_donut(hood, NVP, DH, theta)
        elif T < hood and NVP > boundary:
            # Case E
            print('Case E')
            volume = trap_donut(hood, boundary, NVP, DH, theta)
        elif hood < T < NVP < boundary:  # T always < NVP, just checking if both are between
            # Case G
            print('Case G')
            volume = capped_tetra_donut(hood, NVP, ceiling, DH, theta)
        elif hood < T < boundary < NVP:  # T always < NVP, just checking if both are between
            # Case H
            print('Case H')
            volume = capped_trap_donut(hood, boundary, NVP, ceiling, DH, theta)
    else:
        volume = None

    if volume is not None:
        return volume
    else:
        print("What did you feed the find_blind_volume function?")
        return


def find_total_slice_volume(hood, boundary, ceiling, theta):
    """
    hood: horizontal distance to edge of truck in given direction
    boundary: horixontal distance to outside of area of interest
    ceiling: vertical height of area of interest
    theta: width of half-slice in radians
    """
    volume = prism_donut(hood, boundary, ceiling, theta)
    return volume


def find_rectangular_coordinate(c, d, angle):
    """
    finds the distance at which a slice at an angle relative to straight ahead
    intersects a rectangle with boundaries
    c to the right of the eye point and
    d forward of the eye point
    """

    # determine angular position of the corner
    corner = atan2(-c, d)

    if angle > corner:
        # this measurement is to the front of the rectangle
        D = d / cos(angle)
    else:
        # this measurement is to the side of the rectangle
        D = c / cos(angle + pi / 2)
    return D


# GEOMETRIC BUILDING BLOCKS


def height(R, H, r):
    """
    find the height of the intersection at x = r of the line from (0, H) to (R, 0)
    """
    if 0 <= r <= R:
        h = H - (H * r) / R
        return h

    else:
        print("height function: radius is not in range")


def radius(R, H, h):
    """
    find the horizontal distance of the intersection at y = h of the line from (0, H) to (R, 0)
    """
    if 0 <= h <= H:
        r = R - (R * h) / H
        return r

    else:
        print("radius function: height is not in range")


def prism(R, H, theta):
    '''
    volume of a rectangle of width Radius and height Height revolved through angle theta
    '''
    volume = 0.5 * pow(R, 2) * H * tan(theta)
    return volume


def tetra(R, H, theta):
    '''
    volume of a very specific tetrahedron with a right triangle as the base
    geometrically I assume the peak is centered over the base corner of angle theta
    radius is the length on ground from center point (like NVP)
    height is the height of the tetrahedron (like driver eye height)
    theta is the counterclockwise angle in radians from the leg of length radius to the hypotenuse
    '''
    volume = 1 / 6 * pow(R, 2) * H * tan(theta)
    return volume


def prism_donut(r, R, H, theta):
    '''
    donut. r is inner radius, R is outer radius.
    '''
    total = prism(R, H, theta)
    inside = prism(r, H, theta)
    volume = total - inside
    return volume


def tetra_donut(r, R, H, theta):
    '''
    Right triangle with leg R-r and h (calculated within)
    revolved theta radians at distance r
    R is the outer point and H is the "driver eye point
    '''
    # find intersect height with inner radius
    h = height(R, H, r)
    total = tetra(R, H, theta)
    rectangle = prism(r, h, theta)
    top = tetra(r, H - h, theta)
    volume = total - rectangle - top
    return volume


def capped_tetra_donut(r, R, h, H, theta):
    '''
    a right tetrahedron missing its top above height h
    and its center within radius r
    h must be below r's intersect  with the view line
    R is the outer point and H is the "driver eye point
    H is the total height of prism (driver eye height)
    '''
    # find radius of intersect with top of area of interest
    T = radius(R, H, h)

    total = tetra(R, H, theta)
    rectangle = prism(r, h, theta)
    top = tetra(T, H - h, theta)
    volume = total - rectangle - top
    return volume


def trap_donut(r1, r2, R, H, theta):
    """
    quadrilateral with vertical sides at r1 and r2
    top slope runs from (0, H) to (R, 0)
    """
    # find height where view line enters the area of interest
    h1 = height(R, H, r1)
    # find height where view line exits the area of interest
    h2 = height(R, H, r2)

    rectangle = prism_donut(r1, r2, h2, theta)
    top = tetra_donut(r1, r2, H - h1, theta)
    volume = rectangle + top
    return volume


def capped_trap_donut(r1, r2, R, h, H, theta):
    """
    quadrilateral with vertical sides at r1 and r2
    top slope runs from (0, H) to (R, 0)
    capped at height h
    doesn't draw from trapezoid because there's a lot of ways to construct this (shrug)
    """
    tetrahedron = capped_tetra_donut(r1, R, h, H, theta)
    end = tetra_donut(r2, R, H, theta)
    volume = tetrahedron - end
    return(volume)