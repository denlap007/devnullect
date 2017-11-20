#!/bin/sh
echo "Running bootscipt..." &&
echo "Substituting environment variables..." &&
envsubst < ${SRC_DIR}/config.ini > ${SRC_DIR}/config.ini &&
echo "Starting bot service..." &&
python ${SRC_DIR}/bot.py
