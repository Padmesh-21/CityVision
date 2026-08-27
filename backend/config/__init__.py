import pymysql

# mysqlclient is painful to build on Windows without the MySQL Connector/C
# headers and Visual C++ build tools. PyMySQL is a pure-Python driver that
# speaks the same wire protocol, so we install it as a drop-in replacement
# for MySQLdb before Django ever touches the database backend.
pymysql.install_as_MySQLdb()
