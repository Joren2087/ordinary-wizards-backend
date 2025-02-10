# Ordinary Wizards Backend

## By Joren2087
#### Created at the University Of Antwerp, 2024 for the course Programming Project Databases (2nd Bachelor's degree in Computer Science)

## This is only the backend of the original project for illustrative purposes. The original frontend is not included, but may be referenced by the original documentation

## Introduction
Web-based 3D idle game using THREE.js, Flask, PostgreSQL, SQLAlchemy, SocketIO & Alembic. Made by 6 students for the course Programming Project Databases at the University of Antwerp.

Ordinary Wizards is a web-based 3D idle game where you are a magical wizard that can build his own island, mine crystals & gems, progress through multiple levels and fight other players in a real-time multiplayer battle. 
With the power of WebGL, the game is completely rendered in 3D and can be played on any device that supports a modern web browser. 
Craft magical gems to boost your buildings, upgrade your island, beat other players and become the most powerful wizard in the game!

Full handbook can be found at [USER_MANUAL.md](docs/USER_MANUAL.md)

## Project setup
The project is divided into two main parts: the backend and the frontend. The backend is a RESTful API built using Flask, SQLAlchemy, flask-restful and flask-migrate, that communicates with an external PostgreSQL database.
The frontend is a multi-page (landing, login, register & index pages) web application built using jQuery, THREE.js, SocketIO and out-of-the-box JavaScript, CSS & HTML.

## Installation & running debug server
Execute all the following commands from the root directory of the project.
1. Setup a Python (3.10+) virtual environment and install the required packages using the following commands:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2. Setup a PostgreSQL database and fill in the connection details in the (user created) `.env` file:
    ```bash
    APP_POSTGRES_HOST=127.0.0.1
    APP_POSTGRES_PORT=5432
    APP_POSTGRES_DATABASE=ordinary_wizards
    APP_POSTGRES_USER=ordinary_wizards
    APP_POSTGRES_PASSWORD=<password>
    ```
3. Setup app environment variables as well in the `.env` file:
    ```bash
    APP_BIND=127.0.0.1
    APP_HOST=127.0.0.1:5000
    APP_HOST_SCHEME=http
    APP_SECRET_KEY=<secret_key> # optional
    APP_NAME=Ordinary Wizards
    APP_JWT_SECRET_KEY=jwtRS256.key
    ```
    For a full, detailed list of environment variables, see the [.env.md](docs/ENV.md) file.

4. Generate secret `jwtRS256.key` using the (`keygen.py`)[keygen.py] script:
    ```bash
    python3 keygen.py
    ```

5. Make sure to run the following command to create the database tables:
    ```bash
    flask --app src.app db upgrade
    ```
   
6. Run the Flask debug server using the following command:
    ```bash
    python3 -m src.app
    ```
   
**Important note when running Gunicorn WSGI server**: Gunicorn does not support WebSocket connections (as the loadbalancing algorithm does not work with WebSockets), which this app requires.
In order to fix this, you must run gunicorn with only **1 worker** and use threading for workload spread. 

## Documentation

Please refer to [DOCUMENTATION.md](docs/DOCUMENTATION.md) for more information about the project structure, the API, the database schema and the 3D visuals.

## Intellectual Property

All assets used in this project are free to use. You can find the original sources of the used assets as well as their authors in the [credits.txt](static/credits.txt) file.