# import xmlrpclib
import csv
import sys
import psycopg2
sys.path.append("./openerp")
sys.path.append("./openerp/addons")

# import OpenERP
import openerp

# import the account addon modules that contains the tables
# to be populated.
import despesa

# define connection string
conn_string2 = "dbname='debug' user='admin' password='xb800'"

# get a db connection
conn = psycopg2.connect(conn_string2)

# conn.cursor() will return a cursor object
cursor = conn.cursor()

# and finally use the ORM to insert data into table.
#
# username = "admin"
# pwd = "xb800"
# dbname = "debug"
#
# sock_common = xmlrpclib.ServerProxy("http://localhost:8069/xmlrpc/common")
#
# uid = sock_common.login(dbname, username, pwd)
#
# sock = xmlrpclib.ServerProxy("http://localhost:8069/xmlrpc/object")

reader = csv.reader(open('../SNCP/data/fundamentos.csv','rb'))
for row in reader:
    print row[1]
    fundamentos = {
        'id': row[1],
        'codigo_120':row[2],
        'name':row[3],
        }
    #dim_id=sock.execute(dbname, uid,pwd, 'sncp.despesa.fundamentos','create',fundamentos)