#!/bin/sh
echo "Running bootscipt..." &&
echo "Substituting environment variables..." &&
envsubst < ./bot.py > /dev/null &&
echo "Starting bot service..." &&
python ./bot.py
