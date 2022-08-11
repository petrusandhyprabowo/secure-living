import psycopg2

# heroku
host = 'ec2-23-23-151-191.compute-1.amazonaws.com'
database = 'd8gk809gjhcnkd'
user = 'omjmbqihmwzrqm'
password = '84469b88500b335b2da4991b32154196c194edd18368a07f6615a6cab2b61f1d'

# local
# host = 'localhost'
# database = 'scl_tenant_satu'
# user = 'postgres'
# password = 'admin'
# port = '5432'

def get_db_connection(host=host, database=database, user=user, password=password):
    conn = psycopg2.connect(host=host, database=database, user=user, password=password)
    return conn