#!/bin/bash
echo "hello bash"
docker start redis-cache
#Running Frontend module
cd /home/synergieregion/Documents/Code/syn_front-front_final
npm run serve  & 
#Running Backend module
cd /home/synergieregion/Documents/Code/syn_back_flask
export FLASK_APP=syn_back.py
flask run 
