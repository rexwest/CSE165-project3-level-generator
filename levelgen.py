###############################################################################
# Level Generator for UCSD CSE 165 Space Salmon
# 
# Parameters:
#     -See github readme, or below
# 
# Output File Format:
# 
#     C: Center of the gate
#     R: Right vector
#     U: Up vector
# 
#     CX0 CY0 CZ0 RX0 RY0 RZ0 UX0 UY0 UZ0 
#     CX1 CY1 CZ1 RX1 RY1 RZ1 UX1 UY1 UZ1 
#     ...
#     CXn CYn CZn RXn RYn RZn UXn UYn UZn 
# 
# Written by Rex West, Winter 2015
#
############################################################################### 


###############################################################################
# Imports
############################################################################### 
import sys
import math
import random
import optparse


###############################################################################
# Math Functions
############################################################################### 
def clampf(v, min, max):
	return min if v < min else max if v > max else v

def combo(n, i):
	return math.factorial(n) / ( math.factorial(n-i) * math.factorial(i) )


###############################################################################
# Vector Functions
############################################################################### 
class Vector3:

	def __init__(self, x=0.0, y=0.0, z=0.0):
		self.x = x
		self.y = y
		self.z = z

def add3(a, b):
	r = Vector3()
	r.x = a.x + b.x
	r.y = a.y + b.y
	r.z = a.z + b.z
	return r

def subtract3(a, b):
	r = Vector3()
	r.x = a.x - b.x
	r.y = a.y - b.y
	r.z = a.z - b.z
	return r

def multiply3(a, b):
	r = Vector3()
	r.x = a.x * b.x
	r.y = a.y * b.y
	r.z = a.z * b.z
	return r

def scale3(v, c):
	r = Vector3()
	r.x = v.x * c
	r.y = v.y * c
	r.z = v.z * c
	return r

def dot3(a, b):
	return a.x * b.x + a.y * b.y + a.z * b.z

def cross3(a, b):
	r = Vector3()
	r.x = (a.y * b.z) - (b.y * a.z)
	r.y = (a.z * b.x) - (b.z * a.x)
	r.z = (a.x * b.y) - (b.x * a.y)
	return r

def length3(a):
	return math.sqrt((a.x ** 2.0) + (a.y ** 2.0) + (a.z ** 2.0))

def normalize3(a):
	return scale3(a, 1.0 / length3(a))

def copy3(v):
	return Vector3(v.x, v.y, v.z)

def uniform_sphere_sample():
	sample = Vector3()

	while True:
		sample.x = 2.0 * random.random() - 1.0
		sample.y = 2.0 * random.random() - 1.0
		sample.z = 2.0 * random.random() - 1.0
		if length3(sample) <= 1.0:
			break

	return normalize3(sample);

def uniform_cone_sample(direction, spread):
	normalized_direction = normalize3(direction)
	spread = clampf(spread, 0.0, 1.0)

	#If the spread is too small to get a sample in a reliable amount of time
	if(spread < 0.001):
		return normalize3(direction)

	#Generate random samples until one satisfies the constraints
	while True:
		sample = uniform_sphere_sample()
		if dot3(normalized_direction, sample) >= (1.0 - spread):
			break

	return sample

def minimize3(a, b):
	r = Vector3()
	r.x = b.x if (a.x is None or a.x > b.x) else a.x
	r.y = b.y if (a.y is None or a.y > b.y) else a.y
	r.z = b.z if (a.z is None or a.z > b.z) else a.z
	return r

def maximize3(a, b):
	r = Vector3()
	r.x = b.x if (a.x is None or a.x < b.x) else a.x
	r.y = b.y if (a.y is None or a.y < b.y) else a.y
	r.z = b.z if (a.z is None or a.z < b.z) else a.z
	return r

def nary_maximum(vals):
	if len(vals) == 0:
		return None
	r = vals[0]
	for v in vals:
		if v > r:
			r = v
	return r


###############################################################################
# Spline Functions
############################################################################### 
def point_on_spline(points, t):
	r = Vector3()
	t = clampf(t, 0.0, 1.0)

	n = len(points)
	i = 0

	for point in points:
		r.x = r.x + bez(n, i, t, point.x)
		r.y = r.y + bez(n, i, t, point.y)
		r.z = r.z + bez(n, i, t, point.z)
		i = i + 1

	return r

def tangent_on_spline(points, t):
	delta = 0.00001
	r = Vector3()
	t = clampf(t, 0.0, 1.0 - delta)

	pre = pointOnSpline(t)
	post = pointOnSpline(t + delta)

	return normalize3(subtract3(post, pre))


def bez(n, i, t, control):
	return combo(n, i) * math.pow(1.0-t, n-i) * math.pow(t, i) * control;

def next_tangent_sample(v0, v1):
	return add3(v1, subtract3(v1, v0))


###############################################################################
# Gate Functions
############################################################################### 
class Gate:
	def __init__(self, c=Vector3(), r=Vector3(), u=Vector3()):
		self.c = c
		self.r = r
		self.u = u


###############################################################################
# Constants
############################################################################### 
DEBUG = False

WORLD_SIZE = 10000
WORLD_MARGIN = 4000
WORLD_CENTER = Vector3(0, 0, 0)

GATE_COUNT = 100
GATE_WIDTH = 10
GATE_HEIGHT = 5

PATH_COUNT = 3
PATH_CONTROL_POINT_MIN = 3 #Should be >= 3
PATH_CONTROL_POINT_MAX = 7
PATH_CONTROL_POINT_SPREAD = math.sqrt(2.0)/2.0

SAMPLE_DELTA = 0.001

OUTPUT_FILE_PATH = "level.txt"


###############################################################################
# Generate a level!
###############################################################################
def generate_level():

	#Generate a set of paths
	paths = generate_paths()

	#Scale the final path to fit the world
	paths = scale_paths_to_world(paths)

	#Generate a set of gates on the path
	gates = generate_gates(paths)

	#Serialize the level to file
	serialize_gates(gates)

	return gates

def generate_gates(paths):
	gates = list()

	#Get path set data
	path_lengths = [len(path) for path in paths]
	total_length = sum(path_lengths) - (len(paths) - 1)

	#Generate path intervals
	path_intervals = list()
	path_index = 0
	path_intervals.append((0.0, path_index))
	elapsed_points = 1.0

	for path in paths:
		elapsed_points = (elapsed_points - 1.0) + len(path)
		path_intervals.append( (elapsed_points / total_length, path_index) )
		path_index = path_index + 1

	#Sample the paths
	for i in range(GATE_COUNT):
		gates.append(generate_gate(float(i)/GATE_COUNT, paths, path_intervals))


	return gates


def generate_gate(t, paths, intervals):
	#Keep t away from the edges
	t = clampf(t, 0.0 + SAMPLE_DELTA * 2, 1.0 - SAMPLE_DELTA * 2)

	#Sample the path
	prev_point = sample_paths(t - SAMPLE_DELTA, paths, intervals)
	curr_point = sample_paths(t, paths, intervals)
	next_point = sample_paths(t + SAMPLE_DELTA, paths, intervals)

	#Get two tangent approximations
	tan_1 = normalize3(subtract3(curr_point, prev_point))
	tan_2 = normalize3(subtract3(next_point, prev_point))

	#Calculate the right and up vectors
	right = normalize3(cross3(tan_2, tan_1))
	up = normalize3(cross3(right, tan_1))

	#Create a gate
	return Gate(curr_point, scale3(right, GATE_WIDTH/2.0), scale3(up, GATE_HEIGHT/2.0))


def sample_paths(t, paths, intervals):
	#Keep t in the valid range
	t = clampf(t, 0.0, 1.0)
	index = 0
	path_start_time = 0.0
	path_end_time = 0.0

	#Get the path index
	for (end_time, path_index) in intervals:
		if t < end_time:
			index = path_index
			path_end_time = end_time
			break
		path_start_time = end_time

	#Get the path
	path = paths[index]

	#Normalize t to the range f [0,1] on the current path
	normalized_t = (t - path_start_time) / (path_end_time - path_start_time)

	return point_on_spline(path, normalized_t)

def scale_paths_to_world(paths):
	mins = Vector3(None, None, None)
	maxs = Vector3(None, None, None)

	#Get the minimal and maximal values across all dimensions
	for path in paths:
		for point in path:
			mins = minimize3(mins, point)
			maxs = maximize3(maxs, point)

	#Of those, find the absolute maximum
	abs_max = nary_maximum([abs(val) for val in (mins.__dict__.values() + maxs.__dict__.values())])

	#Calculate the value needed to scale the path control points to fit into the world (taking a margin into account)
	world_scale = (float(WORLD_SIZE - WORLD_MARGIN) / WORLD_SIZE) * (WORLD_SIZE / abs_max)

	#Scale each component of each point in each path
	for path in paths:
		for point in path:
			point.x = point.x * world_scale
			point.y = point.y * world_scale
			point.z = point.z * world_scale

	return paths

def generate_paths():
	#Intermediate variables
	paths = list()
	start_point = Vector3()
	next_point = uniform_sphere_sample()

	#Generate a set of paths
	for i in range(0, PATH_COUNT):
		point_count = random.randint(PATH_CONTROL_POINT_MIN, PATH_CONTROL_POINT_MAX)
		path = genetate_path(point_count, start_point, next_point)
		start_point = path[-1]
		next_point = next_tangent_sample(path[-2], path[-1])
		paths.append(path)

	return paths

def genetate_path(point_count, start_point, first_point):
	points = list()

	prev = start_point
	curr = first_point
	next = None

	points.append(copy3(start_point))
	points.append(first_point)

	for i in range(0, point_count - 2):
		next = uniform_cone_sample(subtract3(curr, prev), PATH_CONTROL_POINT_SPREAD)
		prev = curr
		curr = next
		points.append(next)

	return points


###############################################################################
# Convert Gates to File
############################################################################### 
def serialize_gates(gates):
	#Print the gates if the debug flag is set
	if DEBUG:
		for gate in gates:
			print gate.c.x, gate.c.y, gate.c.z, gate.r.x, gate.r.y, gate.r.z, gate.u.x, gate.u.y, gate.u.z

	#Write the gates to file!
	fout = file(OUTPUT_FILE_PATH, "w")
	fout.writelines( ("%f %f %f %f %f %f %f %f %f\n" % (gate.c.x, gate.c.y, gate.c.z, gate.r.x, gate.r.y, gate.r.z, gate.u.x, gate.u.y, gate.u.z)) for gate in gates )
	

###############################################################################
# Main
############################################################################### 
if __name__ == "__main__":
    #Parameter parsing
    parser = optparse.OptionParser()
    parser.set_usage(sys.argv[0] + " [option]")

    #Parameter options
    parser.add_option("-o", "--outfile", dest="OUTPUT_FILE_PATH", action="store", default='level.txt', help="File to write to")
    parser.add_option("--debug", dest="DEBUG", action="store_true", default=False, help="Enable Debug printing")

    parser.add_option("--wsize", dest="WORLD_SIZE", action="store", default=10000, help="World Size")
    parser.add_option("--wmargin", dest="WORLD_MARGIN", action="store", default=4000, help="World Margin")

    parser.add_option("--gcount", dest="GATE_COUNT", action="store", default=100, help="Gate Count")
    parser.add_option("--gwidth", dest="GATE_WIDTH", action="store", default=10, help="Gate Width")
    parser.add_option("--gheight", dest="GATE_HEIGHT", action="store", default=5, help="Gate Height")

    parser.add_option("--pcount", dest="PATH_COUNT", action="store", default=3, help="Path Count")
    parser.add_option("--pcpmin", dest="PATH_CONTROL_POINT_MIN", action="store", default=3, help="Path Control Point Minimum")
    parser.add_option("--pcpmax", dest="PATH_CONTROL_POINT_MAX", action="store", default=7, help="Path Control Point Maximum")
    parser.add_option("--pcpspread", dest="PATH_CONTROL_POINT_SPREAD", action="store", default=(math.sqrt(2.0)/2.0), help="Path Control Point Sample Cone Spread")

    #Parse the parameters
    (options, args) = parser.parse_args()

    #Pass them to globals
    OUTPUT_FILE_PATH = options.OUTPUT_FILE_PATH
    DEBUG = options.DEBUG
    WORLD_SIZE = int(options.WORLD_SIZE)
    WORLD_MARGIN = int(options.WORLD_MARGIN)
    GATE_COUNT = int(options.GATE_COUNT)
    GATE_WIDTH = int(options.GATE_WIDTH)
    GATE_HEIGHT = int(options.GATE_HEIGHT)
    PATH_COUNT = int(options.PATH_COUNT)
    PATH_CONTROL_POINT_MIN = int(options.PATH_CONTROL_POINT_MIN) #Should be >= 3
    PATH_CONTROL_POINT_MAX = int(options.PATH_CONTROL_POINT_MAX)
    PATH_CONTROL_POINT_SPREAD = float(options.PATH_CONTROL_POINT_SPREAD)

    #Generate a level!
    generate_level()


