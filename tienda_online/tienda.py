
import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
from datetime import datetime

class TiendaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tienda Moderna")
        self.root.geometry("900x600")
        self.user = None
        self.cart = []
        self.load_data()
        self.show_login()

    def load_data(self):
        with open("data/productos.json", "r") as f:
            self.productos = json.load(f)
        if os.path.exists("data/usuarios.json"):
            with open("data/usuarios.json", "r") as f:
                self.usuarios = json.load(f)
        else:
            self.usuarios = {}
        if os.path.exists("data/historial.json"):
            with open("data/historial.json", "r") as f:
                self.historial = json.load(f)
        else:
            self.historial = {}

    def save_users(self):
        with open("data/usuarios.json", "w") as f:
            json.dump(self.usuarios, f)

    def save_historial(self):
        with open("data/historial.json", "w") as f:
            json.dump(self.historial, f)

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear_screen()
        frame = tk.Frame(self.root)
        frame.pack(pady=50)

        tk.Label(frame, text="Usuario").pack()
        user_entry = tk.Entry(frame)
        user_entry.pack()

        tk.Label(frame, text="Contraseña").pack()
        pass_entry = tk.Entry(frame, show="*")
        pass_entry.pack()

        def login():
            user = user_entry.get()
            pwd = pass_entry.get()
            if self.usuarios.get(user) == pwd:
                self.user = user
                self.cart = []
                self.show_catalog()
            else:
                messagebox.showerror("Error", "Credenciales inválidas")

        def register():
            user = user_entry.get()
            pwd = pass_entry.get()
            if user in self.usuarios:
                messagebox.showinfo("Info", "Usuario ya existe")
            else:
                self.usuarios[user] = pwd
                self.save_users()
                messagebox.showinfo("Registrado", "Usuario registrado")

        ttk.Button(frame, text="Iniciar sesión", command=login).pack(pady=5)
        ttk.Button(frame, text="Registrarse", command=register).pack(pady=5)

    def show_catalog(self):
        self.clear_screen()
        top = tk.Frame(self.root)
        top.pack(fill="x")
        ttk.Button(top, text="🛒 Carrito", command=self.show_cart).pack(side="right", padx=10)
        ttk.Button(top, text="📜 Historial", command=self.show_history).pack(side="right")
        ttk.Button(top, text="Cerrar sesión", command=self.show_login).pack(side="left", padx=10)
        tk.Label(self.root, text="Catálogo", font=("Arial", 20)).pack(pady=10)

        for p in self.productos:
            frame = tk.Frame(self.root, bd=2, relief="ridge", padx=10, pady=10)
            frame.pack(pady=5)
            tk.Label(frame, text=p["nombre"], font=("Arial", 14)).pack()
            tk.Label(frame, text=f"${p['precio']}", font=("Arial", 12)).pack()
            ttk.Button(frame, text="Agregar al carrito", command=lambda p=p: self.add_to_cart(p)).pack()

    def add_to_cart(self, producto):
        self.cart.append(producto)
        messagebox.showinfo("Agregado", f"{producto['nombre']} añadido al carrito")

    def show_cart(self):
        self.clear_screen()
        ttk.Button(self.root, text="< Volver", command=self.show_catalog).pack(anchor="w", padx=10, pady=5)
        tk.Label(self.root, text="Carrito", font=("Arial", 20)).pack(pady=10)

        total = 0
        for idx, item in enumerate(self.cart):
            frame = tk.Frame(self.root, pady=5)
            frame.pack()
            tk.Label(frame, text=f"{item['nombre']} - ${item['precio']}").pack(side="left")
            ttk.Button(frame, text="Quitar", command=lambda i=idx: self.remove_item(i)).pack(side="right", padx=10)
            total += item["precio"]

        tk.Label(self.root, text=f"Total: ${total}", font=("Arial", 16)).pack(pady=10)
        if self.cart:
            ttk.Button(self.root, text="Finalizar compra", command=self.checkout).pack()

    def remove_item(self, index):
        del self.cart[index]
        self.show_cart()

    def checkout(self):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        compra = {
            "fecha": fecha,
            "items": self.cart,
            "total": sum(p["precio"] for p in self.cart)
        }
        self.historial.setdefault(self.user, []).append(compra)
        self.save_historial()
        self.cart.clear()
        messagebox.showinfo("Compra", "Compra realizada con éxito")
        self.show_catalog()

    def show_history(self):
        self.clear_screen()
        ttk.Button(self.root, text="< Volver", command=self.show_catalog).pack(anchor="w", padx=10, pady=5)
        tk.Label(self.root, text="Historial de compras", font=("Arial", 20)).pack(pady=10)
        compras = self.historial.get(self.user, [])
        if not compras:
            tk.Label(self.root, text="Sin compras aún").pack()
        else:
            for c in compras:
                frame = tk.Frame(self.root, pady=5, padx=10, relief="ridge", bd=2)
                frame.pack(pady=5)
                tk.Label(frame, text=f"Fecha: {c['fecha']}", font=("Arial", 12)).pack(anchor="w")
                for i in c["items"]:
                    tk.Label(frame, text=f"- {i['nombre']} (${i['precio']})").pack(anchor="w")
                tk.Label(frame, text=f"Total: ${c['total']}", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = TiendaApp(root)
    root.mainloop()
