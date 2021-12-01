from flask import Flask,redirect,render_template,request,url_for, session
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import os
import glob
from selenium.webdriver.support.ui import WebDriverWait
from threading import Thread
import csv
import sqlite3
import mysql.connector
import matplotlib.pyplot as plt
import threading
import base64
import re
import io
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from prediction.predictionstockmarket import predictDataSet
app=Flask(__name__)
app.secret_key = 'your secret key'

@app.route('/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        db = getMysqlConnection()
        cur = db.cursor(dictionary=True)
        cur.execute('SELECT * FROM usuario WHERE nick_name_usuario = %s AND password_usuario = %s', (username, password,))
        # Fetch one record and return result
        account = cur.fetchone()
        print(account)
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = int (account['id_usuario'])
            session['username'] = account['nick_name_usuario']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)


@app.route('/requestCompany',methods=['GET','POST'])
def requestCompany():
    return render_template('nasdaq_petition/index.html')

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        db = getMysqlConnection()
        cur = db.cursor(dictionary=True)
        cur.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cur.fetchone()
        #If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cur.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    return render_template('register.html', msg=msg)

@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        db = getMysqlConnection()
        cur = db.cursor(dictionary=True)
        cur.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cur.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/data')
def data():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        db = getMysqlConnection()
        cur = db.cursor()
        cur.execute('SELECT * FROM usuario')
        accounts = cur.fetchall()
        print(accounts)
        db.commit()
        # Show the profile page with account info
        return render_template('data.html', accounts=accounts)
    # User is not loggedin redirect to login page

@app.route('/graph')    
def graph():
    img = io.BytesIO()
    y = [1,2,3,4,5]
    x = [0,2,1,3,4]
    plt.plot(x,y)
    plt.savefig(img, format='png')
    img.seek(0)

    plot_url = base64.b64encode(img.getvalue())
    return render_template('graph2.html', plot_url=plot_url)
    print(threading.current_thread())

def find_between( s, first, last ):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""



def getMysqlConnection():
    return mysql.connector.connect(host='sistemasderecomendacion.mysql.database.azure.com',
                                   database='sr',
                                   user='sistemasderecomendacion',
                                   password='m2AyGl6&NRCc',)

@app.route('/getMySQL')
def index():  # put application's code here
    db = getMysqlConnection()
    sqlstr = "select * from usuario"
    cur = db.cursor()
    cur.execute(sqlstr)
    empleados = cur.fetchall()
    print(empleados)
    return render_template('empresas/index.html',empleados=empleados);

@app.route('/destroy/<int:id>')
def destroy(id):
    conn = getMysqlConnection()
    cur = conn.cursor()
    cur.execute("DELETE FROM usuario where id=%s",(id))
    conn.commit()
    return redirect('/')

@app.route('/edit/<int:id>')
def edit(id):
    conn = getMysqlConnection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuario where id=%s",(id))
    usuarios = cur.fetchall()
    conn.commit()
    print(usuarios)
    return redirect('/edit.html',usuarios=usuarios)


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



@app.route('/search',methods=['POST'])
def search():
    _company_name=request.form['company_name']

    _company_name = _company_name.replace(" ","%20")

    link = "https://www.nasdaq.com/search?q="+_company_name+"&page=1&sort_by=relevence&langcode=en"

    chrome_options = uc.ChromeOptions()

    chrome_options.add_argument("--headless")

    chrome_options.add_argument("--disable-extensions")

    chrome_options.add_argument("--disable-popup-blocking")

    chrome_options.add_argument("--profile-directory=Default")

    chrome_options.add_argument("--ignore-certificate-errors")

    chrome_options.add_argument("--disable-plugins-discovery")

    chrome_options.add_argument("--incognito")

    chrome_options.add_argument("user_agent=DN")

    chrome_options.add_argument("--disable-gpu")


    driver = uc.Chrome(options=chrome_options)

    driver.delete_all_cookies()
    
    driver.get(link)

    response_table = driver.find_elements(By.CLASS_NAME,"search-results__text")

    links =driver.find_element(By.CLASS_NAME,"search-results__results-items")

    getLink = links.get_attribute("innerHTML")

    getLinks = getLink.split("</a>")

    respuesta=[]

    aux=0

    for item in response_table:
        if aux == 5:
            break;
        s =item.text.splitlines()
        if "Summary" not in s[0]:
            break;

        link = ""
        s[0] = s[0].replace("- Summary","").strip()
        s[1] = s[1].split(" ")[0]
        for x in getLinks:
            k= str(s[1].lower())
            c= str(x)
            if k in c:
                link = find_between(c,'href="','"')
                link = "https://www.nasdaq.com" + link
                break;

        add= [s[0],s[1],link]

        if add not in respuesta:
            respuesta.append(add)
        aux= aux +1

    driver.quit()


    return render_template('nasdaq_response/index.html',response=respuesta)

@app.route("/selectData",methods=["POST","GET"])
def getData():
    empresa = request.form['nombre']
    sigla = request.form['sigla']
    url = request.form['url']

    def getDatas():
        chrome_options = uc.ChromeOptions()

        chrome_options.add_argument("--disable-extensions")

        chrome_options.add_argument("--disable-popup-blocking")

        chrome_options.add_argument("--profile-directory=Default")

        chrome_options.add_argument("--ignore-certificate-errors")

        chrome_options.add_argument("--disable-plugins-discovery")

        chrome_options.add_argument("--incognito")

        chrome_options.add_argument("user_agent=DN")

        chrome_options.add_argument("--disable-gpu")

        dir = os.path.dirname(__file__)
        filename = os.path.join(dir, 'downloads')

        prefs = {}
        prefs["profile.default_content_settings.popups"]=0

        prefs["download.default_directory"]=filename
        chrome_options.add_experimental_option("prefs", prefs)

        driver = uc.Chrome(options=chrome_options)
        driver.maximize_window()
        driver.delete_all_cookies()
        
        driver.get(url)

        element = driver.find_element(By.CLASS_NAME,'summary-data__header')
        element.location_once_scrolled_into_view

        WebDriverWait(driver,2)
        time.sleep(2);

        titles = driver.find_elements(By.CLASS_NAME,"summary-data__cellheading")
        titles2 = driver.find_elements(By.CLASS_NAME,"summary-data__cell")

        data_company = []
        for x in range(len(titles)):
            data_company.append([titles[x].text,titles2[x].text])


        driver.get(url+"/historical")

        time.sleep(5)

        driver.execute_script("scroll(0, 200);")

        dates= driver.find_elements(By.CLASS_NAME,"table-tabs__tab")

        for y in dates:
            if y.get_attribute("data-value") == 'm6':
                y.click();
                break;
        
        WebDriverWait(driver,5)
        time.sleep(5)

        try:
            driver.find_element(By.XPATH,"/html/body/div[1]/div/main/div[2]/div[4]/div[3]/div/div[1]/div/div[1]/div[3]/button").click()
        except NoSuchElementException:
            try:
                driver.find_element(By.XPATH,"/html/body/div[2]/div/main/div[2]/div[4]/div[3]/div/div[1]/div/div[1]/div[3]/button").click()
            except NoSuchElementException:
                pass

        time.sleep(4);

        driver.quit()

        list_of_files = glob.glob(filename+"\*") # * means all if need specific format then *.csv
        latest_file = max(list_of_files, key=os.path.getctime)#save id,empresa, sigla, latest_file
        print(latest_file)
        print(data_company)#guardar data empresa
        #for x in data_company:
            #x[0]=nombre columna
            #x[1]=valor

        db = getMysqlConnection()
        cur = db.cursor()
        cur.execute('INSERT INTO empresa VALUES (NULL, %s, %s, %s)', (, ,,))
        print "Registro Insertados Correctamente"

        try:
            cur.execute()
            db.commit()

        except:
            print
            "No se Guardaron los Registros"
            db.rollback()

        getTweet(sigla)
        convertToCSV(sigla)
        

    thread= Thread(target=getDatas)
    thread.start()

    return render_template("nasdaq_response/ok.html")

@app.route("/predictCompany")
def predict():
    sigla="INTC"+".csv"
    ruta_data_accions="HistoricalData_1637979637603.csv"
    predict=predictDataSet(ruta_data_accions)
    #sentimientos=analysisBySentiments(sigla+'.csv')
    sentimientos=""

    return render_template("final_predict.html",predict=predict,sentimientos=sentimientos)


def getTweet(sigla):
    import tweet_collector

    tweet_collector.setArgs(sigla)
    tweet_collector.run()
def convertToCSV(sigla):
    csvWriter = csv.writer(open(sigla+'.csv', 'w',newline='',encoding='utf-8'))
    conn = sqlite3.connect(sigla+'_2021-11-24-2021-11-25.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Tweet")
    rows = cursor.fetchall()
    print("entra csv")
    for row in rows:
        csvWriter.writerow(row)
    print("sale csv")

def insert_bd():
      """if request.method=='POST':
        # Handle POST Request here
        return render_template('index.html')
    
    sql= "INSERT into autor values (0,'Andres1','Algo1 xd');"
    conn=mysql.connect()
    cursor=conn.cursor()
    cursor.execute(sql)
    conn.commit()"""

if __name__ == '__main__':
    #DEBUG is SET to TRUE. CHANGE FOR PROD
    app.run(port=5000,debug=True)



# See PyCharm help at https://www.jetbrains.com/help/pycharm/
