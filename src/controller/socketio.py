from flask_socketio import SocketIO, emit

socketio = SocketIO()

def create_socketio(app):

    @socketio.on('my_ping', namespace='/')
    def ping_pong():
        emit('my_response')

    async_mode='eventlet'
    socketio.init_app(app,host='0.0.0.0', debug=True, port=5000)

    return app