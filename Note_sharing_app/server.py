import bcrypt
import jwt
import base64
import datetime
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify , send_file
import os
from Crypto.Random import get_random_bytes
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials 
from urllib.parse import urlparse, parse_qs, unquote_plus
# Kết nối đến MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["users"]
users_collection = db["user"]
notes_collection = db["note"]

app = Flask(__name__)
app.config['SECRET_KEY'] = 'f3bb24e89d40f38349b441c9d7ebc3b7c7df431617bc3d4675df85cbb48e8de5'

# Đăng ký người dùng
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    # Kiểm tra nếu tên đăng nhập đã tồn tại
    if users_collection.find_one({"username": data['username']}):
        return jsonify({"message": "Username already exists!"}), 400
    # Băm mật khẩu với salt
    password = data['password'].encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password, salt)
    # Lưu thông tin người dùng vào MongoDB
    users_collection.insert_one({
        "username": data['username'],
        "password": hashed_password
    })
    return jsonify({"message": "User registered successfully!"}), 201

# Đăng nhập người dùng
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = users_collection.find_one({"username": data['username']})
    if not user:
        return jsonify({"message": "User not found!"}), 404
    # Kiểm tra mật khẩu
    if bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
        # Tạo JWT token
        token = jwt.encode({
            'username': user['username'],
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)  # Hết hạn sau 1 giờ
        }, app.config['SECRET_KEY'], algorithm='HS256')
        # Cập nhật trường 'token' trong database cho người dùng
        users_collection.update_one(
            {"username": user['username']},  # Điều kiện tìm người dùng
            {"$set": {"token": token}}  # Cập nhật trường 'token'
        )
        return jsonify({"message": "Login successful", "token": token}), 200
    else:
        return jsonify({"message": "Invalid password!"}), 400


# Thêm ghi chú
@app.route('/notes', methods=['POST'])
def add_notes():
    data = request.get_json()
    existing_note = notes_collection.find_one({"name": data['name']})
    if existing_note:
        return jsonify({"error": "Name already exists in the database!"}), 400
    # Thêm ghi chú vào database
    notes_collection.insert_one({
        "username": data['username'],
        "name": data['name'],
        "file_extension": data['file_extension'],
        "key": data['key'],
        "encrypted_data": data['encrypted_data']
    })
    return jsonify({"message": "Notes added successfully!"}), 200

# Lấy ghi chú
@app.route('/notes', methods=['GET'])
def get_notes():
    username = request.args.get('username')
    # Lấy tất cả ghi chú của người dùng
    notes = list(notes_collection.find({"username": username}, {"_id": 0}))
    return jsonify({"notes": notes}), 200

# Xóa ghi chú
@app.route('/notes', methods=['DELETE'])
def delete_notes():
    data = request.get_json()
    # Xóa ghi chú khỏi database
    notes_collection.delete_one({
        "username": data['username'],
        "name": data['name']
    })
    return jsonify({"message": "Notes deleted successfully!"}), 200






##################################################################################################
# Khởi tạo Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.file']
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

def upload_to_google_drive(file_path, file_name):
    """
    Tải file lên Google Drive và trả về URL chia sẻ.
    """
    # Tải file lên Google Drive
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, mimetype='application/octet-stream')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    # Thiết lập quyền chia sẻ công khai
    file_id = file.get('id')
    drive_service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()
    
    # Tạo URL chia sẻ
    share_url = f"https://drive.google.com/uc?id={file_id}&export=download"
    return share_url



UPLOAD_FOLDER = './uploads'  # Thư mục lưu file
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# API upload file
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part!"}), 400

    file = request.files['file']
    note_name = request.form.get('note_name')  # Lấy tên ghi chú
    if not note_name:
        return jsonify({"message": "Missing note name!"}), 400

    if file.filename == '':
        return jsonify({"message": "No selected file!"}), 400

    # Lưu file tạm thời trên server
    filename = secure_filename(file.filename)
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(temp_path)

    try:
        # Tải file lên Google Drive
        google_drive_url = upload_to_google_drive(temp_path, filename)

        # Xóa file tạm
        os.remove(temp_path)

        # Lưu thông tin vào cơ sở dữ liệu
        db['files'].insert_one({
            "note_id": note_name,
            "filename": filename,
            "google_drive_url": google_drive_url
        })

        return jsonify({"message": "File uploaded successfully!", "download_url": google_drive_url}), 201
    except Exception as e:
        # Xóa file tạm nếu xảy ra lỗi
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"message": f"Failed to upload file: {str(e)}"}), 500
# API tải file qua URL
@app.route('/download/<token>', methods=['GET'])
def download_file(token):
    try:
        # Giải mã token
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        file_path = data.get('file_path')  # Sử dụng .get() để tránh KeyError
        app.logger.info(f"Decoded token data: {data}")
        app.logger.info(f"Checking file path: {file_path}")
        # Kiểm tra file_path có tồn tại không
        if not file_path or not os.path.exists(file_path):
            return jsonify({"message": "File not found!"}), 404

        # Trả về file để tải xuống
        return send_file(file_path, as_attachment=True)
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "The link has expired!"}), 400
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token!"}), 400
    

@app.route('/share', methods=['POST'])
def share_url():
    data = request.get_json()
    note_id = data.get('note_id')

    if not note_id:
        return jsonify({"message": "Thiếu note ID!"}), 400

    # Kiểm tra nếu URL đã tồn tại và chưa hết hạn
    shared_entry = db['shared_urls'].find_one({"note_id": note_id})
    if shared_entry:
        expiration_time = shared_entry['expiration_time']
        if datetime.datetime.utcnow() < expiration_time:
            remaining_time = (expiration_time - datetime.datetime.utcnow()).total_seconds()
            return jsonify({
                "message": "URL đã tồn tại!",
                "url": shared_entry['google_drive_url'],
                "remaining_time": remaining_time
            }), 200

    # Truy vấn ghi chú trong database
    note = notes_collection.find_one({"name": note_id})
    if not note:
        return jsonify({"message": "Không tìm thấy ghi chú!"}), 404

    key = note['key']
    encrypted_data = base64.b64decode(note['encrypted_data'])
    temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{note_id}.encrypted")
    file_extension = note['file_extension']

    with open(temp_file_path, 'wb') as temp_file:
        temp_file.write(encrypted_data)

    try:
        # Tải file lên Google Drive
        google_drive_url = upload_to_google_drive(temp_file_path, f"{note_id}.encrypted")

        # Thêm key vào URL dưới dạng query parameter
        secure_url = f"{google_drive_url}&key={key}"

        # Xóa file tạm
        os.remove(temp_file_path)

        # Cập nhật thời gian hết hạn
        expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

        # Lưu URL vào database
        db['shared_urls'].replace_one(
            {"note_id": note_id},  # Điều kiện tìm kiếm
            {
                "note_id": note_id,
                "google_drive_url": secure_url,
                "expiration_time": expiration_time,
                "file_name": f"{note_id}{file_extension}"  # Đúng định dạng file
            },
            upsert=True  # Tạo mới nếu không tồn tại
        )

        # Trả về link chia sẻ
        return jsonify({
            "message": "Tạo URL thành công!",
            "url": secure_url,
            "remaining_time": 600  # Thời gian còn lại là 10 phút
        }), 200
    except Exception as e:
        # Xóa file tạm nếu có lỗi
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return jsonify({"message": f"Lỗi khi tải lên Google Drive: {str(e)}"}), 500

SERVICE_ACCOUNT_FILE = 'credentials.json'
def build_drive_service():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds) 
@app.route('/revoke', methods=['POST'])
def revoke_url():
    data = request.get_json()
    print(data)
    input_url = data.get('url')

    if not input_url:
        return jsonify({"message": "Thiếu URL để hủy!"}), 400

    # Tách thông tin từ URL
    try:
        parsed_url = urlparse(input_url)
        query_params = parse_qs(parsed_url.query)
        file_id = query_params.get('id', [None])[0]
        key = query_params.get('key', [None])[0]

        if not file_id or not key:
            return jsonify({"message": "URL thiếu thông tin file_id hoặc key!"}), 400
    except Exception as e:
        return jsonify({"message": f"Lỗi phân tích URL: {str(e)}"}), 400

    # Tìm link chia sẻ trong database
    shared_url_entry = db['shared_urls'].find_one({"google_drive_url": input_url})
    if not shared_url_entry:
        return jsonify({"message": "Không tìm thấy URL để hủy!"}), 404

    # Hủy quyền truy cập trên Google Drive
    try:
        drive_service = build_drive_service()
        drive_service.files().delete(fileId=file_id).execute()
    except Exception as e:
        return jsonify({"message": f"Lỗi khi xóa file trên Google Drive: {str(e)}"}), 500

    # Xóa URL khỏi database
    db['shared_urls'].delete_one({"google_drive_url": input_url})

    return jsonify({"message": "URL đã bị hủy và xóa thành công!"}), 200

@app.route('/validate_url', methods=['POST'])
def validate_url():
    data = request.get_json()

    input_url = data.get('url')

    # Phân tích URL để lấy key và id
    parsed_url = urlparse(input_url)
    query_params = parse_qs(parsed_url.query)
    key = query_params.get('key', [None])[0]  # Lấy key từ query parameters
    file_id = query_params.get('id', [None])[0]  # Lấy id từ query parameters

    if key:
        key = key.replace(' ', '+')
    
    # Kiểm tra key và id có tồn tại trong URL không
    if not key or not file_id:
        return jsonify({"message": "URL thiếu thông tin key hoặc id!"}), 400

    # Tìm trong database với id và key
    shared_entry = db['shared_urls'].find_one({
        "google_drive_url": {"$regex": f"id={file_id}"},  # Tìm `id` trong URL
    })
    if not shared_entry:
        return jsonify({"message": "URL hoặc key không tồn tại trong hệ thống!"}), 404

    # Lấy thông tin file từ database
    download_url = shared_entry.get("google_drive_url")
    file_extension = shared_entry.get("file_name", "").split(".")[-1]

    # Trả về thông tin nếu tìm thấy
    return jsonify({
        "download_url": download_url,
        "key": key,
        "file_extension": file_extension
    }), 200

# Chạy server Flask
if __name__ == '__main__':
    app.run(debug=True)
