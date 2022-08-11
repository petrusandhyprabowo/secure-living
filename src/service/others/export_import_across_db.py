import numpy
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from src.config import dbcon


def getDatabaseDetails(database_id):
    conn = None
    cur = None
    errorMessage = 'Success'
    status = 200
    data = ''
    try:
        conn = dbcon.get_db_connection(database='scl_core')
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT database_name, database_user, database_password, database_host, database_port FROM "
            "public.databases where database_id = %s;",
            [database_id])
        data = cur.fetchall()
    except Exception as error:
        errorMessage = error
        status = 500
    finally:
        cur.close()
        conn.close()
    return {'code': status, 'message': errorMessage, 'data': data}


def dynamicSelect(database, fields, tableName, where=None, orders=None, displayColumn=True):
    if orders is None:
        orders = []
    if where is None:
        where = {}
    conn = None
    cur = None
    errorMessage = 'Success'
    status = 200
    data = ''
    try:
        conn = dbcon.get_db_connection(database=database)
        cur = conn.cursor()
        if displayColumn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
        listQuery = []

        query = sql.SQL("SELECT {fields} FROM public.{table}").format(
            fields=sql.SQL(',').join(sql.Identifier(field) for field in fields),
            table=sql.Identifier(tableName)
        )
        listQuery.append(query)

        if where:
            whereQuery = sql.SQL('WHERE {whereKey} = {whereValue}').format(
                whereKey=sql.Identifier(where['column']),
                whereValue=sql.Literal(where['value'])
            )
            listQuery.append(whereQuery)

        if orders:
            orderQuery = sql.SQL('ORDER BY {orderCol}').format(
                orderCol=sql.SQL(',').join(sql.Identifier(order) for order in orders)
            )
            listQuery.append(orderQuery)

        composedQuery = sql.Composed(listQuery)
        cur.execute(composedQuery)
        data = cur.fetchall()
    except Exception as error:
        errorMessage = error
        status = 500
    finally:
        cur.close()
        conn.close()
    return {'code': status, 'message': errorMessage, 'data': data}


def dynamicInsert(database, fields, tableName, data):
    conn = None
    cur = None
    errorMessage = 'Insert Success'
    status = 200
    try:
        conn = dbcon.get_db_connection(database=database)
        cur = conn.cursor()

        query = sql.SQL('INSERT INTO public.{table} ({fields}) VALUES ').format(
            table=sql.Identifier(tableName),
            fields=sql.SQL(', ').join(map(sql.Identifier, fields))).as_string(conn)
        values = sql.SQL('({value})').format(
            value=sql.SQL(', ').join(sql.Placeholder() * len(fields))
        ).as_string(conn)

        args = ','.join(cur.mogrify(values, i).decode('utf-8') for i in data)

        cur.execute(query + args)
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


# transfer data WARGA from secure_living
def transferData():
    licensePlateOwner = {'B1043FYK': {'vid':1,'uid':[1,13]},'B1231PAF': {'vid':2,'uid':[1,13]},'B1298SJX': {'vid':3,'uid':[1,13]},'B1406PAF': {'vid':4,'uid':[2,15,14]},'B1426PVF': {'vid':5,'uid':[2,15,14]},'B1428KRP': {'vid':6,'uid':[2,15,14]},'B1446PJ': {'vid':7,'uid':[2,15,14]},'B1448DP': {'vid':8,'uid':[3]},'B1466PMF': {'vid':9,'uid':[3]},'B1469PAF': {'vid':10,'uid':[4,18,17,16]},'B1475PJV': {'vid':11,'uid':[5,21,20,19]},'B1476PAF': {'vid':12,'uid':[5,21,20,19]},'B1476PAG': {'vid':13,'uid':[6,22]},'B1476PIF': {'vid':14,'uid':[6,22]},'B1476VAF': {'vid':15,'uid':[7,23]},'B1488PJF': {'vid':16,'uid':[7,23]},'B2550FCV': {'vid':17,'uid':[7,23]},'B3309LE': {'vid':18,'uid':[8,25,24]},'B3319BFG': {'vid':19,'uid':[8,25,24]},'B3339BBB': {'vid':20,'uid':[8,25,24]},'B3383BEI': {'vid':21,'uid':[8,25,24]},'B3399BEN': {'vid':22,'uid':[9,28,27,26]},'B3536KFW': {'vid':23,'uid':[9,28,27,26]},'B3712T00': {'vid':24,'uid':[9,28,27,26]},'B3772TBD': {'vid':25,'uid':[10]},'B406PUF': {'vid':26,'uid':[10]},'B4386SBK': {'vid':27,'uid':[10]},'B4466PVF': {'vid':28,'uid':[11,30,29]},'B4586SEI': {'vid':29,'uid':[11,30,29]},'B4598SCZ': {'vid':30,'uid':[11,30,29]},'B4870SME': {'vid':31,'uid':[12,33,32,31]},'B4870SNE': {'vid':32,'uid':[12,33,32,31]},'B4870SNF': {'vid':33,'uid':[12,33,32,31]}}

    # collect source data
    sourceFields = ['license_plate', 'direction', 'image_path', 'box', 'camera', 'timestamptz']
    sourceWhere = {'column': 'status', 'value': 'WARGA'}
    sourceOrder = ['license_plate', 'id', 'timestamptz']

    sourceData = dynamicSelect(database='secure_living', tableName='ocr_history', fields=sourceFields,
                               where=sourceWhere, orders=sourceOrder)['data']

    cleanData = []
    for data in sourceData:
        cleanData.append([licensePlateOwner[data['license_plate']]['vid'],str(numpy.random.choice(licensePlateOwner[data['license_plate']]['uid'], size=1)[0]),
                         data['direction'],data['image_path'],data['box'],data['camera'],data['timestamptz']])
    print('cleanData',cleanData)

    dbs = ['scl_tenant_test',getDatabaseDetails(1)['data'][0]['database_name'],
           getDatabaseDetails(2)['data'][0]['database_name']]
    targetFields = ['vehicle_id', 'user_id', 'vehicle_history_status', 'vehicle_history_snapshot_path',
                    'vehicle_history_box', 'camera', 'create_date']
    for db in dbs:
        insertStatus = dynamicInsert(database=db, tableName='vehicle_history', fields=targetFields, data=cleanData)
        print('insertStatus', insertStatus)

# transfer data TAMU from secure_living
def transferData():
    # collect source data
    sourceFields = ['license_plate', 'direction', 'vehicle_type', 'box', 'image_path', 'destination', 'camera',
                    'timestamptz']
    sourceWhere = {'column': 'status', 'value': 'TAMU'}
    sourceOrder = ['license_plate', 'id', 'timestamptz']
    sourceData = [list(map(str, x)) for x in
                  dynamicSelect(database='secure_living', tableName='ocr_history', fields=sourceFields,
                                where=sourceWhere, orders=sourceOrder, displayColumn=False)['data']]
    print('source', sourceData[0][7])

    dbs = ['scl_tenant_test', getDatabaseDetails(1)['data'][0]['database_name'],
           getDatabaseDetails(2)['data'][0]['database_name']]
    targetFields = ['visitor_lisence_plate', 'visitor_status', 'visitor_vehicle_type', 'visitor_license_plate_box',
                    'visitor_snapshot_path', 'visitor_destination', 'visitor_camera', 'create_date']
    for db in dbs:
        insertStatus = dynamicInsert(database=db, tableName='visitors', fields=targetFields, data=sourceData)
        print('insertStatus', insertStatus)
