from flask import Flask

from src.socketio.chat import ChatNamespace
from src.socketio.forwarding import ForwardingNamespace

# Dictionary to store the clients
# key: client id -> list[session id]


def attach_namespaces(app: Flask) -> None:
    """
    Attach all socketIO namespaces to the app
    :param app: The Flask app to register the endpoints to
    :return: None
    """
    # Register the namespaces
    app.socketio.chat_namespace = ChatNamespace('/chat')
    app.socketio.on_namespace(app.socketio.chat_namespace)
    app.socketio.forwarding_namespace = ForwardingNamespace('/forward', app)
    app.socketio.on_namespace(app.socketio.forwarding_namespace)
