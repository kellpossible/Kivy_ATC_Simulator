from kivy.garden.mapview import MapView, MapMarker, MapLayer
from kivy.base import runTouchApp

from kivy.properties import StringProperty, ObjectProperty
from kivy.graphics import (Canvas, PushMatrix, PopMatrix, MatrixInstruction,
						   Translate, Scale, Line, Color)
from kivy.utils import get_color_from_hex

from os.path import join, dirname
import math
import datetime
import dateutil.parser
import csv

import re

#this is a test

class NavObject(object):
	def __init__(self, ICAO_id, latitude, longitude, **kwargs):
		self.ICAO_id = ICAO_id
		self.latitude = latitude
		self.longitude = longitude

	def get_icon_details(self):
		return None

class Airport(NavObject):
	def __init__(self, ICAO_id, latitude, longitude, **kwargs):
		super(Airport, self).__init__(ICAO_id, latitude, longitude, **kwargs)


	def get_icon_details(self):
		return {
		'source':join(dirname(__file__), "icons", "marker.png"),
		'anchor_x': 0.5,
		'anchor_y': 0.0
		}

class Fix(NavObject):
	def __init__(self, ICAO_id, latitude, longitude, **kwargs):
		super(Fix, self).__init__(ICAO_id, latitude, longitude, **kwargs)

	def get_icon_details(self):
		return {
		'source':join(dirname(__file__), "icons", "fix.png"),
		'anchor_x': 0.5,
		'anchor_y': 0.5
		}

class DirectionalBeacon(NavObject):
	def __init__(self, ICAO_id, latitude, longitude, **kwargs):
		super(DirectionalBeacon, self).__init__(ICAO_id, latitude, longitude, **kwargs)

class VOR(DirectionalBeacon):
	def __init__(self, ICAO_id, latitude, longitude, **kwargs):
		super(VOR, self).__init__(ICAO_id, latitude, longitude, **kwargs)

	def get_icon_details(self):
		return {
		'source':join(dirname(__file__), "icons", "vor.png"),
		'anchor_x': 0.5,
		'anchor_y': 0.5
		}

class ILS(DirectionalBeacon):
	def __init__(self, ICAO_id, latitude, longitude, **kwargs):
		super(ILS, self).__init__(ICAO_id, latitude, longitude, **kwargs)


class FlightPlan(object):
	@staticmethod
	def parse_xplane_fms(filename):
		nav_objects = []

		matcher = re.compile("(\d+)\s+([a-zA-Z-]+)\s+(\d+)\s+([+-]\d+[.]\d+)\s+([+-]\d+[.]\d+)\s*(\d+[.]\d+)*")
		f = open(filename, "r")
		for line in f:
			m = matcher.match(line)
			if m is not None:
				groups = m.groups()
				print(m.groups())
				ap = None
				if groups[0] == "1":
					ap = Airport(groups[1], float(groups[3]), float(groups[4]))

				if groups[0] == "11":
					ap = Fix(groups[1], float(groups[3]), float(groups[4]))

				if groups[0] == "3":
					ap = VOR(groups[1], float(groups[3]), float(groups[4]))

				if ap:
					nav_objects.append(ap)

		return FlightPlan(nav_objects)

	def __init__(self, nav_objects=[]):
		self.nav_objects = nav_objects

FP = FlightPlan.parse_xplane_fms("YMML2YSCB.fms")

PlanLatLon = []
for nav_object in FP.nav_objects:
	PlanLatLon.append([nav_object.latitude, nav_object.longitude])


def approx_equal(x, y, tolerance=0.0):
	return abs(x-y) <= 0.5 * tolerance * (abs(x) + abs(y))

class TrackEntry(object):
	def __init__(self, time, latitude, longitude, altitude, heading, roll, pitch):
		self.time = time
		self.latitude = latitude
		self.longitude = longitude
		self.altitude = altitude
		self.heading = heading
		self.roll = roll
		self.pitch = pitch

	def is_same_position(self, entry, tolerance=0.0):
		if approx_equal(self.latitude, entry.latitude, tolerance):
			if approx_equal(self.longitude, entry.longitude, tolerance):
				return True
		return False

track_entries = []

print("parsing track.csv")
with open("YMML2YSCB_track.csv", 'rb') as csvfile:
	trackreader = csv.reader(csvfile)
	for row in trackreader:
		print(row)
		time = dateutil.parser.parse(row[0])
		longitude = float(row[1])
		latitude = float(row[2])
		altitude = float(row[3])
		heading = float(row[4])
		roll = float(row[5])
		pitch = float(row[6])
		track_entry = TrackEntry(time, latitude, longitude, altitude, heading, roll, pitch)
		track_entries.append(track_entry)

csvfile.close()


print("creating plane track for drawing")
PathLatLon = []
entries_len = len(track_entries)
entry_index = 0
same_pos_count = 0
while entry_index < entries_len:
	include_entry = True
	entry = track_entries[entry_index]
	if entry_index > 0:
		last_entry = track_entries[entry_index-1]
		if entry.is_same_position(last_entry):
			include_entry = False
			same_pos_count += 1
	if include_entry:
		PathLatLon.append([entry.latitude, entry.longitude])

	entry_index += 2 #decrease the resolution by a factor of 2

print("number of latlon", len(PathLatLon))
print("number of track entries", len(track_entries))
print("number same pos", same_pos_count)

class AirPathMapLayer(MapLayer):
	initial_zoom = None
	first_time = True
	EarthRadius = 6378137.0

	def __init__(self, path_latlon, plan_latlon, **kwargs):
		super(AirPathMapLayer, self).__init__(**kwargs)

		self.path_latlon = path_latlon
		self.plan_latlon = plan_latlon

	def reposition(self):
		mapview = self.parent
		self.canvas.clear()

		plan_points=[]
		for ll in self.plan_latlon:
			x, y = mapview.get_window_xy_from(ll[0], ll[1], mapview.zoom)
			plan_points.append(x)
			plan_points.append(y)

		path_points=[]
		for ll in self.path_latlon:
			x, y = mapview.get_window_xy_from(ll[0], ll[1], mapview.zoom)
			path_points.append(x)
			path_points.append(y)

		
		self.canvas.add(Color(1,0,0))
		self.canvas.add(Line(points=plan_points, width=1.5))
		self.canvas.add(Color(0,0,0))
		self.canvas.add(Line(points=path_points, width=2))






view = MapView(zoom=11, lat=PathLatLon[0][0], lon=PathLatLon[0][1])
layer = AirPathMapLayer(path_latlon=PathLatLon, plan_latlon=PlanLatLon)

view.add_layer(layer)

for nav_object in FP.nav_objects:
	marker = MapMarker()
	print(nav_object.latitude, nav_object.longitude)
	marker.lat = nav_object.latitude
	marker.lon = nav_object.longitude
	icon_details = nav_object.get_icon_details()

	marker.source = icon_details['source']
	marker.anchor_x = icon_details['anchor_x']
	marker.anchor_y = icon_details['anchor_y']

	view.add_marker(marker)



runTouchApp(view)