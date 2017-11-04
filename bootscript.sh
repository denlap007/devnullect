#!/bin/sh
echo "Running bootscipt..." &&
echo "Substituting environment variables..." &&
envsubst < ${SRC_DIR}/bot.py > ${SRC_DIR}/bot.py &&
envsubst < ${SRC_DIR}/models/db.py > ${SRC_DIR}/models/db.py &&
echo "Starting bot service..." &&
python ${SRC_DIR}/bot.py
