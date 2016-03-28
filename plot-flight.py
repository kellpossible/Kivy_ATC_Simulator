from kivy.garden.mapview import MapView
from kivy.garden.mapview import MapView
from kivy.app import App
import math


EarthRadius = 6378137.0
#these all assume you're using radians for angles
def y_to_lat(a_y):
	"""returns lattitude in radians"""
	return 2.0 * math.atan(math.exp(math.radians(a_y / EarthRadius))) - math.pi/2.0

def lat_to_y(a_lat):
	return math.log(math.tan(math.pi/4.0 + a_lat/2.0)) * EarthRadius

def x_to_lon(a_x):
	"""returns longtitude in radians"""
	return a_x / EarthRadius

def lon_to_x(a_lon):
	return a_lon * EarthRadius







class MapViewApp(App):
    def build(self):
        mapview = MapView(zoom=11, lat=50.6394, lon=3.057)
        return mapview

MapViewApp().run()