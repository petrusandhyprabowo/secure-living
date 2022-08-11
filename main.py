import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from src.controller.dashboard import Dashboard
# from src.controller import socketio
from flask_socketio import SocketIO,emit

from src.service.dashboard import dashboard_service

app = Flask('__name__',template_folder='templates',static_folder='assets')
cors = CORS(app, resources={r"/*": {"origins": "*"}})

Dashboard.register(app, route_base='/dashboard')

socketio = SocketIO(app)

@socketio.on('connect', namespace='/mysocket')
def my_socket(data):
    emit('my_response',data)

@app.route('/dashboard/mysocket', methods=['POST'])
def mysocket():
    requests = request.form
    dataZ = request.form['json']
    jsonx = json.loads(dataZ)
    data_json = jsonx['data']
    response = dashboard_service.insertPlateNumber(data_json)
    print('response',response)


    data = {}
    if requests:
        # top10TamuMasukPalingLama = dashboard_service.getTop10TamuMasukPalingLama()
        topTamuMasukPalingLama = dashboard_service.getTop5TamuMasukPalingLama()
        totalVisitorsInside = dashboard_service.getTotalVisitorInside()
        totalVisitorsThisWeek = dashboard_service.getVisitorsInBetween()
        totalVisitorsLastWeek = dashboard_service.getVisitorsInBetween(start='13 day', end='7 day')
        print('topTamuMasukPalingLama',topTamuMasukPalingLama)
        data = {
            'response': response,
            'status': response['status'],
            'licensePlate': response['licensePlate'],
            'topTamuMasukPalingLama': topTamuMasukPalingLama['data'],
            'totalVisitorsInside': totalVisitorsInside['data'],
            'totalVisitorsThisWeek': totalVisitorsThisWeek['data'],
            'totalVisitorsLastWeek': totalVisitorsLastWeek['data']
        }

    socketio.emit('my_response',data,namespace='/mysocket')
    return jsonify({'status': 200, 'message': 'success'})

if __name__ == '__main__':
    # app.run(host='0.0.0.0', debug=True, port=5000)
    socketio.run(app, host='0.0.0.0', debug=True, port=80)