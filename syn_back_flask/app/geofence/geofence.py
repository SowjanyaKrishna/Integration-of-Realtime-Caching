import app
from app.geofence import bp
from app.models import SpeedRange, SpeedRangeSchema, User, MqttTopics, MqttTopicsSchema
from app import db
from flask import jsonify, request, Flask, session, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import shapely.geometry
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from shapely import geometry
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import json
import time
import math
import threading
import decimal
from app.geofence.enlargeshrink import Enlargeshrink
from app.geofence.tagdetection import Tag_detection
from app.geofence.coordinateconversion import globaltolocal_x
from app.geofence.coordinateconversion import globaltolocal_y
import queue
import redis
from redis.commands.json.path import Path
import subprocess
from subprocess import Popen, PIPE


'REDIS CONNECTION CONFIGURATION'
redis_con = redis.Redis(host="127.0.0.1", port=6379, db=0)


"""  
It takes the data from the Speed Range table in frontend and adds it to the database.
  :return: The data is being returned as a json object."""


@bp.route("/addspeeddata", methods=["POST"])
def create_form():

    data = request.get_json() or {}
    upperlimit = float(data["upperlimit"])
    lowerlimit = float(data["lowerlimit"])
    offset = float(data["offset"])

    print(upperlimit)
    print(lowerlimit)
    print(offset)

    data1 = SpeedRange(upperlimit=upperlimit, lowerlimit=lowerlimit, offset=offset)
    db.session.add(data1)
    db.session.commit()

    print("DONE")
    return jsonify(data)


"""
It takes a edited speedrange as json object from the front end, and updates the database with the new values.
  :return: The data is being returned as a JSON object."""


@bp.route("/editspeed", methods=["PUT"])
def editSpeedRange():
    data = request.get_json() or {}
    id = int(data["id"])
    print("id:", id)
    speedrange = SpeedRange.query.get(id)
    speedrange.upperlimit = float(data["upperlimit"])
    speedrange.lowerlimit = float(data["lowerlimit"])
    speedrange.offset = float(data["offset"])
    print("range:", speedrange.upperlimit, speedrange.lowerlimit, speedrange.offset)
    db.session.commit()

    print("SpeedRange Edited Succesfully !!")
    return jsonify(data)


""" 
  It deletes a row from the database based on the id passed in the request.
  :return: The message is being returned.
"""


@bp.route('/deletespeed/<int:speed_id>', methods=['DELETE'])
def delete_speed(speed_id):

    speedrange= SpeedRange.query.get(speed_id)
    db.session.delete(speedrange)
    db.session.commit()

    message = {"message": "Speed row deleted successfully"}
    return jsonify(message)


"""
 It queries the database for all the data in the SpeedRange table, then it uses the SpeedRangeSchema
  to serialize the data into a JSON object, and then it returns the JSON object.
"""


@bp.route("/getSpeedTabledata", methods=["GET"])
def get_speedtabledata():
    tabledata = SpeedRange.query.all()
    tabledata_schema = SpeedRangeSchema(many=True)
    output = tabledata_schema.dump(tabledata)
    return jsonify(output)


"""
  It deletes all the rows in the SpeedRange table.
  :return: a json object with a message.
"""


@bp.route("/Clearspeedrangetable", methods=["GET"])
def clear_speedrangetable():
    dbdata = SpeedRange.query.delete()
    db.session.commit()
    message = {"message": "Speed table deleted successfully"}
    return jsonify(message)


"""
  It takes the MQTT topics as  JSON object from a POST request triggered by frontend, and then adds it to a database table
  :return: The data that is being returned is the data that is being sent to the server.
"""


@bp.route("/tablemqtt", methods=["POST"])
def create_mqtt_table():
    mqtt_data = request.get_json() or {}
    AGVName = str(mqtt_data["AGVName"])
    AGVTopic = str(mqtt_data["AGVTopic"])
    GeofenceId = str(mqtt_data["GeofenceId"])
    NaiseTag = str(mqtt_data["NaiseTag"])

    print(mqtt_data)

    print(AGVName)
    print(AGVTopic)
    print(GeofenceId)
    print(NaiseTag)

    mqtt_data1 = MqttTopics(AGVName=AGVName, AGVTopic=AGVTopic, GeofenceId=GeofenceId, NaiseTag=NaiseTag)

    db.session.add(mqtt_data1)
    db.session.commit()

    print("MQTT update DONE")
    return jsonify(mqtt_data)


"""
It takes a edited row from MQTT table as json object from the front end, and updates the database with the new values.
  :return: The data is being returned as a JSON object.
"""


@bp.route("/editmqtt", methods=["PUT"])
def editSMqttTable():
    data = request.get_json() or {}
    id = int(data["id"])
    print("id:", id)
    mqtt_tabledata = MqttTopics.query.get(id)
    mqtt_tabledata.AGVName = str(data["AGVName"])
    mqtt_tabledata.AGVTopic = str(data["AGVTopic"])
    mqtt_tabledata.GeofenceId = str(data["GeofenceId"])
    mqtt_tabledata.NaiseTag = str(data["NaiseTag"])
    print(
        "mqtt tpoics:",
        mqtt_tabledata.AGVName,
        mqtt_tabledata.AGVTopic,
        mqtt_tabledata.GeofenceId,
        mqtt_tabledata.NaiseTag,
    )
    db.session.commit()

    print("Mqtt tabledata Edited Succesfully !!")
    return jsonify(data)




    

@bp.route('/mqttselectedrow',methods=['POST'])
def mqtt_row_selection():
    data = request.get_json() or {}
    i_d = data['clickedid']
    id= i_d[0]
    col=(int(id)-1)
    
    "Query function for MQTT Topic with id posted here"

    agv_name= db.session.query(MqttTopics.AGVName).all()
    agvname=agv_name[col]
    global Agv_name
    Agv_name= agvname[0]
    print("AGVname=", agvname[0])

    agv_topic= db.session.query(MqttTopics.AGVTopic).all()
    agvtopic= agv_topic[col]
    global Agv_topic
    Agv_topic= agvtopic[0]
    print("AGVtopic=", agvtopic[0])

    geofence_id= db.session.query(MqttTopics.GeofenceId).all()
    geofenceid= geofence_id[col]
    global Geofence_id
    Geofence_id= geofenceid[0]
    print("GeofenceId=", geofenceid[0])

    naise_tag= db.session.query(MqttTopics.NaiseTag).all()
    naisetag= naise_tag[col]
    global Naise_tag
    Naise_tag= naisetag[0]
    print("NaiseTag=", naisetag[0])

    return jsonify(data)


"""
  It deletes a row from the database based on the id passed in the request
  :return: The return value of the function is a json object.
"""
@bp.route('/deletemqtt/<int:mqtt_id>', methods=['DELETE'])
def delete_mqtt(mqtt_id):

    mqtt_row = MqttTopics.query.get(mqtt_id)
    print("id:", id)
    
    db.session.delete(mqtt_row)
    db.session.commit()

    message = {"message": "Mqtt row deleted successfully"}
    return jsonify(message)


"""
  It queries the MqttTopics table in the database, then uses the MqttTopicsSchema to serialize the
  data into JSON format, and then returns the JSON data.
"""


@bp.route("/getMqttTabledata", methods=["GET"])
def get_mqtttabledata():
    tabledata = MqttTopics.query.all()
    tabledata_schema = MqttTopicsSchema(many=True)
    output = tabledata_schema.dump(tabledata)
    return jsonify(output)


"""
  It takes a value from a javascript function and stores it in a global variable.
  :return: The value of the zone_offset_value variable.
"""


@bp.route("/getZoneOffset", methods=["POST"])
def Zone_Offset():
    zone_data = request.get_json() or {}
    print(zone_data)
    global zone_offset_value
    zone_offset_value = float(zone_data["zoneoffset"])

    print(zone_offset_value)

    return jsonify(zone_offset_value)


zone_offset_value = 0.2


"""
On clicking "connect" in the frontend, thid api function is excecuted
consists- MQTT connection, 
          coordinateconversion function call,
          threading calls for function enlargeshrink and tagdetection

"""

@bp.route("/Connect", methods=["POST"])
def connection():
    "query functions for speedrange table"
    upp = db.session.query(SpeedRange.upperlimit).all()
    upper = []
    for x in upp:
        redis_con.lpush("upperlimit", x[0])
        upper.append(x[0])
    print("upperlimit=", upper)

    low = db.session.query(SpeedRange.lowerlimit).all()
    lower = []
    for y in low:
        redis_con.lpush("lowerlimit", y[0])
        lower.append(y[0])
    print("lowerlimit=", lower)

    off = db.session.query(SpeedRange.offset).all()
    off_set = []
    for z in off:
        redis_con.lpush("off_set", z[0])
        off_set.append(z[0])
    print("offset=", off_set)

    """
    Store data into redis-cache
    """

    redis_con.set("Agv_topic", Agv_topic)
    redis_con.set("Agv_name", Agv_name)
    redis_con.set("Naise_tag", Naise_tag)
    redis_con.set("Geofence_id", Geofence_id)

    user_input={
        'Agv_name' : Agv_name,
        'Agv_topic' : Agv_topic,
        'Naise_tag' : Naise_tag,
        'Geofence_id' : Geofence_id,
        'upperlimit' : upper,
        'lowerlimit' : lower,
        'off_set' : off_set,
        'zone_offset_value': zone_offset_value
    }
    
    redis_con.json().set('user_input', Path.root_path(), user_input)
    print("hello flask")
    #start bash code to run mqtt, tag detection and enlargeshrink python application
    subprocess.call('/home/synergieregion/Documents/Code/bash/entry_screens.sh')
    #subprocess.call('/home/synergieregion/Documents/Code/bash/tag.sh')#to run only tag detection
    hello = {"message": "Connected"}
    return jsonify(hello)
    

@bp.route('/TagDetection', methods=['GET'])
def Tag_Detection():

  warning= redis_con.get('warning')
  #warning_status= warning.decode()
  warning_status= str(warning)
  print("get_action", warning_status)
  action={"warning": warning_status}
  return jsonify(action)



@bp.route("/Disconnect", methods=["POST"])
def disconnect():
      # t2.join()
  #client.loop_stop()
  #client.disconnect()
  print("client disconnected")
  bye = {"message": "Diconnected"}
  return (bye)

