from flask import Flask,redirect,render_template,request,url_for, session
from datetime import datetime
from flask import send_file
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
from sqlalchemy import create_engine
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

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

@app.route("/predictByFilter")
def byFilter():
    db = getMysqlConnection()
    cur = db.cursor()
    sql= "SELECT id_usuario FROM usuario"
    cur.execute(sql)
    users = cur.fetchall()
    
    sql= "SELECT id_empresa, nombre_empresa FROM empresa"
    cur.execute(sql)
    companies = cur.fetchall()
    d={}
    l=[]
    aux=0
    for user in users:
        d[user[0]]=[]

        for company in companies:
            sql= "SELECT count(*) FROM acciones where id_empresa = %s and id_usuario = %s"
            cur.execute(sql,(company[0],user[0]))
            count = cur.fetchone()
            d[user[0]].append(count[0])
            if aux==0:
                l.append(company[1])
        aux=1
  
    df = pd.DataFrame(d, index =l)
    # print the data

    df_corr=df.corr(method='pearson')

    def vecinosCercanos(corrUser, k=5):
        return corrUser[corrUser.index != corrUser.name].nlargest(n=k).index.tolist()

    vecinos = df_corr.apply(lambda col: vecinosCercanos(col))

    def calculateRecomendationUser(vecinosCercanos, usercorr, data):    
        def calculatePredictCompany(vecinosCercanos,usercorr,buyCompany): 
            haveBuy = ~np.isnan(buyCompany)
            if(np.sum(haveBuy) != 0):
                return np.dot(buyCompany.loc[haveBuy], usercorr.loc[haveBuy])/np.sum(usercorr[haveBuy])
            else:
                return np.nan        
        return df.apply(lambda row: calculatePredictCompany(vecinosCercanos, usercorr, row[vecinosCercanos]), axis=1)
        
    predictCompany = df.apply(lambda buys: calculateRecomendationUser(vecinos[buys.name],df_corr[buys.name][vecinos[buys.name]],df))

    sql= "SELECT nombre_empresa FROM acciones a, empresa e where a.id_empresa=e.id_empresa and a.id_usuario =%s group by nombre_empresa"
    cur.execute(sql,(session["id"],))
    companies_of_user = [item[0] for item in cur.fetchall()]


    predict=predictCompany[session["id"]].sort_values(ascending=False).head(5)
    predict.to_csv("./al.csv")
    ap=pd.read_csv("./al.csv")
    ar=ap.iloc[:,0].to_numpy()
    b = np.array(companies_of_user)
    c = ar[~np.in1d(ar,b)]
    print(c)

    return render_template("index.html")

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

@app.route("/predictContent")
def byContent():
    db_connection_str = 'mysql+pymysql://sistemasderecomendacion:m2AyGl6&NRCc@sistemasderecomendacion.mysql.database.azure.com/sr'
    db_connection = create_engine(db_connection_str)
    df = pd.read_sql('SELECT nombre_empresa, sector, industry FROM empresa', con=db_connection)
    #df.drop(['id_empresa','sigla_empresa','name_file','estado_empresa','exchange','dividen_pay','dividen_date',"market_cap"], axis=1, inplace=True)
    df=df.replace({'\\$':''}, regex=True)
    df=df.replace({'\\%':''}, regex=True)
    df=df.replace({'N/A':''}, regex=True)

    columnsString=["nombre_empresa","sector","industry"]
    df[columnsString]=df[columnsString].astype("string")
    
    """columnsToArray=["today","h_week","share_volume","average_volume"]

    for column in columnsToArray:
        if(column=="today" or column=="h_week"):
            separator="/"
        else:
            separator=","

        df[column] = df[column].apply(lambda x: x.split(separator) if x != '' else [])
        s = df.apply(lambda x: pd.Series(x[column]),axis=1).stack().reset_index(level=1, drop=True)
        s.name = column+"_clean"
        df = df.drop(column, axis=1).join(s)


    columnsString=["nombre_empresa","sector","industry"]
    df[columnsString]=df[columnsString].astype("string")
    
    def processCol(col):
        return col.astype(str).apply(lambda val: val.replace(',','') if val != '' else 0).astype(float)

    num_columns = df.select_dtypes(exclude='string').columns
    df[num_columns]=df[num_columns].apply(processCol)"""

    vectorizer = TfidfVectorizer(min_df=1, stop_words='english')
    bag_of_words= vectorizer.fit_transform(df["sector"]+" "+df["industry"])
    print(bag_of_words.shape)
    cosine_sim = linear_kernel(bag_of_words, bag_of_words)
    indices = pd.Series(df.index, index=df['nombre_empresa']).drop_duplicates()

    def content_recommender(top, title, cosine_sim=cosine_sim, df=df, indices=indices):
        idx = indices[title]
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:top+1]
        companies_indices = [i[0] for i in sim_scores]
        return df['nombre_empresa'].iloc[companies_indices]
    
    print(content_recommender(5,'Intel Corporation Common Stock (INTC)'))


    return render_template("index.html")


@app.route("/predictByFilter")
def byFilter():
    db = getMysqlConnection()
    cur = db.cursor()
    sql= "SELECT id_usuario FROM usuario"
    cur.execute(sql)
    users = cur.fetchall()
    
    sql= "SELECT id_empresa, nombre_empresa FROM empresa"
    cur.execute(sql)
    companies = cur.fetchall()
    d={}
    l=[]
    aux=0
    for user in users:
        d[user[0]]=[]

        for company in companies:
            sql= "SELECT count(*) FROM acciones where id_empresa = %s and id_usuario = %s"
            cur.execute(sql,(company[0],user[0]))
            count = cur.fetchone()
            d[user[0]].append(count[0])
            if aux==0:
                l.append(company[1])
        aux=1
  
    df = pd.DataFrame(d, index =l)
    # print the data

    df_corr=df.corr(method='pearson')

    def vecinosCercanos(corrUser, k=5):
        return corrUser[corrUser.index != corrUser.name].nlargest(n=k).index.tolist()

    vecinos = df_corr.apply(lambda col: vecinosCercanos(col))

    def calculateRecomendationUser(vecinosCercanos, usercorr, data):    
        def calculatePredictCompany(vecinosCercanos,usercorr,buyCompany): 
            haveBuy = ~np.isnan(buyCompany)
            if(np.sum(haveBuy) != 0):
                return np.dot(buyCompany.loc[haveBuy], usercorr.loc[haveBuy])/np.sum(usercorr[haveBuy])
            else:
                return np.nan        
        return df.apply(lambda row: calculatePredictCompany(vecinosCercanos, usercorr, row[vecinosCercanos]), axis=1)
        
    predictCompany = df.apply(lambda buys: calculateRecomendationUser(vecinos[buys.name],df_corr[buys.name][vecinos[buys.name]],df))

    sql= "SELECT nombre_empresa FROM acciones a, empresa e where a.id_empresa=e.id_empresa and a.id_usuario =%s group by nombre_empresa"
    cur.execute(sql,(session["id"],))
    companies_of_user = [item[0] for item in cur.fetchall()]


    predict=predictCompany[session["id"]].sort_values(ascending=False).head(5)
    predict.to_csv("./al.csv")
    ap=pd.read_csv("./al.csv")
    ar=ap.iloc[:,0].to_numpy()
    b = np.array(companies_of_user)
    c = ar[~np.in1d(ar,b)]
    print(c)

    return render_template("index.html")

@app.route("/getCompany/<int:id>")
def getCompany(id=None):
    if id != None:
        sql = "SELECT * from empresa where id_empresa = %s";
        db = getMysqlConnection()
        cur = db.cursor(dictionary=True)
        cur.execute(sql, (id,))
        company = cur.fetchone()
        print(company)

    return render_template("company2.html",company=company)

@app.route("/saveBuy",methods=["POST"])
def saveBuy():
    id_c=request.form['id_company']
    now = datetime.now()
    

    # dd/mm/YY H:M:S
    fecha = now.strftime("%Y-%m-%d %H:%M:%S")
    
    conn = getMysqlConnection()
    cur = conn.cursor()


    sql = 'INSERT INTO acciones (id_empresa,id_usuario,fecha_adquisicion,estado_accion) VALUES (%s,%s,%s,%s)'
    val = (id_c,session["id"],fecha,"comprada")
    cur.execute(sql, val)
    conn.commit()
    print("llego el id "+id_c)

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
    return render_template('empresas/index.html',empleados=empleados)

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

        WebDriverWait(driver,10)
        time.sleep(10);

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
        #print(data_company)#guardar data empresa
        exchange = data_company[0][1]
        sector = data_company [1][1]
        industry = data_company [2][1]
        year = data_company[3][1]
        today = data_company[4][1]
        share = data_company[5][1]
        average = data_company[6][1]
        previous = data_company[7][1]
        week = data_company[8][1]
        market = data_company[9][1]
        ratio = data_company[10][1]
        forward = data_company[11][1]
        earnings = data_company[12][1]
        annualized = data_company[13][1]
        dividend = data_company[14][1]
        dividendp = data_company[15][1]
        current = data_company[16][1]

        try:
            beta = data_company[17][1]
        except:
            beta ="N/A"
        

        name_file=latest_file.split("\\")[-1]


        conn = getMysqlConnection()
        cur = conn.cursor()

        sql = 'INSERT INTO empresa (nombre_empresa,sigla_empresa,name_file,exchange,sector,industry,year_target,today,share_volume,average_volume,previous_close,h_week,market_cap,ratio,forward,earnings,annualized_dividend,dividen_date,dividen_pay,current_yield,estado_empresa,beta) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        val = (empresa,sigla,name_file,exchange, sector, industry ,year ,today ,share ,average ,previous ,week ,market,ratio ,forward,earnings,annualized,dividend,dividendp,current,'activo',beta)
        cur.execute(sql, val)
        conn.commit()
        #getTweet(sigla)
        #convertToCSV(sigla)
        

    thread= Thread(target=getDatas)
    thread.start()

    return render_template("nasdaq_response/ok.html")


@app.route('/home',methods=['GET','POST'])
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        # We need all the account info for the user so we can display it on the profile page
        db = getMysqlConnection()
        cur = db.cursor()
        cur.execute('SELECT * FROM empresa ')
        company = cur.fetchall()
        print(company)
        db.commit()
        return render_template('home.html', username=session['username'],companys=company)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/getPlotCSV') # this is a job for GET, not POST
def plot_csv():
    return send_file('downloads/a.csv',
                     mimetype='text/csv',
                     attachment_filename='a.csv',
                     as_attachment=True)

@app.route('/getPlotCSS') # this is a job for GET, not POST
def plot_css():
    return send_file('templates/custom.css',
                     mimetype='text/css',
                     attachment_filename='custom.css',
                     as_attachment=True)

@app.route('/getB') # this is a job for GET, not POST
def plot_jpeg():
    return send_file('templates/business.jpeg',
                     mimetype='img/jpeg',
                     attachment_filename='business.jpeg',
                     as_attachment=True)

@app.route("/predictCompany")
def predict():
    sigla="INTC"+".csv"
    ruta_data_accions="HistoricalData_1637979637603.csv"
    #predict=predictDataSet(ruta_data_accions)
    predict=predictDataSet()
    
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
