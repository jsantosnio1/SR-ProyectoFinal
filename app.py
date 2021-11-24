from flask import Flask
from flask import render_template,request,redirect
import mysql.connector



app = Flask(__name__)



def getMysqlConnection():
    return mysql.connector.connect(host='localhost', database='spring', user='root', password='')


@app.route('/')
def index():  # put application's code here
    db = getMysqlConnection()
    sqlstr = "select * from persona"
    cur = db.cursor()
    cur.execute(sqlstr)
    empleados = cur.fetchall()
    print(empleados)
    return render_template('empresas/index.html',empleados=empleados);

@app.route('/destroy/<int:id>')
def destroy(id):
    conn = getMysqlConnection()
    cur = conn.cursor()
    cur.execute("DELETE FROM persona where id=%s",(id))
    conn.commit()
    return redirect('/')

@app.route('/create')
def create():  # put application's code here
    return render_template('empresas/create.html')

@app.route('/store',methods=['POST'])
def storage():
    _nombre=request.form['txtNombre']
    _apellido=request.form['txtApellido']
    _correo=request.form['txtCorreo']
    _numero=request.form['txtNumero']

    sql = "INSERT INTO `persona`(`id`,`nombre`,`apellido`,`email`,`telefono`) VALUES (3,%s,%s,%s,%s);"
    datos=(_nombre,_apellido,_correo,_numero)
    conn = getMysqlConnection()
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    return render_template('empresas/index.html')
if __name__ == '__main__':
    app.run()
