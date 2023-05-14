import json
import numpy as np
import paho.mqtt.client as mqtt
import time
import redis 
from redis.commands.json.path import Path
from coordinateconversion import globaltolocal_x
from coordinateconversion import globaltolocal_y

newX = []  # new x coordinates for enlarge/shrink
newY = []   # new y coordinates for enlarge/shrink
enlarge_shrink = []
broker_address= "192.168.77.97"

client= mqtt.Client("enlarge")  # client ID "mqtt-test"

#Redis CONFIGURATION
redis_con = redis.Redis(host="127.0.0.1", port=6379, db=0)
#Redis QUERY
result= redis_con.json().get('user_input')
zone_offset_value= redis_con.json().get('user_input',Path('.zone_offset_value'))
upper= redis_con.json().get('user_input',Path('.upperlimit'))
lower= redis_con.json().get('user_input',Path('.lowerlimit'))
off_set= redis_con.json().get('user_input',Path('.off_set'))
Agv_name= redis_con.json().get('user_input',Path('.Agv_name'))
Geofence_id= redis_con.json().get('user_input',Path('.Geofence_id'))
global_coordinates=redis_con.json().get('geofence_relative_coordinates')
rxl= redis_con.json().get('geofence_relative_coordinates',Path('.geofence_relative_xcoordinates'))
ryl= redis_con.json().get('geofence_relative_coordinates',Path('.geofence_relative_ycoordinates'))

print("result",result)
print('zone_offset_value:',zone_offset_value)
print('upper:',upper)
print('lower:',lower)
print('off_set:',off_set)
print("Agv_name:",Agv_name)
print("Geofence_id:",Geofence_id)
print("rxl",rxl)
print("ryl",ryl)

def agv_position():
    'Redis AGV_Positions'
    agv_position= redis_con.xread({'agv_pos': "$"},count=1,block=0)
    [[stream, [[number, d]]]] = agv_position
    y = {k.decode("utf-8"):v.decode("utf-8") for k,v in d.items()}

    agv_speeds=(y['agv_speed'])
    agv_xs=(y['agv_xs'])
    agv_ys=(y['agv_ys'])
    agv_angle=(y['agv_angle'])
    agv_speed=float(agv_speeds)
    agv_angles=float(agv_angle)
    agv_xss=float(agv_xs)
    agv_yss=float(agv_ys)
    agv_pos=[agv_xss,agv_yss,agv_angles]
    print("agv_pos",agv_pos)
    return agv_speed, agv_pos


def Enlargeshrink():
    #client.publish("lnho", payload=json.dumps({"id": "upper"}))
    ################# Enlarge and shrink algorithm ##################
    print("--------Enlarge---------")
    uplarge = {  # json data to be published new data MapAreas/Geofence topic
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [enlarge_shrink]},
             "properties": {
                    "name": Geofence_id,
                    "isRelative": True,
                    "relativeItem": Agv_name,
                    "mqtt_settings_geofence": [],
                    "mqtt_settings_warningZone": [],
                    "zone_width": None,
                    "direction": 0,
                    "neighbours": [],
                    "isEnabled": True,
                    "disableIfFireAlarm": False,
                    "ignoredTags": [],
                    "waitingZoneNarrowArea": None,
                    "type": "geofence",
                    "event": None,
                },
            }
         ],
    }
    print(upper)
    print(lower)
    print(off_set)


    def normalizeVec(rxl, ryl):
        distance = np.sqrt(rxl * rxl + ryl * ryl)
        return rxl / distance, ryl / distance  # returning normalized vector

    def makeOffsetPoly(rxl, ryl, num, outer_ccw=1):
        num_points = len(rxl)

        for val in range(num_points):
            
            prev = (val + num_points - 1) % num_points
            
            next = (val + 1) % num_points
            

            vnX = rxl[next] - rxl[val]
            vnY = ryl[next] - ryl[val]
            vnnX, vnnY = normalizeVec(vnX, vnY)
            nnnX = vnnY
            nnnY = -vnnX

            vpX = rxl[val] - rxl[prev]
            vpY = ryl[val] - ryl[prev]
            vpnX, vpnY = normalizeVec(vpX, vpY)
            npnX = vpnY * outer_ccw
            npnY = -vpnX * outer_ccw

            bisX = (nnnX + npnX) * outer_ccw
            bisY = (nnnY + npnY) * outer_ccw

            bisnX, bisnY = normalizeVec(bisX, bisY)
            bislen = -(num) / np.sqrt(1 + nnnX * npnX + nnnY * npnY)

            newX.append(rxl[val] + bislen * bisnX)
            newY.append(ryl[val] + bislen * bisnY)

    def float_range(start, stop, step):
        assert step > 0.0
        total = start
        compo = 0.0
        while total <= stop:
            yield total
            y = step - compo
            temp = total + y
            tempr = round(temp, 4)
            compo = (tempr - total) - y
            total = tempr
    i=0

    while True:
        agv_speed,agv_pos=agv_position()
        
        print("agv_speed",agv_speed)

        count = len(upper)
        while i < count:
            con = list(float_range(lower[i], upper[i], 0.001))
            if agv_speed in con:
              val = i
              num = off_set[val]
              print("offset", num)
              i = 0
              break

            else:
              i += 1

        enlarge_shrink.clear()
        makeOffsetPoly(rxl, ryl, num)
        

        for ex, ey in zip(newX, newY):
            enlarge_shrink.append([ex, ey])
        print("coordinates1:", enlarge_shrink)

        print("data published to MapAreas")
        client.connect(broker_address, 1883)
        
        client.publish("MapAreas/Geofence", payload=json.dumps(uplarge))
        client.publish("uyytf", payload=json.dumps({"id": "gfgv"}))
        #print("published to MapAreas")
        newX.clear()
        newY.clear()
        #time.sleep(1)

