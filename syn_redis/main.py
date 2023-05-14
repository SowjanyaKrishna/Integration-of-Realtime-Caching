import omlox_listener as omlox
import mqtt_client as mqttcon
import mqtt_tag as mqtttag
from omlox_listener import listen

#Call model to connect to Omlox listener
#omlox.create_folder()
#omlox.setup_csv()
#omlox.asyncio.run(listen())


#Call model to connect to MQTT
#mqttcon.initclient()
#call model to send mqtt data to redis-cache
#mqttcon.send_dataredis()
#Call model to connect to MQTT for Tag detection
mqtttag.initclient()


