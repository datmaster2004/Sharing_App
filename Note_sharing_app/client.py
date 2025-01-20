import tkinter as tk
from tkinter import filedialog, messagebox
import re
import pyperclip  # Dùng để copy vào clipboard
import os
import base64
import requests
from Crypto.Cipher import AES 
from Crypto.Random import get_random_bytes 
from pymongo import MongoClient
import tkinter as tk
from tkinter import messagebox
import pyperclip  # Dùng để copy vào clipboard
import requests
from datetime import datetime, timedelta

# Hàm căn giữa cửa sổ
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

# Hàm kiểm tra tính hợp lệ của mật khẩu
def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):  # Ít nhất 1 chữ cái in hoa
        return False
    if not re.search(r"[0-9]", password):  # Ít nhất 1 số
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):  # Ít nhất 1 ký tự đặc biệt
        return False
    return True

# Danh sách ghi chú
notes = []

# Biến toàn cục lưu tên đăng nhập
global_username = ""
# Hàm căn giữa cửa sổ
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

# Hàm giải mã dữ liệu
def decrypt_data(encrypted_data, key):
    # Tách IV và ciphertext từ dữ liệu mã hóa
    iv = encrypted_data[:16]  # Lấy 16 byte đầu tiên làm IV
    ciphertext = encrypted_data[16:]
    # Khởi tạo đối tượng cipher AES với khóa và IV
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # Giải mã dữ liệu
    plaintext = cipher.decrypt(ciphertext)
    # Loại bỏ padding
    padding_length = plaintext[-1]  # Byte cuối cùng cho biết độ dài padding
    plaintext = plaintext[:-padding_length]  # Loại bỏ padding
    return plaintext
    
# Hàm tải file về máy
def download_file(datas):
    # Tạo thư mục "note_list" nếu chưa tồn tại
    directory = os.path.join(os.getcwd(), "note_list")
    if not os.path.exists(directory):
        os.makedirs(directory)
    for data in datas:
        username = data['username']
        name = data['name']
        file_extension = data['file_extension']
        key = base64.b64decode(data['key'])
        encrypted_data = base64.b64decode(data['encrypted_data'])
        # Giải mã dữ liệu
        decrypted_data = decrypt_data(encrypted_data, key)
        # Lưu dữ liệu vào file
        file_name = f"{username}_{name}.{file_extension}"
        file_path = os.path.join(directory, file_name)
        with open(file_path, "wb") as f:
            f.write(decrypted_data)
        # Thêm dữ liệu vào mảng notes
        notes.append({"name": name, "file": file_path})
    messagebox.showinfo("Thành công", "File đã được tải xuống thành công!")

# Hàm lấy file từ server
def get_notes():
    username = global_username
    try:
        response = requests.get('http://127.0.0.1:5000/notes', params={"username": username})
        if response.status_code == 200:
            datas = response.json()["notes"]
            messagebox.showinfo("Thành công", "Dữ liệu đã được tải về!")
        else:
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu: {response.text}")
        download_file(datas)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không tải được dữ liệu: {str(e)}")

# Hàm hiển thị cửa sổ tạo URL
def show_create_url_window(parent_window, note_name):
    """
    Hiển thị cửa sổ tạo URL, gửi yêu cầu tạo URL đến server và quản lý giao diện.
    """
    parent_window.withdraw()
    create_url_window = tk.Toplevel(parent_window)
    create_url_window.title("Tạo URL")
    center_window(create_url_window, 500, 400)
    create_url_window.configure(bg="#f8f9fa")
    
    # Lấy file path từ danh sách ghi chú
    file_path = next((note["file"] for note in notes if note["name"] == note_name), None)

    if not file_path:
        messagebox.showerror("Lỗi", "Không tìm thấy file liên quan đến ghi chú!")
        parent_window.deiconify()
        return

    url_label = tk.Label(
        create_url_window,
        text="URL sẽ hiển thị ở đây sau khi tạo.",
        font=("Helvetica", 12),
        bg="#f8f9fa",
        fg="#343a40",
        wraplength=450,
        justify="center"
    )
    url_label.pack(pady=10)

    countdown_time = [600]  # Thời gian đếm ngược 10 phút
    def go_back():
        create_url_window.destroy()
        parent_window.deiconify()
    def update_timer():
        """Cập nhật đồng hồ đếm ngược."""
        if countdown_time[0] > 0:
            minutes, seconds = divmod(countdown_time[0], 60)
            timer_label.config(text=f"Thời gian còn lại: {minutes:02}:{seconds:02}")
            countdown_time[0] -= 1
            create_url_window.after(1000, update_timer)
        else:
            messagebox.showinfo("Hết giờ", "Thời gian chia sẻ URL đã hết!")
            cancel_share()

    def generate_url():
        """Gọi API để tạo URL và cập nhật giao diện."""
        try:
            response = requests.post(
                'http://localhost:5000/share',
                json={"note_id": note_name}  # Gửi note_id để kiểm tra hoặc tạo URL
            )

            # Kiểm tra phản hồi từ server
            if response.status_code == 200:
                data = response.json()
                download_url = data["url"]
                remaining_time = data["remaining_time"]

                # Cập nhật giao diện
                url_label.config(text=f"URL tải xuống: {download_url}")
                pyperclip.copy(download_url)  # Copy URL vào clipboard
                messagebox.showinfo("Thành công", "URL đã được tạo và sao chép vào clipboard!")

                # Cập nhật bộ đếm
                countdown_time[0] = int(remaining_time)
                update_timer()  # Bắt đầu hoặc cập nhật đếm giờ
            else:
                messagebox.showerror("Lỗi", response.json().get("message", "Không thể tạo URL!"))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Lỗi", f"Không thể kết nối với server: {str(e)}")

    def copy_to_clipboard():
        """Sao chép URL vào clipboard."""
        pyperclip.copy(url_label.cget("text").replace("URL tải xuống: ", ""))
        messagebox.showinfo("Copy", "URL đã được sao chép vào clipboard!")

    def cancel_share():
        """Hủy chia sẻ URL."""
        try:
            # Lấy URL từ giao diện (ví dụ: từ nhãn URL đã tạo)
            shared_url = url_label.cget("text").replace("URL tải xuống: ", "").strip()

            if not shared_url:
                messagebox.showerror("Lỗi", "Không tìm thấy URL để hủy chia sẻ!")
                return

            # Gửi yêu cầu đến server để hủy chia sẻ
            response = requests.post("http://localhost:5000/revoke", json={"url": shared_url})
            if response.status_code == 200:
                messagebox.showinfo("Hủy chia sẻ", "URL đã bị hủy thành công!")
            else:
                error_message = response.json().get("message", "Không thể hủy URL")
                messagebox.showerror("Lỗi", f"Hủy chia sẻ thất bại: {error_message}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Hủy chia sẻ thất bại: {str(e)}")
        finally:
            # Đóng cửa sổ tạo URL và quay lại cửa sổ cha
            create_url_window.destroy()
            parent_window.deiconify()



    # Nút quay lại
    back_button = tk.Button(
        create_url_window,
        text="← Quay lại",
        font=("Helvetica", 10),
        bg="#007bff",
        fg="white",
        activebackground="#0056b3",
        activeforeground="white",
        relief="flat",
        command=go_back
    )
    back_button.place(x=10, y=10)
    

    # Nút sao chép URL
    copy_button = tk.Button(
        create_url_window,
        text="Copy URL",
        font=("Helvetica", 12),
        bg="#007bff",
        fg="white",
        activebackground="#0056b3",
        activeforeground="white",
        relief="flat",
        command=copy_to_clipboard
    )
    copy_button.pack(pady=10)

    # Nút hủy chia sẻ
    cancel_button = tk.Button(
        create_url_window,
        text="Hủy chia sẻ",
        font=("Helvetica", 12),
        bg="#dc3545",
        fg="white",
        activebackground="#c82333",
        activeforeground="white",
        relief="flat",
        command=cancel_share
    )
    cancel_button.pack(pady=10)

    # Đồng hồ đếm ngược
    timer_label = tk.Label(
        create_url_window,
        text="Thời gian còn lại: 10:00",
        font=("Helvetica", 12),
        bg="#f8f9fa",
        fg="#343a40"
    )
    timer_label.pack(pady=10)
    generate_url()



# Hàm hiển thị danh sách ghi chú - Liệt kê ghi chú 
def show_notes_list_window(parent_window):
    parent_window.withdraw()
    list_window = tk.Toplevel(parent_window)
    list_window.title("Danh sách ghi chú")
    center_window(list_window, 600, 400)
    list_window.configure(bg="#f8f9fa")

    def go_back():
        list_window.destroy()
        parent_window.deiconify()


    def delete_note(note_index):
        # Khai báo thư mục lưu file và tạo nếu không tồn tại
        directory = os.path.join(os.getcwd(), "note_list")  
        if not os.path.exists(directory):
            os.makedirs(directory)
        # Xóa file theo đường dẫn được lưu trong danh sách notes
        file_path = notes[note_index]['file']
        if os.path.exists(file_path):
            os.remove(file_path)
        # Xóa ghi chú trên server
        try:
            response = requests.delete(
                'http://127.0.0.1:5000/notes',
                json={
                    "username": global_username,
                    "name": notes[note_index]['name']
                }
            )
            if response.status_code == 200:
                messagebox.showinfo("Thành công", "Xóa ghi chú trên server thành công")
            else:
                messagebox.showerror("Lỗi", f"Không thể xóa ghi chú: {response.text}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {str(e)}")
        # Xóa ghi chú khỏi danh sách notes 
        notes.pop(note_index)
        messagebox.showinfo("Thành công", "Ghi chú đã được xóa!")
        list_window.destroy()
        show_notes_list_window(parent_window)

    def open_file(file_path):
        if os.path.exists(file_path):
            os.startfile(file_path)  # Mở file bằng ứng dụng mặc định
        else:
            messagebox.showerror("Lỗi", "File không tồn tại!")

    def load_notes():
        # Khai báo thư mục lưu file và tạo nếu không tồn tại
        directory = os.path.join(os.getcwd(), "note_list")
        if not os.path.exists(directory):
            os.makedirs(directory)
        # Kiểm tra nếu thư mục không rỗng
        if os.listdir(directory):
            # Xóa tất cả file trong thư mục
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            # Xóa toàn bộ note trong mảng notes
            notes.clear()
            messagebox.showinfo("Thành công", "Đã xóa tất cả các file trong thư mục và ghi chú trong mảng!")
        # Lấy lại danh sách ghi chú từ server
        get_notes()
        list_window.destroy()
        show_notes_list_window(parent_window)

    # Tiêu đề
    title_label = tk.Label(
        list_window,
        text="Danh sách ghi chú",
        font=("Helvetica", 16, "bold"),
        bg="#f8f9fa",
        fg="#343a40"
    )
    title_label.pack(pady=20)

    # Hiển thị danh sách ghi chú
    if not notes:
        tk.Label(list_window, text="Chưa có ghi chú nào!", font=("Helvetica", 12), bg="#f8f9fa", fg="red").pack(pady=10)
    else:
        for idx, note in enumerate(notes):
            note_frame = tk.Frame(list_window, bg="#f8f9fa")
            note_frame.pack(fill="x", padx=10, pady=5)

            note_label = tk.Label(note_frame, text=f"{idx + 1}. {note['name']}", font=("Helvetica", 12), bg="#f8f9fa")
            note_label.pack(side="left", padx=10)

            url_button = tk.Button(
                note_frame,
                text="Chia sẻ",
                font=("Helvetica", 10),
                bg="#007bff",
                fg="white",
                activebackground="#0056b3",
                activeforeground="white",
                relief="flat",
                command=lambda name=note["name"]: show_create_url_window(list_window, name)
            )
            url_button.pack(side="left", padx=5)

            open_button = tk.Button(
                note_frame,
                text="Mở file",
                font=("Helvetica", 10),
                bg="#ffc107",
                fg="white",
                activebackground="#e0a800",
                activeforeground="white",
                relief="flat",
                command=lambda path=note["file"]: open_file(path)
            )
            open_button.pack(side="left", padx=5)

            delete_button = tk.Button(
                note_frame,
                text="Xóa",
                font=("Helvetica", 10),
                bg="#dc3545",
                fg="white",
                activebackground="#c82333",
                activeforeground="white",
                relief="flat",
                command=lambda index=idx: delete_note(index)
            )
            delete_button.pack(side="left", padx=5)

    # Nút quay lại
    back_button = tk.Button(
        list_window,
        text="← Quay lại",
        font=("Helvetica", 12),
        bg="#17a2b8",
        fg="white",
        activebackground="#138496",
        activeforeground="white",
        relief="flat",
        command=go_back
    )
    back_button.place(x=10, y=10)

    # Nút load lại danh sách ghi chú
    refresh_button = tk.Button(
        list_window,
        text="Load",
        font=("Helvetica", 12),
        bg="#28a745",
        fg="white",
        activebackground="#218838",
        activeforeground="white",
        relief="flat",
        command=load_notes
    )
    refresh_button.place(x=540, y=10)

# Hàm hiển thị cửa sổ quản lý ghi chú
def show_notes_window():
    root.withdraw()
    notes_window = tk.Toplevel(root)
    notes_window.title("Chức năng quản lý ghi chú")
    center_window(notes_window, 500, 400)
    notes_window.configure(bg="#f8f9fa")

    selected_file = [None]

    def go_back():
        # Kiểm tra nếu thư mục không rỗng
        directory = os.path.join(os.getcwd(), "note_list")
        if os.listdir(directory):
            # Xóa tất cả file trong thư mục
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            # Xóa toàn bộ note trong mảng notes
            notes.clear()
        notes_window.destroy()
        root.deiconify()

    def show_url_input():
        show_url_input_window(notes_window)

    # Hàm mã hóa dữ liệu file
    def encrypt_file_to_variable(input_file, key):
        # Tạo IV ngẫu nhiên
        iv = get_random_bytes(16)
        # Tạo cipher AES  
        cipher = AES.new(key, AES.MODE_CBC, iv)  
        # Đọc nội dung file
        with open(input_file, "rb") as f:
            plaintext = f.read()
        # Padding dữ liệu để chia hết 16 byte
        padding_length = 16 - len(plaintext) % 16
        plaintext += bytes([padding_length]) * padding_length
        # Mã hóa
        ciphertext = cipher.encrypt(plaintext)
        # Lưu nội dung mã hóa vào biến (bao gồm cả IV)
        encrypted_data = iv + ciphertext
        return encrypted_data

    def choose_file():
        file_path = filedialog.askopenfilename(
            title="Chọn file",
            filetypes=(("Tất cả các file", "*.*"), ("File văn bản", "*.txt"))
        )
        if file_path:
            selected_file[0] = file_path
            file_label.config(text=f"Đã chọn: {file_path.split('/')[-1]}")

    def add_note():
        """
        Gửi dữ liệu ghi chú và file lên server thông qua API /upload.
        """
        name = name_entry.get()
        if not (2 <= len(name) <= 20):
            messagebox.showerror("Lỗi", "Tên phải từ 2 đến 20 ký tự!")
        elif not selected_file[0]:
            messagebox.showerror("Lỗi", "Vui lòng chọn file!")
        else:

            # Tạo khóa AES ngẫu nhiên (256-bit)
            key = get_random_bytes(32)
            # Mã hóa file và lưu nội dung mã hóa vào biến
            encrypted_data = encrypt_file_to_variable(selected_file[0], key)
            # --> Viết gửi data này cho server xử lí để lưu vào database [usernam] [name] [file_extension] [key] [encrypted_data]
            file_name = os.path.basename(selected_file[0])  # Lấy tên file, ví dụ: "file.txt"
            file_extension = os.path.splitext(file_name)[1]  # Lấy phần mở rộng, ví dụ: ".txt"
            try:
                response = requests.post(
                    'http://127.0.0.1:5000/notes',
                    json={
                        "username": global_username, 
                        "name": name,
                        "file_extension": file_extension,             
                        "key": base64.b64encode(key).decode('utf-8'),  # Chuyển key từ bytes thành base64
                        "encrypted_data": base64.b64encode(encrypted_data).decode('utf-8')  # Chuyển dữ liệu mã hóa thành base64
                    }
                )
                if response.status_code == 200:
                    messagebox.showinfo("Thành công", "Ghi chú đã được gửi đến server!")
                else:
                    messagebox.showerror("Lỗi", f"Không thể gửi ghi chú: {response.text}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {str(e)}")
            # notes.append({"name": name, "file": selected_file[0]})
            # --> đoạn này không cần nữa do lưu file từ server về
            # Cập nhật lại các trường
            name_entry.delete(0, tk.END)
            selected_file[0] = None
            file_label.config(text="Chưa chọn file")

            
    # Nút quay lại
    back_button = tk.Button(
        notes_window,
        text="← Quay lại",
        font=("Helvetica", 10),
        bg="#007bff",
        fg="white",
        activebackground="#0056b3",
        activeforeground="white",
        relief="flat",
        command=go_back
    )
    back_button.place(x=10, y=10)
    
    # Nút nhập URL
    url_input_button = tk.Button(
        notes_window,
        text="Nhập URL",
        font=("Helvetica", 10),
        bg="#17a2b8",
        fg="white",
        activebackground="#138496",
        activeforeground="white",
        relief="flat",
        command= show_url_input
    )
    url_input_button.place(x=400, y=10)

    title_label = tk.Label(
        notes_window,
        text="Quản lý ghi chú",
        font=("Helvetica", 16, "bold"),
        bg="#f8f9fa",
        fg="#343a40"
    )
    title_label.pack(pady=20)

    # Chọn file
    file_button = tk.Button(
        notes_window,
        text="Chọn file",
        font=("Helvetica", 12),
        bg="#28a745",
        fg="white",
        activebackground="#218838",
        activeforeground="white",
        relief="flat",
        command=choose_file
    )
    file_button.pack(pady=10)

    file_label = tk.Label(notes_window, text="Chưa chọn file", font=("Helvetica", 12), bg="#f8f9fa")
    file_label.pack(pady=5)

    # Nhập tên
    tk.Label(notes_window, text="Đặt tên ghi chú:", font=("Helvetica", 12), bg="#f8f9fa").pack(pady=5)
    name_entry = tk.Entry(notes_window, font=("Helvetica", 12), width=30)
    name_entry.pack(pady=5)

    # Nút xác nhận
    confirm_button = tk.Button(
        notes_window,
        text="Xác nhận",
        font=("Helvetica", 12),
        bg="#ffc107",
        fg="white",
        activebackground="#e0a800",
        activeforeground="white",
        relief="flat",
        command=add_note
    )
    confirm_button.pack(pady=10)

    # Nút liệt kê ghi chú
    list_button = tk.Button(
        notes_window,
        text="Liệt kê các ghi chú",
        font=("Helvetica", 12),
        bg="#17a2b8",
        fg="white",
        activebackground="#138496",
        activeforeground="white",
        relief="flat",
        command=lambda: show_notes_list_window(notes_window)
    )
    list_button.pack(pady=10)
    
# Hàm hiển thị cửa sổ nhập URL
def show_url_input_window(parent_window):
    url_input_window = tk.Toplevel(parent_window)
    url_input_window.title("Nhập URL")
    center_window(url_input_window, 400, 250)
    url_input_window.configure(bg="#f8f9fa")

    def go_back():
        url_input_window.destroy()
        parent_window.deiconify()

    def handle_url_input():
        input_url = url_entry.get()

        try:
            # Gửi URL đến server để kiểm tra tính hợp lệ
            response = requests.post("http://127.0.0.1:5000/validate_url", json={"url": input_url})
            if response.status_code == 200:
                # Nếu URL hợp lệ, tải file từ server
                file_info = response.json()
                download_url = file_info.get("download_url")
                aes_key = base64.b64decode(file_info.get("key"))  # Lấy khóa giải mã từ server
                file_extension = file_info.get("file_extension", "txt")  # Lấy phần mở rộng file từ server

                # Tải dữ liệu mã hóa từ URL
                encrypted_data = requests.get(download_url).content

                # Giải mã dữ liệu
                decrypted_data = decrypt_data(encrypted_data, aes_key)

                # Lưu dữ liệu đã giải mã vào file
                file_name = file_info.get("file_name", f"decrypted_file.{file_extension}")  # Đặt tên file với đúng phần mở rộng
                decrypted_file_path = os.path.join(os.getcwd(), "downloads", file_name)
                os.makedirs(os.path.dirname(decrypted_file_path), exist_ok=True)
                with open(decrypted_file_path, "wb") as file:
                    file.write(decrypted_data)

                # Mở file đã giải mã bằng ứng dụng mặc định
                if os.path.exists(decrypted_file_path):
                    os.startfile(decrypted_file_path)
                else:
                    messagebox.showerror("Lỗi", "File đã giải mã không tồn tại!")
            else:
                messagebox.showerror("Lỗi", response.json().get("message", "URL không hợp lệ!"))

        except Exception as e:
            messagebox.showerror("Lỗi", f"URL đã hết quyền truy cập")

        url_input_window.destroy()
        parent_window.deiconify()
    # Nút quay lại
    back_button = tk.Button(
        url_input_window,
        text="← Quay lại",
        font=("Helvetica", 10),
        bg="#007bff",
        fg="white",
        activebackground="#0056b3",
        activeforeground="white",
        relief="flat",
        command=go_back
    )
    back_button.place(x=10, y=10)

    title_label = tk.Label(
        url_input_window,
        text="Nhập URL",
        font=("Helvetica", 16, "bold"),
        bg="#f8f9fa",
        fg="#343a40"
    )
    title_label.pack(pady=20)

    tk.Label(url_input_window, text="URL:", font=("Helvetica", 12), bg="#f8f9fa").pack(pady=5)
    url_entry = tk.Entry(url_input_window, font=("Helvetica", 12), width=40)
    url_entry.pack(pady=5)

    submit_button = tk.Button(
        url_input_window,
        text="Xác nhận",
        font=("Helvetica", 12),
        bg="#28a745",
        fg="white",
        activebackground="#218838",
        activeforeground="white",
        relief="flat",
        command=handle_url_input
    )
    submit_button.pack(pady=20)
# Hàm hiển thị cửa sổ Đăng nhập
def show_login_window():
    root.withdraw()
    login_window = tk.Toplevel(root)
    login_window.title("Đăng nhập")
    center_window(login_window, 400, 350)
    login_window.configure(bg="#f8f9fa")

    def go_back():
        login_window.destroy()
        root.deiconify()

    def handle_login():
        global global_username  
        username = username_entry.get()
        password = password_entry.get()

        if not (2 <= len(username) <= 20):
            messagebox.showerror("Lỗi", "Tên đăng nhập phải từ 2 đến 20 ký tự!")
        elif len(password) < 8:
            messagebox.showerror("Lỗi", "Mật khẩu phải có ít nhất 8 ký tự!")
        else:

            

            data = {'username': username, 'password': password}
            global_username = username
            try:
                # Gửi yêu cầu đăng nhập đến server
                response = requests.post('http://localhost:5000/login', json=data)
                
                if response.status_code == 200:
                    # Nếu đăng nhập thành công
                    messagebox.showinfo("Đăng nhập thành công", "Bạn đã đăng nhập thành công!")
                    get_notes()
                    login_window.destroy()
                    show_notes_window()  # Chuyển tới cửa sổ quản lý ghi chú
                elif response.status_code == 400 or response.status_code == 404:
                    # Nếu đăng nhập thất bại (sai username hoặc password)
                    messagebox.showerror("Lỗi", "Tên đăng nhập hoặc mật khẩu không đúng!")
                else:
                    # Nếu có lỗi kết nối hoặc mã lỗi khác
                    messagebox.showerror("Lỗi", "Lỗi kết nối với server.")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Lỗi", f"Không thể kết nối với server: {e}")


    # Nút quay lại
    back_button = tk.Button(
        login_window,
        text="← Quay lại",
        font=("Helvetica", 10),
        bg="#007bff",
        fg="white",
        activebackground="#0056b3",
        activeforeground="white",
        relief="flat",
        command=go_back
    )
    back_button.place(x=10, y=10)

    title_label = tk.Label(
        login_window,
        text="Đăng nhập",
        font=("Helvetica", 16),
        bg="#f8f9fa",
        fg="#343a40"
    )
    title_label.pack(pady=20)

    tk.Label(login_window, text="Tên đăng nhập:", font=("Helvetica", 12), bg="#f8f9fa").pack(pady=5)
    username_entry = tk.Entry(login_window, font=("Helvetica", 12), width=30)
    username_entry.pack(pady=5)

    tk.Label(login_window, text="Mật khẩu:", font=("Helvetica", 12), bg="#f8f9fa").pack(pady=5)
    password_entry = tk.Entry(login_window, font=("Helvetica", 12), width=30, show="*")
    password_entry.pack(pady=5)

    submit_button = tk.Button(
        login_window,
        text="Đăng nhập",
        font=("Helvetica", 12),
        bg="#28a745",
        fg="white",
        activebackground="#218838",
        activeforeground="white",
        relief="flat",
        command=handle_login
    )
    submit_button.pack(pady=20)

# Hàm hiển thị cửa sổ Đăng ký
def show_register_window():
    root.withdraw()
    register_window = tk.Toplevel(root)
    register_window.title("Đăng ký")
    center_window(register_window, 400, 450)
    register_window.configure(bg="#f8f9fa")

    def go_back():
        register_window.destroy()
        root.deiconify()

    def handle_register():
        global global_username  
        username = username_entry.get()
        password = password_entry.get()
        confirm_password = confirm_password_entry.get()

        if not (2 <= len(username) <= 20):
            messagebox.showerror("Lỗi", "Tên đăng nhập phải từ 2 đến 20 ký tự!")
        elif not is_valid_password(password):
            messagebox.showerror("Lỗi", "Mật khẩu không hợp lệ! (Ít nhất 8 ký tự, 1 số, 1 chữ in hoa, 1 ký tự đặc biệt)")
        elif password != confirm_password:
            messagebox.showerror("Lỗi", "Mật khẩu không khớp!")
        else:

            # Gửi yêu cầu lên server để kiểm tra tên đăng nhập
            data = {'username': username, 'password': password}
            try:
                # Giả sử URL của server là 'http://localhost:5000/check_username'
                response = requests.post('http://localhost:5000/register', json=data)
                
                # Kiểm tra kết quả từ server
                if response.status_code == 201:
                    messagebox.showinfo("Thành công", "Đăng ký thành công!")
                    register_window.destroy()
                    root.deiconify()
                elif response.status_code == 400:
                    # Nếu tên đăng nhập đã tồn tại
                    result = response.json()
                    messagebox.showerror("Lỗi", result['message'])
                else:
                    messagebox.showerror("Lỗi", "Lỗi kết nối với server.")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Lỗi", f"Không thể kết nối với server: {e}")


    # Nút quay lại
    back_button = tk.Button(
        register_window,
        text="← Quay lại",
        font=("Helvetica", 10),
        bg="#007bff",
        fg="white",
        activebackground="#0056b3",
        activeforeground="white",
        relief="flat",
        command=go_back
    )
    back_button.place(x=10, y=10)

    title_label = tk.Label(
        register_window,
        text="Đăng ký tài khoản",
        font=("Helvetica", 16, "bold"),
        bg="#f8f9fa",
        fg="#343a40"
    )
    title_label.pack(pady=20)

    tk.Label(register_window, text="Tên đăng nhập:", font=("Helvetica", 12), bg="#f8f9fa").pack(pady=5)
    username_entry = tk.Entry(register_window, font=("Helvetica", 12), width=30)
    username_entry.pack(pady=5)

    tk.Label(register_window, text="Mật khẩu:", font=("Helvetica", 12), bg="#f8f9fa").pack(pady=5)
    password_entry = tk.Entry(register_window, font=("Helvetica", 12), width=30, show="*")
    password_entry.pack(pady=5)

    tk.Label(register_window, text="Xác nhận mật khẩu:", font=("Helvetica", 12), bg="#f8f9fa").pack(pady=5)
    confirm_password_entry = tk.Entry(register_window, font=("Helvetica", 12), width=30, show="*")
    confirm_password_entry.pack(pady=5)

    submit_button = tk.Button(
        register_window,
        text="Đăng ký",
        font=("Helvetica", 12),
        bg="#28a745",
        fg="white",
        activebackground="#218838",
        activeforeground="white",
        relief="flat",
        command=handle_register
    )
    submit_button.pack(pady=20)

# Hàm xử lý sự kiện đóng cửa sổ ở của số root 
def on_closing():
    directory = os.path.join(os.getcwd(), "note_list")
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    root.destroy()

# Tạo cửa sổ chính
root = tk.Tk()
root.title("Quản lý ghi chú")
center_window(root, 600, 400)
root.configure(bg="#f8f9fa")

# Gắn sự kiện on_closing vào nút X (close)
root.protocol("WM_DELETE_WINDOW", on_closing)

title_label = tk.Label(
    root,
    text="Chào mừng bạn!",
    font=("Helvetica", 24, "bold"),
    bg="#f8f9fa",
    fg="#343a40"
)
title_label.pack(pady=50)

button_frame = tk.Frame(root, bg="#f8f9fa")
button_frame.pack(pady=20)


login_button = tk.Button(
    button_frame,
    text="Đăng nhập",
    font=("Helvetica", 14, "bold"),
    bg="#007bff",
    fg="white",
    activebackground="#0056b3",
    activeforeground="white",
    width=15,
    height=2,
    relief="flat",
    command=show_login_window
)
login_button.grid(row=0, column=0, padx=20)

register_button = tk.Button(
    button_frame,
    text="Đăng ký",
    font=("Helvetica", 14, "bold"),
    bg="#28a745",
    fg="white",
    activebackground="#218838",
    activeforeground="white",
    width=15,
    height=2,
    relief="flat",
    command=show_register_window
)
register_button.grid(row=0, column=1, padx=20)

root.mainloop()