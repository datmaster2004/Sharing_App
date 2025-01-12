import bcrypt
import jwt
import datetime
from pymongo import MongoClient
from flask import Flask, request, jsonify

# Kết nối đến MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["users"]
users_collection = db["user"]

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
# Chạy server Flask
if __name__ == '__main__':
    app.run(debug=True)
