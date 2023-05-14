import time
import math
import queue
from shapely import geometry
import shapely.geometry
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from coordinateconversion import localtoglobal_x
from coordinateconversion import localtoglobal_y
import redis 
from redis.commands.json.path import Path




"""
      This function takes the coordinates of the tag, the coordinates of the AGV, the coordinates of the
      geofence and the offset value as input and returns the zone in which the tag is present
      
      :param rxl: list of x coordinates of the geofence in the local frame
      :param ryl: list of y coordinates of the robot in local frame
      :param agv_pos: This is the position of the AGV in the global frame
      :param x: x coordinate of the tag
      :param y: y coordinate of the tag
      :param zone_offset_value: This is the value that determines the size of the red zone. The default
      value is 0.2
"""

gbl_geofence_coords= []


#Redis CONFIGURATION
redis_con = redis.Redis(host="127.0.0.1", port=6379, db=0)
#Redis QUERY
result= redis_con.json().get('user_input')
zone_offset_value= redis_con.json().get('user_input',Path('.zone_offset_value'))
print("result",result)
print('zone_offset_value',zone_offset_value)
rxl= redis_con.json().get('geofence_relative_coordinates',Path('.geofence_relative_xcoordinates'))
ryl= redis_con.json().get('geofence_relative_coordinates',Path('.geofence_relative_ycoordinates'))
print("rxl",rxl)
print("ryl",ryl)

def agv_position():
    'Redis AGV_Positions'
    agv_position= redis_con.xread({'agv_pos_tag': "$"},count=1,block=0)
    [[stream, [[number, d]]]] = agv_position
    y = {k.decode("utf-8"):v.decode("utf-8") for k,v in d.items()}


    agv_xs=(y['agv_xs'])
    agv_ys=(y['agv_ys'])
    agv_angle=(y['agv_angle'])

    agv_angles=float(agv_angle)
    agv_xss=float(agv_xs)
    agv_yss=float(agv_ys)
    agv_pos=[agv_xss,agv_yss,agv_angles]
    print("agv_pos",agv_pos)
    return agv_pos

def tag_position():
    'Redis TAG_Positions'
    tag_position= redis_con.xread({'tag_pos': "$"},count=1,block=0)
    [[stream, [[number, m]]]] = tag_position
    x = {k.decode("utf-8"):v.decode("utf-8") for k,v in m.items()}

    tag_xs=(x['tag_x'])
    tag_ys=(x['tag_y'])
    tag_x=float(tag_xs)
    tag_y=float(tag_ys)
    print("tag_pos", tag_x,tag_y)
    return tag_x,tag_y


def Tag_detection():
      print("--------Tag---------")
      print("zoneoffset", zone_offset_value)

      while True:
            
            agv_pos= agv_position()
            x,y= tag_position()

      
            inside_purple = False
            inside_red = False

            gbx= localtoglobal_x(rxl, agv_pos, ryl)
            #print("gbx=", gbx)
            gby= localtoglobal_y(rxl, agv_pos, ryl)
            #print("gby=", gby)

            tag_point = Point(x, y)
            gbl_geofence_coords.clear()
            for gx, gy in zip(gbx, gby):
                  gbl_geofence_coords.append([gx, gy])
            #print( "gbl_geofence_coords",gbl_geofence_coords )

            lines = [
                  [gbl_geofence_coords[i - 1], gbl_geofence_coords[i]]
                  for i in range(len(gbl_geofence_coords))]

            factor = zone_offset_value

            xs = [i[0] for i in gbl_geofence_coords]
            ys = [i[1] for i in gbl_geofence_coords]
            x_center = 0.5 * min(xs) + 0.5 * max(xs)
            y_center = 0.5 * min(ys) + 0.5 * max(ys)

            min_corner = geometry.Point(min(xs), min(ys))
            max_corner = geometry.Point(max(xs), max(ys))
            center = geometry.Point(x_center, y_center)
            shrink_distance = center.distance(min_corner) * factor

            my_polygon = geometry.Polygon(gbl_geofence_coords)
            my_polygon_shrunken = my_polygon.buffer(-shrink_distance)
 

            inside_purple = my_polygon.contains(tag_point)
            inside_red = my_polygon_shrunken.contains(tag_point)
            if inside_purple == True:
                  if inside_red == True:
                        warning = "warning:Tag is inside the geofence-red zone"
                        print("warning:Tag is inside the geofence-red zone")

                  else:
                        warning = "warning:Tag is inside the geofence-blue zone"
                        print("warning:Tag is inside the geofence-blue zone")
            else:
                  warning = "warning:Tag is outside the geofence"
                  print("warning:Tag is outside the geofence")
            print("warning",warning)
            redis_con.set("warning", warning)
            #redis_con.xadd("WARNING_STREAM", warning)#change warning variable to dict value to stream 

            gbx.clear()
            gby.clear()  
            time.sleep(1)

