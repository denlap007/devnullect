# devnullect
Repo for devnullect telegram bot

## How to run the bot dockerized in one command

```shell
docker run -d --name devnullect-bot -v </host/path>:/src/db -e BOT_TOKEN=<YOUR__BOT_TOKEN> denlap/devnullect
```
where
* </host/path> is a path to your host to persist data if you remove the container, i.e. /home/db
* <YOUR__BOT_TOKEN> is the BOT_TOKEN you were given when created the bot


#### To Do
* Add group support
* Update documentation for deployment (old docker method legacy)
* Update wiki
* add urls with www or nothing as prefix
* support more languages
* create profile pic :)
