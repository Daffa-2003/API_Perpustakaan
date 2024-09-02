import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from OpenAI import klasifikasiKeyword as keywords
from flask_jwt_extended import create_access_token, JWTManager
from sqlalchemy import or_


app = Flask(__name__)
CORS(app)

# url = 'postgresql://postgres:daffa@localhost/Perpustakaan'
url = 'postgresql://postgres:otobook24@otobook24.ch600aquk67o.us-east-1.rds.amazonaws.com:5432/mf_perpus'

app.config['SQLALCHEMY_DATABASE_URI'] = url
db = SQLAlchemy(app)
migrate = Migrate(app, db)

UPLOAD_FOLDER = './uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
UPLOAD_FOTOPROFILE = './fotoProfile/'
app.config['UPLOAD_FOTOPROFILE'] = UPLOAD_FOTOPROFILE
ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'gif'}

app.config['JWT_SECRET_KEY'] = 'nalsdasdlkjasjfkmkj21kjklj4jkg12hgasf'
jwt = JWTManager(app)

class MasterBuku(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    judul = db.Column(db.String(250), nullable=False)
    pengarang = db.Column(db.String(250), nullable=False)
    penerbitan = db.Column(db.String(250), nullable=False)
    deskripsi = db.Column(db.String(250), nullable=False)
    isbn = db.Column(db.String(100), nullable=False, unique=True)
    dateTime = db.Column(db.DateTime, nullable=True, default=db.func.now(), onupdate=db.func.now())

    # Menambahkan relasi dengan cascade delete dan nama backref yang unik
    cover_buku = db.relationship('CoverBuku', backref='master_buku_cover', cascade="all, delete-orphan", lazy=True)
    sinopsis_buku = db.relationship('SinopsisBuku', backref='master_buku_sinopsis', cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f"<MasterBuku {self.id}>"

class CoverBuku(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    master_buku_id = db.Column(db.Integer, db.ForeignKey('master_buku.id'), nullable=False)
    cover = db.Column(db.String(250), nullable=False)
    path = db.Column(db.String(250), nullable=False)
    
    def __repr__(self):
        return f"<CoverBuku {self.id}>"

class SinopsisBuku(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sinopsis = db.Column(db.Text, nullable=False)
    keyword = db.Column(db.Text, nullable=False)
    dateTime = db.Column(db.DateTime, nullable=True, default=db.func.now(), onupdate=db.func.now())
    master_buku_id = db.Column(db.Integer, db.ForeignKey('master_buku.id'), nullable=False, unique=True)
    
    def __repr__(self):
        return f"<SinopsisBuku {self.id}>"
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(250), nullable=False) 
    email = db.Column(db.String(250), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False)
    fotoprofile = db.Column(db.String(250), nullable=True)
    path = db.Column(db.String(250), nullable=True)
    dateTime = db.Column(db.DateTime, nullable=True, default=db.func.now(), onupdate=db.func.now())
    
    def __init__(self, username, email, password) -> None:
        super().__init__()
        self.username = username
        self.email = email
        self.password = Bcrypt().generate_password_hash(password).decode('utf-8')
        
    def __repr__(self):
        return f"<User {self.id}>"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS


##### USER #####

# endpoint untuk menambahkan data user
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        user = User(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User berhasil ditambahkan'}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 400

# endpoint untuk login
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        if user is None:
            return jsonify({'message': 'User tidak ditemukan'}), 404
        if Bcrypt().check_password_hash(user.password, data['password']):   
            access_token = create_access_token(identity=user.id)
            return jsonify({'access_token': access_token, 'id' : user.id}), 200
        else:
            return jsonify({'message': 'Password salah'}), 400
    except Exception as e:
        return jsonify({'message': str(e)}), 400
    

    
# get user
@app.route('/api/getUser', methods=['GET'])
def getUser():
    try:
        user = User.query.all()
        userList = []
        for u in user:
            userList.append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
            })
        return jsonify({"data":userList}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

# get  user 
@app.route('/api/getUser/<id>', methods=['GET'])
def getUserLogin(id):
    try:
        user = User.query.filter_by(id=id).first()
        if user is None:
            return jsonify({'message': 'Data tidak ditemukan'}), 404
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'fotoprofile' : user.fotoprofile,
            'path' : user.path
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

# edit user by id
@app.route('/api/editUser/<id>', methods=['PUT'])
def editUser(id):
    try:
        user = User.query.filter_by(id=id).first()
        if user is None:
            return jsonify({'message': 'Data tidak ditemukan'}), 404

        # Jika ada file dalam permintaan, tangani sebagai form-data
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'message': 'No selected file'}), 400
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOTOPROFILE'], filename))
                master = {
                    'username': request.form['username'],
                    'email': request.form['email'],
                    'fotoprofile': filename,
                    'path': f'/fotoProfile/{filename}'
                }
                for key, value in master.items():
                    setattr(user, key, value)
                db.session.commit()
                return jsonify({'message': 'Data berhasil diubah'}), 200
            else:
                return jsonify({'message': 'File tidak valid'}), 400

        # Jika tidak ada file, harapkan data dalam bentuk JSON
        elif request.content_type == 'application/json':
            data = request.get_json()
            master = {
                'username': data['username'],
                'email': data['email']
            }
            for key, value in master.items():
                setattr(user, key, value)
            db.session.commit()
            return jsonify({'message': 'Data berhasil diubah'}), 200
        else:
            return jsonify({'message': 'Unsupported Media Type'}), 415

    except Exception as e:
        return jsonify({'message': str(e)}), 400


@app.route('/fotoProfile/<filename>', methods=['GET'])
def get_profile(filename):
    return send_from_directory(app.config['UPLOAD_FOTOPROFILE'], filename)

# logout
@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        # Hanya kembalikan pesan sukses
        return jsonify({'message': 'Logout berhasil'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

##### BUKU #####

# endpoint untuk menambahkan data buku
@app.route('/api/addBuku', methods=['POST'])
def addBuku():
    try:
        data = request.get_json()
        # subjek = generate_keywords_openai(data['abstrak'])
        # abstract = summarization.summarize(data['abstrak'])
        buku = MasterBuku(
            judul = data['judul'],
            isbn = data['isbn'],
            pengarang = data['pengarang'],
            penerbitan = data['penerbitan'],
            deskripsi = data['deskripsi'],
            # abstrak = abstract,
        )
        db.session.add(buku)
        db.session.commit()
        return jsonify({'message': 'Data berhasil ditambahkan'}),201
    except Exception as e:
        return jsonify({'message': str(e)}), 400

# get buku 
@app.route('/api/getBuku', methods=['GET'])
def getBuku():
    try:
        buku = MasterBuku.query.all()
        bukuList = []
        for b in buku:
            bukuList.append({
                'id': b.id,
                'judul': b.judul,
                'pengarang': b.pengarang,
                'penerbitan': b.penerbitan,
                'deskripsi': b.deskripsi,
                'isbn': b.isbn
            })
        return jsonify({"data":bukuList}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400
    

# get buku and sinopsis
@app.route('/api/getBukuSinopsis', methods=['GET'])
def getBukuSinopsis():
    try:
        buku = MasterBuku.query.all()
        sinopsis = SinopsisBuku.query.all()
        bukuList = []
        for b in buku:
            for s in sinopsis:
                if b.id == s.master_buku_id:
                    bukuList.append({
                        'id': b.id,
                        'judul': b.judul,
                        'pengarang': b.pengarang,
                        'penerbitan': b.penerbitan,
                        'deskripsi': b.deskripsi,
                        'isbn': b.isbn,
                        'sinopsis': s.sinopsis,
                        'keyword': s.keyword
                    })
        return jsonify({"data":bukuList}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400
    

# get buku by id 
@app.route("/api/getBuku/<id>", methods=['GET'])
def getBukuById(id):
    buku = MasterBuku.query.filter_by(id=id).first()
    if buku is None:
        return jsonify({'message': 'Data tidak ditemukan'}), 404
    return jsonify({
        'id': buku.id,
        'judul': buku.judul,
        'pengarang': buku.pengarang,
        'penerbitan': buku.penerbitan,
        'deskripsi': buku.deskripsi,
        'isbn': buku.isbn
    }), 200

# edit buku by id
@app.route('/api/editBuku/<id>', methods=['PUT'])
def editBuku(id):
    try:
        buku = MasterBuku.query.filter_by(id=id).first()
        if buku is None:
            return jsonify({'message': 'Data tidak ditemukan'}), 404
        data = request.get_json()
        master = {
            'judul': data['judul'],
            'pengarang': data['pengarang'],
            'penerbitan': data['penerbitan'],
            'deskripsi': data['deskripsi'],
            'abstrak': data['abstrak'],
            'isbn': data['isbn'],
            'subjek': data['subjek']
        }
        for key, value in master.items():
            setattr(buku, key, value)
        db.session.commit()
        return jsonify({'message': 'Data berhasil diubah'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400



# delete buku by id
@app.route('/api/deleteBuku/<id>', methods=['DELETE'])
def deleteBuku(id):
    try:
        buku = MasterBuku.query.filter_by(id=id).first()
        if buku is None:
            return jsonify({'message': 'Data tidak ditemukan'}), 404
        db.session.delete(buku)
        db.session.commit()
        return jsonify({'message': 'Data berhasil dihapus'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400


# add cover
@app.route('/api/uploadCover/<master_buku_id>', methods=['POST'])
def uploadCover(master_buku_id):
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        cover = CoverBuku(
            master_buku_id = master_buku_id,
            cover = filename,
            path=f'uploads/{filename}'
        )
        db.session.add(cover)
        db.session.commit()
        return jsonify({'message': 'Cover berhasil diupload'}), 201
    else:
        return jsonify({'message': 'File tidak valid'}), 400

# get cover by id
@app.route('/api/getCover/<master_buku_id>', methods=['GET'])
def getCover(master_buku_id):
    cover = CoverBuku.query.filter_by(master_buku_id=master_buku_id).first()
    if cover is None:
        return jsonify({'message': 'Data tidak ditemukan'}), 404
    return jsonify({
        'id': cover.id,
        'master_buku_id': cover.master_buku_id,
        'cover': cover.cover,
        'path': f'/uploads/{cover.cover}'
    }), 200
    

@app.route('/uploads/<filename>', methods=['GET'])
def get_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    

# edit cover by id
@app.route('/api/editCover/<id>', methods=['PUT'])
def editCover(id):
    try:
        cover = CoverBuku.query.filter_by(id=id).first()
        if cover is None:
            return jsonify({'message': 'Data tidak ditemukan'}), 404
        data = request.get_json()
        master = {
            'master_buku_id': data['master_buku_id'],
            'cover': data['cover'],
            'path': data['path']
        }
        for key, value in master.items():
            setattr(cover, key, value)
        db.session.commit()
        return jsonify({'message': 'Data berhasil diubah'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400
    
# delete cover by id
@app.route('/api/deleteCover/<id>', methods=['DELETE'])
def deleteCover(id):
    try:
        cover = CoverBuku.query.filter_by(id=id).first()
        if cover is None:
            return jsonify({'message': 'Data tidak ditemukan'}), 404
        db.session.delete(cover)
        db.session.commit()
        return jsonify({'message': 'Data berhasil dihapus'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400
    
# add sinopsis
@app.route('/api/addSinopsis/<master_buku_id>', methods=['POST'])
def addSinopsis(master_buku_id):
    try:
        data = request.get_json()
        sinopsis = SinopsisBuku(
            sinopsis = data['sinopsis'],
            keyword = data['keyword'],
            master_buku_id = master_buku_id
        )
        db.session.add(sinopsis)
        db.session.commit()
        return jsonify({'message': 'Data berhasil ditambahkan'}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 400

# get sinopsis by master_buku_id
@app.route('/api/getSinopsis/<master_buku_id>', methods=['GET'])
def getSinopsis(master_buku_id):
    try:
        sinopsis = SinopsisBuku.query.filter_by(master_buku_id=master_buku_id).first()
        if sinopsis is None:
            return jsonify({'message': 'Data tidak ditemukan'}), 404
        return jsonify({
            'id': sinopsis.id,
            'sinopsis': sinopsis.sinopsis,
            'keyword': sinopsis.keyword,
            'master_buku_id': sinopsis.master_buku_id
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400
    


# get klasifikasi keyword by sinopsis 
@app.route('/api/getklasifikasi', methods=['POST'])
def klasifikasi():
    try:
        data = request.get_json()
        key = keywords.generate_keywords_openai(data['sinopsis'])
        return jsonify({'keywords': key}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

# get book and sinopsis by id
@app.route('/api/getBookSinopsis/<id>', methods=['GET'])
def getBookSinopsis(id):
    try:
        buku = MasterBuku.query.filter_by(id=id).first()
        if buku is None:
            return jsonify({'message': 'Data tidak ditemukan'}), 404
        sinopsis = SinopsisBuku.query.filter_by(master_buku_id=id).first()
        if sinopsis is None:
            return jsonify({'message': 'Data tidak ditemukan'}), 404
        return jsonify({
            'judul': buku.judul,
            'pengarang': buku.pengarang,
            'penerbitan': buku.penerbitan,
            'deskripsi': buku.deskripsi,
            'isbn': buku.isbn,
            'sinopsis': sinopsis.sinopsis,
            'keyword': sinopsis.keyword
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400
    

# edit sinopsis and buku by id
@app.route('/api/editBookSinopsis/<id>', methods=['PUT'])
def editBookSinopsis(id):
    try:
        buku = MasterBuku.query.filter_by(id=id).first()
        data = request.get_json()
        books = {
            'judul': data['judul'],
            'pengarang': data['pengarang'],
            'penerbitan': data['penerbitan'],
            'deskripsi': data['deskripsi'],
            'isbn': data['isbn']
        }
        for key, value in books.items():
            setattr(buku, key , value)
        sinopsis = SinopsisBuku.query.filter_by(master_buku_id=id).first()
        sinops = {
            'sinopsis': data['sinopsis'],
            'keyword': data['keyword']
        }
        for key, value in sinops.items():
            setattr(sinopsis, key, value)
        db.session.commit()
        return jsonify({'message': 'Data berhasil diubah'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

# search buku by keyword
@app.route('/api/searchBuku', methods=['POST'])
def searchBuku():
    try:
        data = request.get_json()
        # sinopsis = SinopsisBuku.query.filter(SinopsisBuku.keyword.like(f"%{keyword['keyword']}%")).all()
        sinopsis = SinopsisBuku.query.filter(or_(SinopsisBuku.keyword.ilike(f"%{data['keyword']}%"), MasterBuku.judul.ilike(f"%{data['keyword']}%"))).join(MasterBuku, SinopsisBuku.master_buku_id == MasterBuku.id).all()
        bukuList = []
        for s in sinopsis:
           bukuList.append({
                'id': s.master_buku_id,
                'judul': s.master_buku_sinopsis.judul,  # Akses melalui backref
                'pengarang': s.master_buku_sinopsis.pengarang,
                'penerbitan': s.master_buku_sinopsis.penerbitan,
                'deskripsi': s.master_buku_sinopsis.deskripsi,
                'isbn': s.master_buku_sinopsis.isbn,
                'sinopsis': s.sinopsis,
                'keyword': s.keyword
            })
        # buku tanpa sinopsis dan keyword
        buku_query = MasterBuku.query.filter(MasterBuku.judul.ilike(f"%{data['keyword']}%")).outerjoin(SinopsisBuku, MasterBuku.id == SinopsisBuku.master_buku_id).filter(SinopsisBuku.id.is_(None)).all()
        for b in buku_query:
            bukuList.append({
                'id': b.id,
                'judul': b.judul,
                'pengarang': b.pengarang,
                'penerbitan': b.penerbitan,
                'deskripsi': b.deskripsi,
                'isbn': b.isbn,
                'sinopsis': None,
                'keyword': None
            })
        return jsonify({"data":bukuList}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
