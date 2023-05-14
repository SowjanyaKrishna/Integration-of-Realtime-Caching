import paho.mqtt.client as mqtt
import time
import json
import queue
import redis 
from redis.commands.json.path import Path
from coordinateconversion import globaltolocal_x
from coordinateconversion import globaltolocal_y

#MQTT BROKER CONFIGURATION
broker_address= "192.168.77.97"
#Redis CONFIGURATION
redis_con = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
#New Client instance
client= mqtt.Client("hello")  # client ID "mqtt-test"
Naise_tag= "naise/tag/041E"

gx = []  # global x coordinates for geofence
gy = []  # global y coordinates for geofence
agv_pos = []  # position of agv
tag_pos = []
coordinates = []  # variable to add coordinates to maparea topic 1)relative to agv 2)to enlarge and shrink
res_topic= "naise/response/geofence"


result= redis_con.json().get('user_input')
#Geofence_id= redis_con.json().get('user_input',Path('.Geofence_id'))
Agv_name= redis_con.json().get('user_input',Path('.Agv_name'))
Naise_tag= redis_con.json().get('user_input',Path('.Naise_tag'))
Agv_topic= redis_con.json().get('user_input',Path('.Agv_topic'))
print("result",result)

Geofence_id= "Geofence"
Agv_Topic="naise/tag/aagv7"

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


def on_connect(client, userdata, flags, rc): #pub sub mqtt topics
    print(f"Connected with result code {rc}")
    client.subscribe(Naise_tag)
    client.subscribe("naise/response/geofence")
    time.sleep(1)
    client.publish("naise/request/geofence", payload=json.dumps({"id": Geofence_id}))
    client.subscribe(Agv_topic)

def on_message(client, userdata, msg): #decoding payload from subscribed topic
    # print("--------Message---------")
  
    if msg.topic == Agv_topic: #AGV topic
        m_agva = str(msg.payload.decode("utf-8", "ignore"))
        m_agv = json.loads(m_agva)
        pos= m_agv["pose"]
        global agv_pos
        xs = pos["x"]
        ys = pos["y"]
        ang = pos["angle"]
        agv_position = [xs, ys, ang]
        #stream agv data to redis
        print("agv_pos",agv_position)
        agv_pos={
            "agv_xs":xs,
            "agv_ys":ys,
            "agv_angle":ang
        }
        redis_con.xadd("agv_pos_tag", agv_pos)
        


    if msg.topic == res_topic: #geofence coordinates
        m_decode = str(msg.payload.decode("utf-8", "ignore"))
        m_in = json.loads(m_decode)
        print("m_in",m_in)
        map = m_in["geometry"]
        global gx, gy
        glo_geo = map["coordinates"]
        gxs, gys = zip(*glo_geo[0])  #global coordinates
        print(gys)


        geofence_xcoordinates={}
        for x in range(len((gxs))):
            geofence_xcoordinates["geofence_xcoordinate{0}".format(x)] = gxs[x]
        print("x",geofence_xcoordinates)
        
        geofence_ycoordinates={}
        for y in range(len((gys))):
            geofence_ycoordinates["geofence_ycoordinate{0}".format(y)] = gys[y]
        print("y",geofence_ycoordinates)
        
        #stream geofence coordinates to redis
        #redis_con.xadd("geofence_coordinates", geofence_coordinates)
        redis_con.xadd("geofence_xcoordinates", geofence_xcoordinates)
        redis_con.xadd("geofence_ycoordinates", geofence_ycoordinates)
        

        
 
    elif msg.topic == Naise_tag: #Naise Tag 
        m_tag_raw= str(msg.payload.decode("utf-8","ignore"))
        m_tag= json.loads(m_tag_raw)
        ver= m_tag["header"]["version"]
        if ver == "v1.1":
            pos= m_tag["pose"]
            tag_x=pos["x"]
            tag_y=pos["y"]
            tag_pos=[tag_x,tag_y]
            tag_pos={
                "tag_x":tag_x,
                "tag_y":tag_y
            }
            print("tag_pos",tag_pos)
            redis_con.xadd("tag_pos", tag_pos)



def on_log(client, userdata, level, buf):
    print("log: ", buf)


def geofence_relative_agv():  
    time.sleep(2)

    if len(agv_pos) == 3:
        print(agv_pos)
        
        time.sleep(2)
        global rxl
        global ryl
        # Global to relative coordinates
        rxl =  globaltolocal_x(gx, agv_pos, gy)
        #print("rxl",rxl)

        ryl =  globaltolocal_y(gx, agv_pos, gy)
        #print("ryl",ryl)
        

        for rx, ry in zip(rxl, ryl):
            coordinates.append([rx, ry])
        #print("coordinates:", coordinates)
        
        client.publish("MapAreas/Geofence", payload=json.dumps(datalo))
        client.publish("uhhg", payload=json.dumps({"id": "jhugaic"}))
        print("published to MapAreas")


def initclient():
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_log=on_log

    #connect to MQTT broker
    client.connect(broker_address, 1883)


    client.loop_forever()