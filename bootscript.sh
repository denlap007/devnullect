#!/bin/sh
echo "Running bootscipt..." &&
echo "Substituting environment variables..." &&
envsubst < ${SRC_DIR}/conf.ini > ${SRC_DIR}/conf.ini &&
echo "Starting bot service..." &&
python ${SRC_DIR}/bot.py
