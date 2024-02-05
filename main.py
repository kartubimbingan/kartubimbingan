from flask import Flask, render_template, jsonify, request, redirect, session
from flask_session import Session
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import datetime
import json


app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'BAD_SECRET_KEY'

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_DATABASE_PORT'] = 8080
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'kartu-bimbingan'
mysql = MySQL(app)

app.config.from_object(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/", methods=['GET', 'POST'])
def index():
    if not session.get('nim'):
        return redirect('/login/')
    
    return redirect('/pengajuan/')


@app.route("/login/", methods=['GET', 'POST'])
def login():
    if session.get('nim'):
        return redirect('/')

    return render_template('login.html')





@app.route("/pengajuan/", methods=['GET'])
def pengajuan():
    print(session.get('nim'))
    if not session.get('nim'):
        return redirect('/login/')
    
    if request.method == 'POST':
        data = request.form.to_dict(flat=False)
    
    return render_template('index.html')


@app.route("/cek-status/", methods=['GET'])
def cek_status():
    return render_template('cek-status.html')


@app.route("/data-pengajuan/", methods=['GET'])
def data_pengajuan():
    return render_template('data-pengajuan.html')


# ---------------------- GET ----------------------


@app.route("/api/get/mahasiswa/", methods=['GET'])
def get_mahasiswa():
    data = []
    if len(request.args['nim']) > 0:
        cursor = mysql.connection.cursor()
        cursor.execute(f"""SELECT * FROM mahasiswa WHERE nim LIKE '%{request.args['nim']}%'""")
        for mahasiswa in cursor.fetchall():
            data.append({'nim': mahasiswa[0], 'nama': mahasiswa[2], 'prodi': mahasiswa[3], 'pa': mahasiswa[4]})
    
    return jsonify(data)


@app.route("/api/get/dosen/", methods=['GET'])
def get_dosen():
    data = []
    if len(request.args.get('nama')) > 0:
        cursor = mysql.connection.cursor()
        if len(request.args.get('prodi')) > 0:
            cursor.execute(f"""SELECT * FROM dosen WHERE nama LIKE '%{request.args.get('nama')}%' AND prodi = '{request.args.get('prodi')}'""")
        else:
            cursor.execute(f"""SELECT * FROM dosen WHERE nama LIKE '%{request.args.get('nama')}%'""")
        for dosen in cursor.fetchall():
            data.append({'id_dosen': dosen[0], 'nama': dosen[1], 'prodi': dosen[2]})
    
    return jsonify(data)


# ---------------------- POST ----------------------
@app.route("/login-proccess/", methods=['POST'])
def login_proccess():
    data = request.json
    cursor = mysql.connection.cursor()
    cursor.execute(f"SELECT nim, password FROM mahasiswa WHERE nim = {data.get('nim')}")
    result = cursor.fetchall()
    if len(result) == 0:
        return jsonify({'status': 401, 'message': 'NIM atau password anda salah!'})
    
    salt = result[0][1]
    if bcrypt.check_password_hash(salt, data.get('password')):
        session['nim'] = data.get('nim')
        return jsonify({'status': 200}) 
    else:
        return jsonify({'status': 401, 'message': 'NIM atau password anda salah!'})


@app.route("/logout/")
def logout():
    session["nim"] = None
    return redirect("/")


@app.route('/api/post/kartu', methods=['POST'])
def post_kartu():
    data = request.json
    cursor = mysql.connection.cursor()
    cursor.execute(f"""SELECT * FROM kartu WHERE nim = %s AND jenis_kartu = %s""", (data.get('nim'), data.get('jenis-kartu')))
    if not len(cursor.fetchall()) > 0:
        date = str(datetime.date.strftime(datetime.datetime.strptime(data.get('tanggal-surat'), '%d/%m/%Y'), "%Y-%m-%d"))
        cursor.execute(f"""INSERT INTO kartu (nim, pembimbing_1, pembimbing_2, judul, jenis_kartu, tanggal_surat, nomor_surat, selesai) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (data.get('nim'), data.get('id-pembimbing-1'), data.get('id-pembimbing-2'), data.get('judul-proposal'), data.get('jenis-kartu'), date, data.get('nomor-surat'), 0))
        cursor.execute(f"""INSERT INTO lacak_kartu (id_kartu, tiba_di, tanggal) VALUES (%s, %s, %s)""", (cursor.lastrowid, "Prodi", date))
        mysql.connection.commit()
        return jsonify({'status': 200, 'message': 'Pengajuan berhasil! Mohon cek status pengajuan pada halaman \"Cek Status\" secara berkala!'})
    else:
        return jsonify({'status': 400, 'message': f'Anda sudah pernah melakukan pengajuan kartu {data.get("jenis-kartu").lower()} sebelumnya, mohon mengubah pengajuan atau menghubungi petugas!'})
    
    return jsonify({'status': 500, 'message': f'[500] Error: Internal server, Error code : 0x00000001! Harap hubungi programmer!'})


@app.route('/test/', methods=['GET', 'POST'])
def test():
    cursor = mysql.connection.cursor()
    cursor.execute(f"""SELECT * FROM mahasiswa""")
    # pwd = bcrypt.generate_password_hash("unhijaya").decode('utf-8')
    # for mahasiswa in cursor.fetchall():
    #     # cursor.execute(f"""UPDATE mahasiswa SET password = %s WHERE nim = %s""", (pwd, mahasiswa[0]))
    #     print(bcrypt.check_password_hash(mahasiswa[1], 'unhijaya'))

    # # mysql.connection.commit()
    return jsonify({'status': 200})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
