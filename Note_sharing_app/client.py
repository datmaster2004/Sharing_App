import tkinter as tk
from tkinter import filedialog, messagebox
import re
import pyperclip  # Dùng để copy vào clipboard

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

import tkinter as tk
from tkinter import messagebox
import pyperclip  # Dùng để copy vào clipboard

# Hàm căn giữa cửa sổ
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

# Hàm hiển thị cửa sổ tạo URL
def show_create_url_window(parent_window, note_name):
    parent_window.withdraw()
    create_url_window = tk.Toplevel(parent_window)
    create_url_window.title("Tạo URL")
    center_window(create_url_window, 400, 300)
    create_url_window.configure(bg="#f8f9fa")

    # Tạo URL
    url = f"https://example.com/notes/{note_name.replace(' ', '_')}"

    # Đồng hồ đếm ngược
    countdown_time = [600]  # 10 phút

    def update_timer():
        if countdown_time[0] > 0:
            minutes, seconds = divmod(countdown_time[0], 60)
            timer_label.config(text=f"Thời gian còn lại: {minutes:02}:{seconds:02}")
            countdown_time[0] -= 1
            create_url_window.after(1000, update_timer)
        else:
            messagebox.showinfo("Hết giờ", "Thời gian chia sẻ URL đã hết!")
            cancel_share()

    # Quay lại
    def go_back():
        create_url_window.destroy()
        parent_window.deiconify()

    # Copy URL
    def copy_to_clipboard():
        pyperclip.copy(url)
        messagebox.showinfo("Copy", "URL đã được sao chép vào clipboard!")

    # Hủy chia sẻ
    def cancel_share():
        create_url_window.destroy()
        parent_window.deiconify()

    # Giao diện tạo URL
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
    back_button.pack(pady=10, anchor="w", padx=10)

    url_label = tk.Label(
        create_url_window,
        text=f"URL: {url}",
        font=("Helvetica", 12),
        bg="#f8f9fa",
        fg="#343a40",
        wraplength=350,
        justify="center"
    )
    url_label.pack(pady=10)

    button_frame = tk.Frame(create_url_window, bg="#f8f9fa")
    button_frame.pack(pady=10)

    copy_button = tk.Button(
        button_frame,
        text="Copy",
        font=("Helvetica", 12),
        bg="#28a745",
        fg="white",
        activebackground="#218838",
        activeforeground="white",
        relief="flat",
        command=copy_to_clipboard
    )
    copy_button.pack(side="left", padx=10)

    cancel_button = tk.Button(
        button_frame,
        text="Hủy chia sẻ",
        font=("Helvetica", 12),
        bg="#dc3545",
        fg="white",
        activebackground="#c82333",
        activeforeground="white",
        relief="flat",
        command=cancel_share
    )
    cancel_button.pack(side="left", padx=10)

    timer_label = tk.Label(
        create_url_window,
        text="Thời gian còn lại: 10:00",
        font=("Helvetica", 12),
        bg="#f8f9fa",
        fg="#343a40"
    )
    timer_label.pack(pady=10)

    # Bắt đầu đếm giờ
    update_timer()


# Hàm hiển thị danh sách ghi chú
def show_notes_list_window(parent_window):
    parent_window.withdraw()
    list_window = tk.Toplevel(parent_window)
    list_window.title("Danh sách ghi chú")
    center_window(list_window, 600, 400)
    list_window.configure(bg="#f8f9fa")

    def go_back():
        list_window.destroy()
        parent_window.deiconify()

    def create_url(note_name):
        show_create_url_window(list_window, note_name)

    def delete_note(note_index):
        notes.pop(note_index)
        messagebox.showinfo("Xóa ghi chú", "Ghi chú đã được xóa!")
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
                text="Tạo URL",
                font=("Helvetica", 10),
                bg="#007bff",
                fg="white",
                activebackground="#0056b3",
                activeforeground="white",
                relief="flat",
                command=lambda name=note["name"]: create_url(name)
            )
            url_button.pack(side="left", padx=5)

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
    back_button.pack(pady=20)

# Hàm hiển thị cửa sổ quản lý ghi chú
def show_notes_window():
    root.withdraw()
    notes_window = tk.Toplevel(root)
    notes_window.title("Chức năng quản lý ghi chú")
    center_window(notes_window, 500, 400)
    notes_window.configure(bg="#f8f9fa")

    selected_file = [None]

    def go_back():
        notes_window.destroy()
        root.deiconify()

    def choose_file():
        file_path = filedialog.askopenfilename(
            title="Chọn file",
            filetypes=(("Tất cả các file", "*.*"), ("File văn bản", "*.txt"))
        )
        if file_path:
            selected_file[0] = file_path
            file_label.config(text=f"Đã chọn: {file_path.split('/')[-1]}")

    def add_note():
        name = name_entry.get()
        if not (2 <= len(name) <= 20):
            messagebox.showerror("Lỗi", "Tên phải từ 2 đến 20 ký tự!")
        elif not selected_file[0]:
            messagebox.showerror("Lỗi", "Vui lòng chọn file!")
        else:
            notes.append({"name": name, "file": selected_file[0]})
            messagebox.showinfo("Thành công", f"Ghi chú '{name}' đã được tạo!")
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
        username = username_entry.get()
        password = password_entry.get()

        if not (2 <= len(username) <= 20):
            messagebox.showerror("Lỗi", "Tên đăng nhập phải từ 2 đến 20 ký tự!")
        elif len(password) < 8:
            messagebox.showerror("Lỗi", "Mật khẩu phải có ít nhất 8 ký tự!")
        else:
            login_window.destroy()
            show_notes_window()

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
            messagebox.showinfo("Thành công", "Đăng ký thành công!")
            register_window.destroy()
            root.deiconify()

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

# Tạo cửa sổ chính
root = tk.Tk()
root.title("Quản lý ghi chú")
center_window(root, 600, 400)
root.configure(bg="#f8f9fa")

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
