"""
WSGI entry point for the application.
Only use with production WSGI server, such as Gunicorn.
"""

from src.app import app, socketio

if __name__ == "__main__":
    print("Booting WSGI server")
    socketio.run(app)

# from socketio import WSGIApp
# from src.app import app as flaskapp
# app = WSGIApp(flaskapp)
