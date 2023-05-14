#!/bin/bash
echo "hello bash"
#sleep 5
echo "Connecting to MQTT!"
screen -S "syn" -dm bash -c 'exec bash'
screen -S "syn" -X stuff "source /home/synergieregion/Documents/Code/syn_redis/venv/bin/activate^M"
#MQTT CLIENT
screen -S "syn" -X stuff "python3 /home/synergieregion/Documents/Code/syn_redis/mqtt_relative.py^M"
sleep 10
screen -S "syn" -x -X screen bash -c "source /home/synergieregion/Documents/Code/syn_redis/venv/bin/activate^M; python3 /home/synergieregion/Documents/Code/syn_redis/main.py"
#Enlarge Shrink algorithm
screen -S "syn" -x -X screen bash -c "source /home/synergieregion/Documents/Code/syn_back_enlargeshrink/venv/bin/activate^M; python3 /home/synergieregion/Documents/Code/syn_back_enlargeshrink/main.py"
#Tag Detection algorithm
screen -S "syn" -x -X screen bash -c "source /home/synergieregion/Documents/Code/syn_back_tagdetection/venv/bin/activate^M; python3 /home/synergieregion/Documents/Code/syn_back_tagdetection/main.py"




