# devnullect
Repo for telegram bot that manages to-do lists with group support.

## How to run the bot
The bot is configured to run **dockerized in a container**. Current setup includes a **MySQL** database container, a **phpMyAdmin** container for database manipulation and the **bot app** container.

You will **require installed**:
* docker v1.13.0+
* docker-compose v1.10.0+

In the _compose_ directory, the **.env file** contains the configuration information necessary. The variables are self-descriptive and all their values are mandatory for the app to execute.

In order to start the application, from the _**compose** directory_ run:
```shell
docker-compose up -d
```

#### To Do
* Update wiki
* add urls with nothing as prefix
* create profile pic :)
