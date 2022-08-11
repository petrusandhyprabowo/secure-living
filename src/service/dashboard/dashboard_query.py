import json
import numpy
from psycopg2.extras import RealDictCursor

from src.config import dbcon


def get_plate_number_history():
    """Get all Data from public.ocr_history.

    Ini dulu digunakan waktu masih pakai Database testing pertama kali
    :return: dict
    """
    conn = dbcon.get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM public.ocr_history ORDER BY "timestamp" DESC;')
    books = cur.fetchall()
    cur.close()
    conn.close()
    return books


def insertPlateNumber(params):
    """Insert data dari API SDK-Plate Recognizer ke public.ocr_history.

    Ini dulu digunakan waktu masih pakai Database testing pertama kali.

    :param params: dict, data yang didapat dari API SDK-Plate Recognizer
    :return: dict
    """
    conn = None
    cur = None
    errorMessage = 'Insert Success'
    status = 200
    try:
        query = 'INSERT INTO public.ocr_history (tenant_id, cluster_id, "timestamptz", license_plate, vehicle_type, box, image_path, camera, direction, status, isdelete) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'
        conn = dbcon.get_db_connection()
        cur = conn.cursor()
        cur.execute(query, (
            '1', '1', params['timestamp_local'], params['results'][0]['plate'].upper(),
            params['results'][0]['vehicle']['type'],
            json.dumps(params['results'][0]['box']), params['filename'], params['camera_id'],
            # params['results'][0]['direction']
            'IN', numpy.random.choice(['VISITOR'], size=1)[0], '0'))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as error:
        errorMessage = error
        status = 500
    finally:
        cur.close()
        conn.close()
        return {'code': status, 'message': errorMessage}


def getTop10TamuMasukPalingLama():
    """Get top 10 tamu yang paling lama berada di dalam dari public.ocr_history.

    Ini dulu digunakan waktu masih pakai Database testing pertama kali.

    :return: dict
    """
    conn = None
    cur = None
    errorMessage = 'Success'
    status = 200
    data = ''
    try:
        conn = dbcon.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "select xx.license_plate, xx.camera, to_char(xx.\"timestamptz\", 'TMDD TMMonth YYYY HH:MI') as \"date\", extract(epoch from xx.selisih)::int as selisih, xx.destination from ( SELECT distinct on(license_plate) license_plate, camera, direction, status, \"timestamptz\", current_timestamp - \"timestamptz\" as selisih, destination FROM public.ocr_history where status = 'VISITOR' order by license_plate,\"timestamptz\" desc) xx where xx.direction = 'IN' order by xx.selisih desc limit 10")
        data = cur.fetchall()
    except Exception as error:
        errorMessage = error
        status = 500
    finally:
        cur.close()
        conn.close()
    return {'code': status, 'message': errorMessage, 'data': data}


def getTop5TamuMasukPalingLama():
    """Get top 5 tamu yang paling lama berada di dalam sampai saat ini dari table public.visitors
    :return: dict
    """
    conn = None
    cur = None
    errorMessage = 'Success'
    status = 200
    data = ''
    try:
        conn = dbcon.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "select x.visitor_lisence_plate as license_plate,x.visitor_camera as camera,x.visitor_destination as destination,to_char(x.create_date, 'TMDD TMMonth YYYY HH:MI') as date,extract(epoch from x.selisih)::int as selisih from (select distinct on(visitor_lisence_plate) visitor_lisence_plate,visitor_destination,visitor_camera,create_date,current_timestamp-create_date as selisih,visitor_status from public.visitors order by visitor_lisence_plate, create_date desc, visitor_id desc) x where x.visitor_status = 'IN' order by selisih desc limit 5;")
        data = cur.fetchall()
    except Exception as error:
        errorMessage = error
        status = 500
    finally:
        cur.close()
        conn.close()
    return {'code': status, 'message': errorMessage, 'data': data}


def getVisitorsInBetween(start='6 day', end='0 day'):
    """Get data jumlah visitor dalam range waktu (start, end) yang kita tentukan sendiri dari table public.visitors

    :param start: str, hari awal, berapa hari yang lalu dari hari ini. The default is '6 day'.
    :param end: str, hari akhir bisa berapa hari yang lalu dari hari ini atau sampai hari ini. The default is '0 day', this is today.
    :return: dict
    """
    conn = None
    cur = None
    errorMessage = 'Success'
    status = 200
    data = ''
    try:
        conn = dbcon.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "select count(x.visitor_lisence_plate) as count_visitors from (select distinct on(visitor_lisence_plate) visitor_lisence_plate,visitor_destination,visitor_camera,create_date,current_timestamp-create_date as selisih,visitor_status from public.visitors order by visitor_lisence_plate desc, create_date desc) x where x.create_date::date between (current_timestamp - interval %(start)s)::date and (current_timestamp - interval %(end)s)::date;",
            {'start': start, 'end': end})
        data = cur.fetchall()
    except Exception as error:
        errorMessage = error
        status = 500
    finally:
        cur.close()
        conn.close()
    return {'code': status, 'message': errorMessage, 'data': data}


def getTotalVisitorInside():
    """Get total visitor yang berada di dalam dari table public.visitors
    :return: dict
    """
    conn = None
    cur = None
    errorMessage = 'Success'
    status = 200
    data = ''
    try:
        conn = dbcon.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "select count(x.visitor_lisence_plate) as today_visitors from (select distinct on(visitor_lisence_plate) visitor_lisence_plate,visitor_destination,visitor_camera,create_date,current_timestamp-create_date as selisih,visitor_status from public.visitors order by visitor_lisence_plate desc, create_date desc, visitor_id desc) x where x.visitor_status = 'IN' and to_char(x.create_date, 'TMDD TMMonth YYYY') = to_char(current_timestamp, 'TMDD TMMonth YYYY');")
        data = cur.fetchall()
    except Exception as error:
        errorMessage = error
        status = 500
    finally:
        cur.close()
        conn.close()
    return {'code': status, 'message': errorMessage, 'data': data}


def isMember(licensePlate):
    """Check apakah plat nomor ini punya warga atau bukan dari table public.vehicles.

    :param licensePlate: str, plate nomor hasil scan camera
    :return: bool, True jika punya warga, False jika tidak terdaftar
    """
    conn = None
    cur = None
    # errorMessage = 'Success'
    # status = 200
    data = ''
    try:
        conn = dbcon.get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "select count(vehicle_lisence_plate)::int::boolean FROM public.vehicles where vehicle_lisence_plate = %(license_plate)s;",
            {'license_plate': licensePlate.upper()})
        data = cur.fetchone()[0]
    except Exception as error:
        # errorMessage = error
        # status = 500
        print('isMember error:', error)
    finally:
        cur.close()
        conn.close()
    return data


def saveMemberHistory(params):
    """Insert data dari API SDK-Plate Recognizer ke table history member(public.vehicle_history).

    :param params: dict, data yang didapat dari API SDK-Plate Recognizer
    :return: dict, {'code': status, 'message': errorMessage}
    """
    conn = None
    cur = None
    errorMessage = 'Insert Success'
    status = 200
    try:
        query = 'INSERT INTO public.vehicle_history (vehicle_history_status, vehicle_history_snapshot_path, vehicle_history_box, vehicle_id, user_id, camera, create_date) VALUES(%(vehicle_history_status)s, %(vehicle_history_snapshot_path)s, %(vehicle_history_box)s, %(vehicle_id)s, %(user_id)s, %(camera)s, %(create_date)s);'
        conn = dbcon.get_db_connection()
        cur = conn.cursor()
        cur.execute(query, {'vehicle_history_status': params['vehicle_history_status'],
                            'vehicle_history_snapshot_path': params['filename'],
                            'vehicle_history_box': json.dumps(params['results'][0]['box']),
                            'vehicle_id': params['vehicle_id'], 'user_id': params['user_id'],
                            'camera': params['camera_id'], 'create_date': params['timestamp_local']})
        conn.commit()
        cur.close()
        conn.close()
    except Exception as error:
        errorMessage = error
        status = 500
        print('errorMessage', errorMessage)
    finally:
        cur.close()
        conn.close()
        return {'code': status, 'message': errorMessage}


def saveVisitorHistory(params):
    """Insert data dari API SDK-Plate Recognizer ke table history visitor(public.visitors).

    :param params: dict, data yang didapat dari API SDK-Plate Recognizer
    :return: int, returning value of visitor_id ketika insert.
    """
    conn = None
    cur = None
    errorMessage = 'Insert Success'
    status = 200
    insertId = None
    try:
        query = 'INSERT INTO public.visitors(visitor_lisence_plate, visitor_status, visitor_vehicle_type, visitor_license_plate_box, visitor_snapshot_path, visitor_camera, create_date) VALUES(%(visitor_lisence_plate)s, %(visitor_status)s, %(visitor_vehicle_type)s, %(visitor_license_plate_box)s, %(visitor_snapshot_path)s, %(visitor_camera)s, %(create_date)s) RETURNING visitor_id;'
        conn = dbcon.get_db_connection()
        cur = conn.cursor()
        cur.execute(query, {'visitor_lisence_plate': params['results'][0]['plate'].upper(),
                            'visitor_status': params['visitor_status'], 'visitor_camera': params['camera_id'],
                            'visitor_vehicle_type': params['results'][0]['vehicle']['type'],
                            'visitor_license_plate_box': json.dumps(params['results'][0]['box']),
                            'visitor_snapshot_path': params['filename'], 'create_date': params['timestamp_local']})
        conn.commit()
        insertId = cur.fetchone()[0]
        cur.close()
        conn.close()
    except Exception as error:
        errorMessage = error
        status = 500
    finally:
        cur.close()
        conn.close()
        return {'code': status, 'message': errorMessage, 'data': insertId}


def updateInsertLockStatus(userId, vehicleId, lockStatus, date):
    """Update table public.lock_vehicle.

    Untuk mengetahui history dan membantu untuk menulusri siapa yang sedang menggunakan kendaraan tersebut.

    :param userId: int, id dari orang yang mengubah lock status
    :param vehicleId: int, id dari kendaraan yang status nya diubah
    :param lockStatus: boolean, True / False
    :param date: date, tanggal dimana perubahan terjadi
    :return: dict, {'code': status, 'message': errorMessage}
    """
    conn = None
    cur = None
    errorMessage = 'Insert Update Success'
    status = 200
    try:
        query = 'INSERT INTO public.lock_vehicle (user_id, vehicle_id, lock_status, create_date) VALUES(%(user_id)s, %(vehicle_id)s, %(lock_status)s, %(create_date)s);'
        conn = dbcon.get_db_connection()
        cur = conn.cursor()
        cur.execute(query, {'user_id': userId, 'vehicle_id': vehicleId, 'lock_status': lockStatus, 'create_date': date})
        conn.commit()
        cur.close()
        conn.close()
    except Exception as error:
        errorMessage = error
        status = 500
        print('error', error)
    finally:
        cur.close()
        conn.close()
        return {'code': status, 'message': errorMessage}


def exampleDocString(dividend, divisor, taking_int=False):
    """Calculate the product of two numbers with a base factor.

    :param dividend: int | float, the dividend in the division
    :param divisor: int | float, the divisor in the division
    :param taking_int: bool, whether only taking the integer part of the quotient;
      default: False, which calculates the precise quotient of the two numbers
    :return: float | int, the quotient of the dividend and divisor

    :raises: ZeroDivisionError, when the divisor is 0
    """
    return None


def getVehicleInfo(licensePlate):
    """Get vehicle info of member from public.vehicles

    :param licensePlate: str, plate nomor hasil scan camera
    :return: dict, (user_id, vehicle_id, vehicle_status, vehicle_lock_status)
    """
    conn = None
    cur = None
    # errorMessage = 'Success'
    # status = 200
    data = ''
    try:
        conn = dbcon.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT user_id, vehicle_id, vehicle_status, vehicle_lock_status FROM public.vehicles where vehicle_lisence_plate = %(license_plate)s;",
            {'license_plate': licensePlate.upper()})
        data = cur.fetchone()
    except Exception as error:
        # errorMessage = error
        # status = 500
        print('getVehicleInfo error:', error)
    finally:
        cur.close()
        conn.close()
    return data


def getLastStatusDirection(vehicleId):
    """Get status dari arah warga terakhir (Masuk/Keluar) dari table public.vehicle_history

    :param vehicleId: int, vehicle_id bisa di dapat dari fungsi dashboard_query.getVehicleInfo(licensePlate)
    :return: str, Masuk / Keluar
    """
    conn = None
    cur = None
    # errorMessage = 'Success'
    # status = 200
    data = 'None'
    try:
        conn = dbcon.get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "select vehicle_history_status from public.vehicle_history where vehicle_id = %(vehicle_id)s order by create_date desc, vehicle_history_id desc limit 1;",
            {'vehicle_id': vehicleId})
        data = cur.fetchone()[0]
    except Exception as error:
        # errorMessage = error
        # status = 500
        print('getLastStatusDirection error:', error)
    finally:
        cur.close()
        conn.close()
    return data


def getLastStatusDirectionVisitor(licensePlate):
    """get status direction Masuk / Keluar untuk visitor dari table public.visitors

    :param licensePlate: str, berasal dari hasil scan plat nomor
    :return: str, Masuk / Keluar
    """
    conn = None
    cur = None
    # errorMessage = 'Success'
    # status = 200
    data = ''
    try:
        conn = dbcon.get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "select coalesce ((select visitor_status from public.visitors where visitor_lisence_plate = %(visitor_lisence_plate)s order by create_date desc, visitor_id desc limit 1),'0');",
            {'visitor_lisence_plate': licensePlate.upper()})
        data = cur.fetchone()[0]
    except Exception as error:
        # errorMessage = error
        # status = 500
        print('getLastStatusDirectionVisitor error:', error)
    finally:
        cur.close()
        conn.close()
    return data


def getUserIdFromLockVehicle(vehicleId, lockStatus):
    """Get user id dari table public.lock_vehicle yang telah melakukan perubahan locked_status di table public.vehicle

    :param vehicleId: int, vehicle_id bisa di dapat dari fungsi dashboard_query.getVehicleInfo(licensePlate)
    :param lockStatus: str | boolean, bisa di dapat dari fungsi dashboard_query.getVehicleInfo(licensePlate)
    :return: int, user_id
    """
    conn = None
    cur = None
    # errorMessage = 'Success'
    # status = 200
    data = ''
    try:
        conn = dbcon.get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id FROM public.lock_vehicle where vehicle_id = %(vehicle_id)s and lock_status = %(lock_status)s order by create_date desc limit 1;",
            {'vehicle_id': vehicleId, 'lock_status': lockStatus})
        data = cur.fetchone()[0]
    except Exception as error:
        # errorMessage = error
        # status = 500
        print('getUserIdFromLockVehicle error:', error)
    finally:
        cur.close()
        conn.close()
    return data


def getUserIdFromVehicleHistory(vehicleId, vehicleHistoryStatus):
    """Get user id di table public.vehicle_history filter by parameter di bawah ini.

    :param vehicleId: int
    :param vehicleHistoryStatus: str, Masuk / Keluar
    :return: int, user_id
    """
    conn = None
    cur = None
    # errorMessage = 'Success'
    # status = 200
    data = ''
    try:
        conn = dbcon.get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id FROM public.vehicle_history where vehicle_id = %(vehicle_id)s and vehicle_history_status = %(vehicle_history_status)s order by create_date desc limit 1;",
            {'vehicle_id': vehicleId, 'vehicle_history_status': vehicleHistoryStatus})
        data = cur.fetchone()[0]
    except Exception as error:
        # errorMessage = error
        # status = 500
        print('getUserIdFromVehicleHistory error:', error)
    finally:
        cur.close()
        conn.close()
    return data


def getVisitorDestination(licensePlate):
    """get visitor destination ketika dia masuk dari table public.visitors

    :param licensePlate: str
    :return: str, Masuk / Keluar
    """
    conn = None
    cur = None
    # errorMessage = 'Success'
    # status = 200
    data = ''
    try:
        conn = dbcon.get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "select coalesce ((select visitor_destination from public.visitors where visitor_lisence_plate = %(visitor_lisence_plate)s order by create_date desc, visitor_id desc limit 1),'None');;",
            {'visitor_lisence_plate': licensePlate.upper()})
        data = cur.fetchone()[0]
    except Exception as error:
        # errorMessage = error
        # status = 500
        print('getVisitorDestination error:', error)
    finally:
        cur.close()
        conn.close()
    return data


def updateVisitorDestination(insertId, destination):
    """Update visitor destination untuk visitor yang baru saja masuk di table public.visitors.

    :param insertId: int, dapat dari saveVisitorHistory
    :param destination: str, mungkin bisa diisi nomor rumah misalnya
    :return: dict, {'code': status, 'message': errorMessage}
    """
    conn = None
    cur = None
    errorMessage = 'Update Success'
    status = 200
    try:
        query = 'update public.visitors set visitor_destination = %(visitor_destination)s where visitor_id = %(visitor_id)s;'
        conn = dbcon.get_db_connection()
        cur = conn.cursor()
        cur.execute(query, {'visitor_id': insertId, 'visitor_destination': destination})
        conn.commit()
        cur.close()
        conn.close()
    except Exception as error:
        errorMessage = error
        status = 500
    finally:
        cur.close()
        conn.close()
        return {'code': status, 'message': errorMessage}


def updateVehicleLockStatus(vehicleId, lockStatus):
    """Update vehicle lock status di public.vehicle.

    :param vehicleId: int
    :param lockStatus: boolean
    :return: dict, {'code': status, 'message': errorMessage}
    """
    conn = None
    cur = None
    errorMessage = 'Update Success'
    status = 200
    try:
        query = 'update public.vehicles set vehicle_lock_status = %(vehicle_lock_status)s where vehicle_id = %(vehicle_id)s;'
        conn = dbcon.get_db_connection()
        cur = conn.cursor()
        cur.execute(query, {'vehicle_id': vehicleId, 'vehicle_lock_status': lockStatus})
        conn.commit()
        cur.close()
        conn.close()
    except Exception as error:
        errorMessage = error
        status = 500
    finally:
        cur.close()
        conn.close()
        return {'code': status, 'message': errorMessage}
