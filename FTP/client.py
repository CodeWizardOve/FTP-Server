import os
import tkinter as tk
from tkinter import filedialog, messagebox
import socket
import threading

client_socket = None  # Global socket variable

def connect_to_server(ip, port):
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, int(port)))
        status_label.config(text="[SUCCESS]: Welcome to the File Server")
        refresh_file_list()
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to connect: {e}")

def disconnect_from_server():
    global client_socket
    if client_socket:
        client_socket.close()
        client_socket = None
        status_label.config(text="Disconnected")
        for widget in button_frame.winfo_children():
            widget.destroy()

def refresh_file_list():
    def task():
        global client_socket
        if client_socket:
            try:
                client_socket.sendall("LIST".encode('utf-8'))
                data = client_socket.recv(4096).decode('utf-8')
                files = data.split('\n')
                for widget in button_frame.winfo_children():
                    widget.destroy()
                for file in files:
                    if file:  # Avoid inserting empty strings
                        add_file_row(file)
            except Exception as e:
                messagebox.showerror("Network Error", f"Failed to refresh file list: {e}")

    threading.Thread(target=task).start()

def add_file_row(filename):
    row_frame = tk.Frame(button_frame, bg="#FFF")
    row_frame.pack(fill="x", pady=2)

    file_label = tk.Label(row_frame, text=filename, bg="#FFF", anchor="w")
    file_label.pack(side="left", padx=10)

    download_button = tk.Button(row_frame, text="Download", bg="#5bc0de", fg="#FFF", command=lambda: download_file(filename))
    download_button.pack(side="right", padx=5)

    delete_button = tk.Button(row_frame, text="Delete", bg="#d9534f", fg="#FFF", command=lambda: delete_file(filename))
    delete_button.pack(side="right", padx=5)

def upload_file(filepath):
    if filepath:
        filename = os.path.basename(filepath)
        def task():
            try:
                client_socket.sendall(f"UPLOAD {filename}".encode('utf-8'))
                with open(filepath, 'rb') as f:
                    while True:
                        data = f.read(1024)
                        if not data:
                            break
                        client_socket.sendall(data)
                # Ensure the file is closed before checking for the response
                response = client_socket.recv(1024).decode('utf-8')
                if response == 'OK':
                    messagebox.showinfo("Upload Successful", f"Uploaded {filename}")
                    refresh_file_list()
                else:
                    messagebox.showerror("Upload Failed", "Failed to upload file")
            except Exception as e:
                messagebox.showerror("Network Error", f"Failed to upload file: {e}")

        threading.Thread(target=task).start()


def download_file(filename):
    def task():
        try:
            client_socket.sendall(f"GET {filename}".encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')
            if response == 'OK':
                file_extension = os.path.splitext(filename)[1]
                file_types = [(f"{file_extension} files", f"*{file_extension}"), ("All files", "*.*")]
                save_path = filedialog.asksaveasfilename(defaultextension=file_extension, filetypes=file_types, initialfile=filename)
                if save_path:
                    with open(save_path, 'wb') as f:
                        while True:
                            data = client_socket.recv(1024)
                            if not data:
                                break
                            f.write(data)
                    messagebox.showinfo("Download Successful", f"Downloaded {filename}")
            else:
                messagebox.showerror("Download Failed", "Could not download the file")
        except Exception as e:
            messagebox.showerror("Network Error", f"Failed to download file: {e}")

    threading.Thread(target=task).start()

def delete_file(filename):
    def task():
        try:
            client_socket.sendall(f"DEL {filename}".encode('utf-8'))
            response = client_socket.recv(1024)
            if response == b'OK':
                messagebox.showinfo("Delete Successful", f"Deleted {filename}")
                refresh_file_list()
            else:
                messagebox.showerror("Delete Failed", "Could not delete the file")
        except Exception as e:
            messagebox.showerror("Network Error", f"Failed to delete file: {e}")

    threading.Thread(target=task).start()

def create_client_gui():
    global status_label, button_frame

    root = tk.Tk()
    root.title("FTP Client")
    root.configure(bg="#333")

    tk.Label(root, text="IP Address:", bg="#333", fg="#FFF").grid(row=0, column=0, padx=10, pady=10)
    ip_entry = tk.Entry(root)
    ip_entry.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(root, text="Port:", bg="#333", fg="#FFF").grid(row=0, column=2, padx=10, pady=10)
    port_entry = tk.Entry(root)
    port_entry.grid(row=0, column=3, padx=10, pady=10)
    port_entry.insert(0, '65432')

    connect_button = tk.Button(root, text="Connect", bg="#fff", fg="#FFF", command=lambda: threading.Thread(target=connect_to_server, args=(ip_entry.get(), port_entry.get())).start())
    connect_button.grid(row=0, column=4, padx=10, pady=10)

    disconnect_button = tk.Button(root, text="Logout", bg="#555", fg="#FFF", command=disconnect_from_server)
    disconnect_button.grid(row=0, column=5, padx=10, pady=10)

    tk.Label(root, text="File Location:", bg="#333", fg="#FFF").grid(row=1, column=0, padx=10, pady=10)
    file_entry = tk.Entry(root, width=40)
    file_entry.grid(row=1, column=1, columnspan=3, padx=10, pady=10)

    browse_button = tk.Button(root, text="Browse", bg="#555", fg="#FFF", command=lambda: file_entry.insert(0, filedialog.askopenfilename()))
    browse_button.grid(row=1, column=4, padx=10, pady=10)

    upload_button = tk.Button(root, text="Upload", bg="#555", fg="#FFF", command=lambda: upload_file(file_entry.get()))
    upload_button.grid(row=1, column=5, padx=10, pady=10)

    tk.Label(root, text="Server Files", bg="#333", fg="#FFF").grid(row=2, column=0, columnspan=6, pady=10)

    button_frame = tk.Frame(root, bg="#FFF")
    button_frame.grid(row=3, column=0, columnspan=6, sticky="nsew", padx=10, pady=10)

    root.grid_rowconfigure(3, weight=1)
    root.grid_columnconfigure(1, weight=1)

    status_label = tk.Label(root, text="[SUCCESS]: Welcome to the File Server", bg="#333", fg="#FFF")
    status_label.grid(row=4, column=0, columnspan=6, pady=10)

    root.mainloop()

create_client_gui()
