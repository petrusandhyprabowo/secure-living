from flask import Flask, jsonify, request, render_template, json
from flask_classy import FlaskView, route
from src.service.dashboard import dashboard_service
from flask_socketio import emit, SocketIO


class Dashboard(FlaskView):

    @route('/', methods=['GET', 'POST'])
    def homeDashboard(self):
        # top10TamuMasukPalingLama = dashboard_service.getTop10TamuMasukPalingLama()
        topTamuMasukPalingLama = dashboard_service.getTop5TamuMasukPalingLama()
        totalVisitorsInside = dashboard_service.getTotalVisitorInside()
        totalVisitorsThisWeek = dashboard_service.getVisitorsInBetween()
        totalVisitorsLastWeek = dashboard_service.getVisitorsInBetween(start='13 day', end='7 day')
        print('topTamuMasukPalingLama', topTamuMasukPalingLama)
        return render_template('index.html', data={
            'topTamuMasukPalingLama': topTamuMasukPalingLama['data'],
            'totalVisitorsInside': totalVisitorsInside['data'],
            'totalVisitorsThisWeek': totalVisitorsThisWeek['data'],
            'totalVisitorsLastWeek': totalVisitorsLastWeek['data']
        })

    @route('/saveLicensePlate', methods=['POST'])
    def saveLicensePlate(self):
        data = request.form['json']
        jsonx = json.loads(data)
        data_json = jsonx['data']
        message = dashboard_service.insertPlateNumber(data_json)
        print('Dari', data_json['camera_id'], 'deteksi plat nomor', data_json['results'][0]['plate'].upper(), 'jam',
              data_json['timestamp'])
        print('message', message)
        return jsonify({'status': 200, 'message': message})

    @route('/saveDestination', methods=['POST'])
    def saveDestination(self):
        data = request.json
        response = dashboard_service.updateVisitorDestination(data)
        topTamuMasukPalingLama = dashboard_service.getTop5TamuMasukPalingLama()
        return jsonify({'response': response, 'topTamuMasukPalingLama': topTamuMasukPalingLama['data']})

    @route('/updateInsertLockStatus', methods=['POST'])
    def updateInsertLockStatus(self):
        data = request.json
        response = dashboard_service.updateInsertLockStatus(data)
        return response

    # @route('/mysocket', methods=['POST'])
    # def mysocket(self):
    #     data = request.form['data']
    #     print('data',data)
    #     emit('my_response',data,namespace='/mysocket')
    #     return jsonify({'status': 200, 'message': 'success'})