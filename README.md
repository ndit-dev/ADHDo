# ADHDo - Your Dynamic To-Do List

ADHDo is a to-do list application designed to help my self cater the needs of my everyday life. I cloud not find a good to-do list that suited my needs, so I desided to create my own.
It is a docker container hosting a web app written in python flask intended to host locally in my home network.

I created this for my self, mainly hosting it on gitbub for the benefits of version control etc. But feel free to use it if you find it useful.


## Features

- **Dynamic Task Management**: Easily add, modify, or delete tasks based on changing priorities.
- **Category-based Organization**: Organize your tasks under specific categories for more structured planning.
- **Nightly Reset**: Tasks get automatically reset at night, ensuring a fresh start each day.
- **Recurring tasks (coming)** recurring on defined days of the week or month
- **Backup and restore** database in settings
- **light weight** built do be able to run on anything that can support containers. I plan to host it on a routerboard router.

## Installation and Setup

1. Clone the repo
2. run
```
docker build -t adhdo:latest .
docker run -p 80:80 adhdo:latest
```

## Notes to self...
while developing dont for get to update the requirements.txt by running `pip freeze > requirements.txt` to get the required dependencies from the virtual environment if changes have been made to that.
if dockerfile or requirements.txt has changed, or the container is not built on the local machine, run
```
docker-compose build
```
to start or restart the container with the latest changes use `docker-compose up` or `docker-compose up --build` to both build and start it in one step

### dont forget
to disable debug mode and develeopment mode before setting it production