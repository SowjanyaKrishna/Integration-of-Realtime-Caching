import paho.mqtt.client as mqtt
import time
import json
import redis
from coordinateconversion import globaltolocal_x
from coordinateconversion import globaltolocal_y
from redis.commands.json.path import Path

#Redis CONFIGURATION
redis_con = redis.Redis(host="127.0.0.1", port=6379, db=0)
client= mqtt.Client("relative")  # client ID "mqtt-test"

result= redis_con.json().get('user_input')
Geofence_id= redis_con.json().get('user_input',Path('.Geofence_id'))
Agv_name= redis_con.json().get('user_input',Path('.Agv_name'))
Agv_topic= redis_con.json().get('user_input',Path('.Agv_topic'))
print("result",result)
print("---mqtt_relative----")

datax= redis_con.xread({'geofence_xcoordinates':"$"},count=1,block=0)
datay= redis_con.xread({'geofence_ycoordinates':"$"},count=1,block=0)


#datax= redis_con.xread({'geofence_xcoordinates':"$"},count=1,block=0)
[[stream, [[number, x]]]] = datax
valuex = {kx.decode("utf-8"):vx for kx,vx in x.items()}

xcord0=(valuex['geofence_xcoordinate0'])
xcord1=(valuex['geofence_xcoordinate1'])
xcord2=(valuex['geofence_xcoordinate2'])
xcord3=(valuex['geofence_xcoordinate3'])

xcord00=float(xcord0)
xcord10=float(xcord1)
xcord20=float(xcord2)
xcord30=float(xcord3)

gx= [xcord00,xcord10,xcord20,xcord30]# global x coordinates for geofence
print("gx",gx)

#datay= redis_con.xread({'geofence_ycoordinates':"$"},count=1,block=0)
[[stream, [[number, y]]]] = datay
valuey = {ky.decode("utf-8"):vy for ky,vy in y.items()}

xcord0=(valuey['geofence_ycoordinate0'])
xcord1=(valuey['geofence_ycoordinate1'])
xcord2=(valuey['geofence_ycoordinate2'])
xcord3=(valuey['geofence_ycoordinate3'])

ycord00=float(xcord0)
ycord10=float(xcord1)
ycord20=float(xcord2)
ycord30=float(xcord3)

gy= [ycord00,ycord10,ycord20,ycord30]# global y coordinates for geofence
print("gy",gy)


agv_position= redis_con.xread({'agv_pos_tag': "$"},block=0) #get agv position (change agv_pos to agv_pos_tag)

[[stream, [[number, d]]]] = agv_position
y = {k.decode("utf-8"):v.decode("utf-8") for k,v in d.items()}

#agv_speed=(y['agv_speed'])
agv_xs=(y['agv_xs'])
agv_ys=(y['agv_ys'])
agv_angle=(y['agv_angle'])
agv_angles=float(agv_angle)
agv_xss=float(agv_xs)
agv_yss=float(agv_ys)
agv_pos=[agv_xss,agv_yss,agv_angles]
print("agv_pos",agv_pos)




coordinates = [] 
broker_address= "192.168.77.97"
datalo = {  # json data to be published on MapAreas/Geofence topic
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [coordinates]},
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
print("mqtt")

#connect to MQTT broker
client.connect(broker_address, 1883)
client.loop_start()

if len(agv_pos) == 3:
    print(agv_pos)
    
    time.sleep(2)
    # Global to relative coordinates
    rxl =  globaltolocal_x(gx, agv_pos, gy)


    ryl =  globaltolocal_y(gx, agv_pos, gy)

    geofence_relative_coordinates={
            "geofence_relative_xcoordinates": rxl,
            "geofence_relative_ycoordinates":ryl
        }
    redis_con.json().set('geofence_relative_coordinates', Path.root_path(), geofence_relative_coordinates)

    for rx, ry in zip(rxl, ryl):
        coordinates.append([rx, ry])
    print("coordinates:", coordinates)
    

    client.publish("MapAreas/Geofence", payload=json.dumps(datalo))
    print("published to MapAreas")
    print("datalo",datalo)

    client.loop_stop()




