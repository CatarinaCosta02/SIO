from flask_mysqldb import MySQL


class ClinicDB:

    def __init__(self, mysql: MySQL):
        self.mysql = mysql

    @property
    def conn(self):
        return self.mysql.connection

    def init(self):
        file = open('schema.sql', mode='r')
        lines = file.readlines()
        new_lines = []
        for line in lines:
            if not line.startswith('--') and line:
                new_lines += [line]
        join = ''.join(new_lines).replace('\n', ' ')
        cursor = self.conn.cursor()
        for line in join.split(';'):
            if len(line.strip()) > 0:
                cursor.execute(line)
        self.conn.commit()
        file.close()

    def get_layout_ctx(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id,name FROM departments')
        deps = cur.fetchall()
        cur.execute('SELECT id,first_name,last_name FROM doctors')
        docs = cur.fetchall()
        cur.close()
        ctx = {
            'departments': deps,
            'doctors': docs
        }
        return ctx
