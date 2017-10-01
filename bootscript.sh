#!/bin/sh
echo "Running bootscipt..." &&
echo "Substituting environment variables..." &&
envsubst < ./bot.py > ./bot.py &&
echo "Starting bot service..." &&
python ./bot.py
