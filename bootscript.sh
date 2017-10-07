#!/bin/sh
echo "Running bootscipt..." &&
echo "Substituting environment variables..." &&
envsubst < ${SRC_DIR}/bot.py > ${SRC_DIR}/bot.py &&
envsubst < ${SRC_DIR}/dbhelper.py > ${SRC_DIR}/dbhelper.py &&
echo "Starting bot service..." &&
python ${SRC_DIR}/bot.py
