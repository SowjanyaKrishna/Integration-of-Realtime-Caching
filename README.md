# Integration of Realtime Caching in a Dynamic Geofence System for Indoor Logistics

Geofences are virtual zones used to control and influence the movement of driverless
transport systems, such as AGVs. Geofences are critical to the functioning of modern
indoor logistic systems. To control and influence the AGVs' logistical flow, they establish
virtual zones on internal maps, limiting their operation within a specified area and
preventing collisions with objects and other AGVs. The location data of these AGVs is
published using message protocols.
Real-time monitoring of geofences is essential to adaptively change them during runtime
and place them correctly around moving AGVs. This requires constant monitoring of the
current position of all AGVs. Real-time locating systems such as GPS or RFID systems
publish location information using message protocols like MQTT, enabling real-time
location monitoring, and tracking across numerous devices and systems. However, an
event-driven approach like MQTT may not be suitable for applications that require more
synchronous or real-time connectivity with other devices and systems. Additional tools
or middleware may be required to buffer and handle the location data in a more organized
and predictable manner to ensure efficient and prompt use of location data.
This paper aims to integrate a real-time caching system into an existing system for
dynamic geofences used in indoor logistic systems, which are often based on driverless
transport systems. The current geofence system uses MQTT messages to receive the
locations of AGVs in real-time, but it faces challenges in combining with other tools that
do not work asynchronously. The proposed solution is to split the system into two
applications - one that receives MQTT messages and stores them in a cache, and
another that runs a Flask web server that reads information from the cache. The
integration of the real-time caching system improves the responsiveness and scalability
of the system and enables a visualization front end to receive the latest coordinates of
geofences and AGVs via a REST API.

## Objective

The goal of this project is to identify and integrate a real-time caching system that
stores MQTT messages for other processes to read concurrently and in real-time. To
ensure that multiple processes can read from the cache concurrently and in real-time,
use of thread-safe data structure such as a thread-safe queue or a thread-safe
dictionary must be implemented. Each process needs to read from the cache create a
separate thread that reads messages from the queue and processes them. By splitting
the geofence system into two applications, that they run independently of each other
and avoid blocking each other due to the Global Interpreter Lock (GIL). This allows to decouple the MQTT processing from the Flask web server and allows them to run
independently of each other. It also allows multiple processes to read from the cache
concurrently and in real-time, improving the scalability and responsiveness of the
system.

## System Architecture 

![image](https://github.com/SowjanyaKrishna/Integration-of-Realtime-Caching/assets/128833366/54c8225d-8a5d-4892-a167-69e4d1ae7688)

In above Figure, the implemented architecture can be seen with all modules defined. The
backend module is implemented in Flask python framework. All the communication
towards the remaining modules is initiated through this module. The database used is
SQLite as a backend database. The client side (User interface) is implemented on
Vuejs. The user input from the frontend is communicated to the SQLite database using
the library SQLAchemy which enables Object-Relational Mapping (ORM). This
practically means that the operations done on SQLite database can be initiated from
flask using Python queries. This speeds up the process of converting SQL queries into
python. The AGV’s (Rexroth active shuttle) communicate to the NAiSE server, an
MQTT broker is implemented as communication protocol to enable bidirectional
communication. To overcome the issue of multithreading, Redis real-time caching
system is integrated to store MQTT messages and support concurrent reads. When
the connect API is called, the flask backend launches a subprocess that executes the
bash script, which launches three Python applications and the redis-cache that was
launched on a Docker container simultaneously. The MQTT-client application
establishes a connection with the MQTT broker, subscribes to all the messages, and streams to the Redis cache, all the necessary data in specific data types. The
Geofence Enlarge Shrink and Tag Detection applications read the necessary streamed
data from the Redis cache and publish the output back to the frontend in real-time and
on HTTP requests. NAiSE GUI rendered from NAiSE server which provides as 3D
map of the ARENA with real-time movements of the AGV’s, Tags and with a feature to
draw polygon shaped geofences.
