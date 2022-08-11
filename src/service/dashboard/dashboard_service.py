import json

from src.service.dashboard import dashboard_query
from flask import jsonify


def insertPlateNumber(param):
    """Service yang menghandle insert plat nomor punya warga atau punya visitor, dan juga melakukan validasi
    arah (IN/OUT), kendaraan terkunci atau tidak, dan status pengamanannya aktif atau tidak.

    Deskripsi return code:
        1000 - Vehicle is locked, menandakan kendaraan berada dalam status terkunci dan tidak bisa keluar,
        jika mau keluar harus mengganti status menjadi terbuka

        200 - success

    :param param: didapat dari API SDK-PlateRecognize
    :return: dict, {'code': (1000/200), 'message': 'Vehicle is Locked'/('IN'/'OUT'), 'status': ('MEMBER'/'VISITOR'), 'licensePlate': 'B1990XXX', 'visitorId': (muncul jika bukan Warga)}
    """
    response = None
    # dapetin plat nomor ini itu Warga(Member) atau bukan
    isMember = dashboard_query.isMember(param['results'][0]['plate'])
    # check ini member atau bukan
    if isMember:
        # Kalau Warga masuk sini
        # query vehicle info yang di punya si Warga
        vehicleInfo = dashboard_query.getVehicleInfo(param['results'][0]['plate'])
        # query vehicle ini arah terakhirnya IN/OUT
        lastDirection = dashboard_query.getLastStatusDirection(vehicleInfo['vehicle_id'])
        # check kalau arah terakhirnya 'Masuk' dan status vehicle-nya 'Secure' dan status kuncinya terkunci
        # maka tidak bisa keluar dan mendapatkan return Warning
        if (lastDirection == 'IN' or lastDirection == 'None') and vehicleInfo['vehicle_status'] == 'Secure' and \
                vehicleInfo[
                    'vehicle_lock_status']:
            response = {'code': 1000, 'message': 'Locked', 'status': 'MEMBER',
                        'licensePlate': param['results'][0]['plate'].upper()}
        # check kalau arah terakhirnya 'Masuk' dan status vehicle-nya 'Secure' dan status kuncinya terbuka
        # maka bisa keluar
        elif (lastDirection == 'IN' or lastDirection == 'None') and vehicleInfo['vehicle_status'] == 'Secure' and not \
                vehicleInfo['vehicle_lock_status']:
            userId = dashboard_query.getUserIdFromLockVehicle(vehicleInfo['vehicle_id'],
                                                              vehicleInfo['vehicle_lock_status'])
            param['user_id'] = userId
            param['vehicle_id'] = vehicleInfo['vehicle_id']
            param['vehicle_history_status'] = 'OUT'
            dashboard_query.saveMemberHistory(param)
            response = {'code': 200, 'message': param['vehicle_history_status'], 'status': 'MEMBER',
                        'licensePlate': param['results'][0]['plate'].upper()}
        # check kalau arah terakhirnya 'Masuk' dan status vehicle-nya 'Free' maka bisa keluar
        elif (lastDirection == 'IN' or lastDirection == 'None') and vehicleInfo['vehicle_status'] == 'Free':
            param['user_id'] = vehicleInfo['user_id']
            param['vehicle_id'] = vehicleInfo['vehicle_id']
            param['vehicle_history_status'] = 'OUT'
            result = dashboard_query.saveMemberHistory(param)
            print('result', result)
            response = {'code': 200, 'message': param['vehicle_history_status'], 'status': 'MEMBER',
                        'licensePlate': param['results'][0]['plate'].upper()}
        # check kalau arah terakhirnya 'Keluar' dan status vehicle-nya 'Secure' maka update status
        # kuncinya(vehicle_lock_status) menjadi terkunci(True). auto lock.
        elif lastDirection == 'OUT' and vehicleInfo['vehicle_status'] == 'Secure':
            userId = dashboard_query.getUserIdFromVehicleHistory(vehicleInfo['vehicle_id'], 'OUT')
            dashboard_query.updateInsertLockStatus(userId, vehicleInfo['vehicle_id'], True, param['timestamp_local'])
            dashboard_query.updateVehicleLockStatus(vehicleInfo['vehicle_id'], True)
            param['user_id'] = userId
            param['vehicle_id'] = vehicleInfo['vehicle_id']
            param['vehicle_history_status'] = 'IN'
            result = dashboard_query.saveMemberHistory(param)
            response = {'code': 200, 'message': param['vehicle_history_status'], 'status': 'MEMBER',
                        'licensePlate': param['results'][0]['plate'].upper()}
        # check kalau arah terakhirnya 'Keluar' dan status vehicle-nya 'Free' maka masuk aja
        elif lastDirection == 'OUT' and vehicleInfo['vehicle_status'] == 'Free':
            userId = dashboard_query.getUserIdFromVehicleHistory(vehicleInfo['vehicle_id'], 'OUT')
            param['user_id'] = userId
            param['vehicle_id'] = vehicleInfo['vehicle_id']
            param['vehicle_history_status'] = 'IN'
            result = dashboard_query.saveMemberHistory(param)
            response = {'code': 200, 'message': param['vehicle_history_status'], 'status': 'MEMBER',
                        'licensePlate': param['results'][0]['plate'].upper()}
    # Kalau Tamu masuk sini
    else:
        lastVisitorDirection = dashboard_query.getLastStatusDirectionVisitor(param['results'][0]['plate'])
        if lastVisitorDirection == 'IN':
            param['visitor_status'] = 'OUT'
            destination = dashboard_query.getVisitorDestination(param['results'][0]['plate'])
            insertId = dashboard_query.saveVisitorHistory(param)
            dashboard_query.updateVisitorDestination(insertId['data'], destination)
            insertId['data'] = ''
        else:
            param['visitor_status'] = 'IN'
            insertId = dashboard_query.saveVisitorHistory(param)
        response = {'code': 200, 'message': param['visitor_status'], 'status': 'VISITOR',
                    'licensePlate': param['results'][0]['plate'].upper(), 'visitorId': insertId['data']}
    return response


def getTop10TamuMasukPalingLama():
    response = dashboard_query.getTop10TamuMasukPalingLama()
    for row in response['data']:
        # add color style
        if row['selisih'] > 86400:
            row['color'] = 'red'
        elif row['selisih'] > 43200:
            row['color'] = 'orange'
        else:
            row['color'] = 'gray'

        # convert second to day, hour, minute, and second
        string = ''
        second = row['selisih']
        if second < 60:
            string += str(second) + 'seconds'
        else:
            day = int(second / (3600 * 24))
            hour = int((second % (3600 * 24)) / 3600)
            minute = int((second % (3600 * 24)) % 3600 / 60)
            if day: string += str(day) + (' days ' if day > 1 else ' day ')
            if hour: string += str(hour) + (' hours ' if hour > 1 else ' hour ')
            if minute: string += str(minute) + (' minutes ' if minute > 1 else ' minute ')
        row['selisih'] = string

    return response


def getTop5TamuMasukPalingLama():
    response = dashboard_query.getTop5TamuMasukPalingLama()
    # nullData = [{'color':'','date':'','license_plate':'','destination':'','camera':'','selisih':''}]
    for row in response['data']:
        # add color style
        if row['selisih'] > 86400:
            row['color'] = 'red'
        elif row['selisih'] > 43200:
            row['color'] = 'orange'
        else:
            row['color'] = 'gray'

        # convert second to day, hour, minute, and second
        string = ''
        second = row['selisih']
        if second < 60:
            string += str(second) + 'seconds'
        else:
            day = int(second / (3600 * 24))
            hour = int((second % (3600 * 24)) / 3600)
            minute = int((second % (3600 * 24)) % 3600 / 60)
            if day: string += str(day) + (' days ' if day > 1 else ' day ')
            if hour: string += str(hour) + (' hours ' if hour > 1 else ' hour ')
            if minute: string += str(minute) + (' minutes ' if minute > 1 else ' minute ')
        row['selisih'] = string

    return response


def getTotalVisitorInside():
    response = dashboard_query.getTotalVisitorInside()
    response['data'] = response['data'][0]['today_visitors']

    return response


def getVisitorsInBetween(start='6 day', end='0 day'):
    response = dashboard_query.getVisitorsInBetween(start, end)
    response['data'] = response['data'][0]['count_visitors']

    return response


def updateVisitorDestination(param):
    response = dashboard_query.updateVisitorDestination(param['id'], param['destination'])
    return response


def updateInsertLockStatus(data):
    import datetime;
    timestamp = datetime.datetime.now()
    response = dashboard_query.updateInsertLockStatus(data['userId'], data['vehicleId'], data['lockStatus'],
                                                      timestamp)
    dashboard_query.updateVehicleLockStatus(data['vehicleId'], data['lockStatus'])
    return response
