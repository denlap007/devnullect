# devnullect
Repo for devnullect telegram bot

## How to run the bot dockerized in one command

.. code:: shell
docker run -d --name devnullect-bot -v </host/path>:/src/db -e BOT_TOKEN=<YOUR_TOKEN> denlap/devnullect

where </host/path> is a path to your host to persist data if you remove the container, i.e. /home/db
