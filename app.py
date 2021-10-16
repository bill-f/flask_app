from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL, MySQLdb
import bcrypt
import numpy as np
import re

#for email validation
EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9!#$%&*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

#connection with database
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flaskdb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

#home route
@app.route('/')
def home():
    return render_template("home.html")

#form route
@app.route('/form')
def form():
    return render_template("form.html")

#login
@app.route('/login',methods=["GET","POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        errors = False
        #check email format
        if not re.match(EMAIL_REGEX, email):
            flash('Email is of incorrect format.', 'login')
            errors = True
        if len(password) < 6 or len(password) > 20:
            flash('Password must be between 6-20 characters', 'login')
            errors = True
        else:
            #check if given email exist
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cur.fetchone()
            cur.close()
            if user:
                #check if email and password is valid
                if bcrypt.hashpw(password, user["password"].encode('utf-8')) == user["password"].encode('utf-8'):
                    #create sessions vars
                    session['userid'] = user['id']
                    session['fname'] = user['fname']
                    session['lname'] = user['lname']
                    session['email'] = user['email']
                    session['role'] = user['role']
                    return render_template("form.html")
                else:
                    flash('Email and Password dont match', 'login')
                    errors = True
            else:
                flash('invalid email or password', 'login')
                errors = True
        if errors:
            return render_template("home.html")

#logout
@app.route('/logout', methods=["GET", "POST"])
def logout():
    session.clear()
    return render_template("home.html")

#register
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        return render_template("home.html")
    else:
        errors = False
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        conf_password = request.form['conf_password'].encode('utf-8')

        #registration form checks
        if len(first_name) < 2 or len(first_name) > 15:
            flash('First name must be between 2-15 characters', 'reg')
            errors = True
        if not first_name.isalpha():
            flash('First name must be all letters', 'reg')
            errors = True
        if len(last_name) < 2 or len(last_name) > 15:
            flash('Last name must be between 2-15 characters', 'reg')
            errors = True
        if not last_name.isalpha():
            flash('Last name must be all letters', 'reg')
            errors = True
        if not re.match(EMAIL_REGEX, email):
            flash('Email is of incorrect format.', 'reg')
            errors = True
        #check if email is already in use
        else:
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                param = [email]
                count = cur.execute('select * from users where email=%s', param)
                if count > 0:
                    flash('Email is already in use', 'reg')
                    errors = True
                cur.close()
        if len(password) < 6 or len(password) > 20:
            flash('Password must be between 6-20 characters', 'reg')
            errors = True
        if password!=conf_password:
            flash('Passwords dont match', 'reg')
            errors = True

        if errors:
            return render_template("home.html")
        else:
            hash_password = bcrypt.hashpw(password, bcrypt.gensalt())
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("INSERT INTO users (fname, lname, email, password) VALUES (%s,%s,%s,%s)",(first_name, last_name, email, hash_password))
            mysql.connection.commit()
            register_id = cur.lastrowid
            cur.execute("select * from users where id=%s", (register_id,))
            user = cur.fetchone()
            cur.close()
            session['userid'] = user['id']
            session['fname'] = user['fname']
            session['lname'] = user['lname']
            session['email'] = user['email']
            session['role'] = user['role']
            return redirect(url_for('form'))

#results route, show the resulted data
@app.route('/results')
def line():
        #gets the session var of prog_id and data_id created by def program or def action
        prog_id= session.get('prog_id')
        data_id = session.get('data_id')

        if data_id and prog_id:

            #gets the data from user_data table where id = session.get(data_id)
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("select * from user_data where id=%s", (data_id,))
            data_result = cur.fetchall()

            # gets roi data from program table where id = session.get(prog_id)
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("select roi from program where id=%s",(prog_id,))
            roi_result = cur.fetchall()
            #fix ta data apo ti vasi gia na bei se lista
            result_str1 = str(roi_result)
            my_list1 = re.findall(r"[-+]?\d*\.\d+|\d+", result_str1)

            # gets npv data from program table where id = session.get(prog_id)
            cur.execute("select npv from program where id=%s", (prog_id,))
            npv_result = cur.fetchall()
            # fix ta data apo ti vasi gia na bei se lista
            result_str2 = str(npv_result)
            my_list2 = re.findall(r"[-+]?\d*\.\d+|\d+", result_str2)

            # gets depre_year data from program table where id = session.get(prog_id)
            cur.execute("select depre_year from program where id=%s", (prog_id,))
            depre_result = cur.fetchall()
            cur.close()

            # roi list
            line_roi_values = my_list1
            # npv list
            line_npv_values = my_list2

            #labels= years dynamic created list
            labels=[]

            #create a list which starts from 0 and increase by 1 for every value in my_list1( roi data ) to represent the years
            u = 0
            for x in my_list1:
                if x:
                    labels.append(u)
                    u += 1

            #cast roi data my_list1 to float vars to get the max and min variable for the chart
            roi_list_float=[]
            for x in my_list1:
                u = float(x)
                roi_list_float.append(u)
                u += 1

            # cast npv data my_list2 to float vars to get the max and min variable for the chart
            npv_list_float = []
            for x in my_list2:
                u = float(x)
                npv_list_float.append(u)
                u += 1

            #years
            line_labels=labels

            return render_template('results.html', title="VIEW DATA", max1=max(roi_list_float)+100, min1=min(roi_list_float), max2=max(npv_list_float)+1000, min2=min(npv_list_float), labels=line_labels, values1=line_roi_values, values2=line_npv_values, len1 = len(my_list1), roi = my_list1, len2 = len(my_list2), npv = my_list2, depre=depre_result, data=data_result)
        else:
            return render_template('results.html', title="NO DATA AVAILABLE")

@app.route('/program', methods=["GET", "POST"])
def program():
    if request.method == 'POST':
        errors = False
        years = request.form.get('years', type=int)
        ependusi = request.form.get('ependusi', type=float)
        esoda_xrono = request.form.get('esoda_xrono', type=float)
        arxi_esodwn = request.form.get('arxi_esodwn', type=int)
        pososto = request.form.get('pososto', type=float)
        egguisi = request.form.get('egguisi', type=float)
        etos_egguisis = request.form.get('etos_egguisis', type=int)

        #check forms

        if not isinstance(years, int):
            flash('Invalid type of years', 'form')
            errors = True
        elif years <=0 or years >30:
            flash('Value of years must be between 0-30', 'form')
            errors = True
        if not isinstance(ependusi, float):
            flash('Invalid type of investment', 'form')
            errors = True
        elif ependusi <=0 or ependusi > 1000000:
            flash('Value of investment must be between 0-1000000', 'form')
            errors = True
        if not isinstance(esoda_xrono, float):
            flash('Invalid type of Corporate earnings / Year', 'form')
            errors = True
        elif esoda_xrono <=0 or esoda_xrono > 1000000:
            flash('Value of Corporate earnings / Year must be between 0-100000', 'form')
            errors = True
        if not isinstance(arxi_esodwn, int):
            flash('Invalid type of Start of earnings', 'form')
            errors = True
        elif arxi_esodwn <=0 or arxi_esodwn > 30:
            flash('Value of Start of earnings must be between 0-30', 'form')
            errors = True
        if not isinstance(pososto, float):
            flash('Invalid type of Interest rate', 'form')
            errors = True
        elif pososto <=0 or pososto > 10:
            flash('Value of Interest rate must be between 0-10', 'form')
            errors = True
        if not isinstance(egguisi, float):
            flash('Invalid type of Deposit', 'form')
            errors = True
        elif egguisi <0 or egguisi > 1000000:
            flash('Value of Deposit must be between 0-1000000', 'form')
            errors = True
        if not isinstance(etos_egguisis, int):
            flash('Invalid type of Year of deposit return', 'form')
            errors = True
        elif etos_egguisis <0 or etos_egguisis > 30:
            flash('Value of Year of deposit return must be between 0-30', 'form')
            errors = True

        if errors:
            return render_template("form.html")

        else:
            # investment + deposit
            sun_ependusi = egguisi + ependusi

            # years list creation
            list_years = np.arange(0, years + 1, 1).tolist()

            #DCF list creation
            dcf = []
            for x in list_years:
                u = (1 + pososto) ** (-x)
                dcf.append(u)

            #list of earnings/ check each year with start of earnings value, if >= then insert the earnings per year, else insert 0
            i = 1
            list_earns = []
            for x in list_years:
                if x >= arxi_esodwn:
                    y = esoda_xrono
                    list_earns.append(y)
                    i += 1
                else:
                    list_earns.append(0)

            #check if deposit exist and insert it in the specific year
            for x in range(len(list_earns)):
                if egguisi:
                    if etos_egguisis == x:
                        list_earns[x] += egguisi

            #multiply the list of earnings with dcf list one by one
            lista_pragmatikwn = np.multiply(list_earns, dcf)

            #cumsums list_katharwn
            lista_sunolikwn_esodwn = np.cumsum(lista_pragmatikwn)

            #removal of investment in every value of list_katharwn list
            lista_katharwn_kerdwn = [x - sun_ependusi for x in lista_sunolikwn_esodwn]

            #depreciation year find
            depreciation_year= None
            for x in lista_katharwn_kerdwn:
                if x >= 0:
                    depreciation_year = lista_katharwn_kerdwn.index(x)
                    break

            #krataw mono ta duo dekadika psifia
            lista_katharwn_kerdwn = ['%.2f' % elem for elem in lista_katharwn_kerdwn]

            #roi list
            roi = []
            for x in lista_katharwn_kerdwn:
                y = (float(x) / sun_ependusi * 100)
                roi.append(y)

            # krataw mono ta duo dekadika psifia
            roi = ['%.2f' % elem for elem in roi]

            #create a string of the lists with all values divided by ","
            roi_values = ','.join(str(v) for v in roi)
            npv_values = ','.join(str(v) for v in lista_katharwn_kerdwn)

            #insert data to table user_data
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO user_data (years, ependusi, esoda_xrono, arxi_esodwn, pososto, egguisi, etos_egguisis, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (years, ependusi, esoda_xrono, arxi_esodwn, pososto, egguisi, etos_egguisis, session['userid']))
            data_id = cur.lastrowid
            #create session data_id
            session['data_id'] = data_id

            #insert results into program table
            cur.execute("INSERT INTO program (roi, npv, depre_year, user_id, data_id) VALUES (%s, %s, %s, %s, %s)", ([roi_values], [npv_values], depreciation_year, session['userid'], data_id))
            mysql.connection.commit()
            # create session prog_id
            session['prog_id'] = cur.lastrowid
            cur.close()

            #redirt to /line for charts
            return redirect(url_for('line'))


#show data def
@app.route('/data')
def show_data():
    #gets userid
    userid = session.get('userid')
    #check if userid exists
    if userid:
        #select all data for userid
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM user_data WHERE user_id=%s", (session['userid'],))
        #store data in result var
        result = cur.fetchall()
        cur.close()

        #redirect to data.hmtl with datass variable
        return render_template('data.html', datass=result)
    else:
        # redirect to data.hmtl without any data results
        return render_template('data.html')

#show data tools ( delete / view )
@app.route('/data', methods=["GET", "POST"])
def action():
    if request.method == 'POST':
        #get data_id from data selected row
        data_id = request.form['data_id']

        #delete
        if request.form['submit_button'] == 'delete':
            #delete selected data where data_id
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("DELETE FROM user_data WHERE id=%s", (data_id,))
            mysql.connection.commit()
            cur.close()
            #clears session data_id
            if session.get('data_id'):
                session.pop('data_id')
            flash('Data successfully Deleted')
            return redirect(url_for('show_data'))

        #view
        if request.form['submit_button'] == 'view':
            #select program id where data_id is equal to selected from form data id
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("select id from program where data_id=%s", (data_id,))
            result = cur.fetchone()
            #gets id value and clears it to be only a number
            result_str = str(result)
            result_num = re.findall(r"[-+]?\d*\.\d+|\d+", result_str)
            #create a session id with the id selected and cleared
            session['prog_id'] = result_num
            session['data_id'] = data_id
            cur.close()
            #redirect to /line with session progid and session data id
            return redirect(url_for('line'))
        else:
            return redirect(url_for('home'))

#manage user (show users)
@app.route('/manage')
def manage_users():
    #select all users
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM users")
    #store results
    result = cur.fetchall()
    cur.close()

    #redirect to manage.html with results stored as datass
    return render_template('manage.html', datass=result)

#manage users (delete, change role)
@app.route('/manage', methods=["GET", "POST"])
def manage_action():
    if request.method == 'POST':
        user_id = request.form['user_id']
        role = request.form['role']

        #delete user
        if request.form['submit_button'] == 'delete':
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            #delete user by selected id
            cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
            mysql.connection.commit()
            cur.close()
            flash('User successfully Deleted')

            #check if deleted user is the logged in user so after deleting session is cleared and user logged out
            user_id= int(user_id)
            x= int(session.get('userid'))
            if x == user_id:
                session.clear()
                return redirect(url_for('home'))

            return redirect(url_for('manage_users'))

        #update role
        if request.form['submit_button'] == 'update':
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            #updating selected id role
            cur.execute("UPDATE users SET role=%s where id=%s", (role, user_id,))
            mysql.connection.commit()
            cur.close()
            flash('Role successfully Updated')
            return redirect(url_for('manage_users'))
        else:
            return redirect(url_for('home'))

#dashboard
@app.route('/analytics')
def dash():
    # pie chart about users/admins

    #select admins
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT COUNT(role) FROM users WHERE role='admin'")
    result_admin = cur.fetchone()
    result_admin=str(result_admin)
    result_admin=re.sub("[^0-9]", "", result_admin)
    cur.close()

    #select users
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT COUNT(role) FROM users WHERE role='user'")
    result_user = cur.fetchone()
    result_user = str(result_user)
    result_user = re.sub("[^0-9]", "", result_user)
    cur.close()

    labels1 = [
        'Users', 'Admins'
    ]

    values1 = [
        result_user, result_admin,
    ]

    colors = [
        "#292b2c", "#99A2AA"]

    # chart data / month

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT COUNT(id) AS 'ID', EXTRACT(MONTH FROM reg_date) AS 'month' FROM user_data GROUP BY month ORDER BY month")
    result_1 = cur.fetchall()
    cur.close()

    # chart register users / month

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT COUNT(id) AS 'ID', EXTRACT(MONTH FROM reg_date) AS 'month' FROM users GROUP BY month ORDER BY month")
    result_2 = cur.fetchall()
    cur.close()

    # number of all register users

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT COUNT(id) FROM users")
    result_users = cur.fetchone()
    result_users = str(result_users)
    result_users = re.sub("[^0-9]", "", result_users)
    cur.close()

    # number of all register data

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT COUNT(id) FROM user_data")
    result_data = cur.fetchone()
    result_data = str(result_data)
    result_data = re.sub("[^0-9]", "", result_data)
    cur.close()

    return render_template('analytics.html', max=20, set=zip(values1, labels1, colors), datad=result_1, datau=result_2, users=result_users, data=result_data)


if __name__ == '__main__':
    app.secret_key = "^A%DJAJU^JJ123"
    app.run(debug=True)