
import customtkinter as ctk
from PIL import Image
from io import BytesIO
from urllib.request import urlopen
import json
from pathlib import Path
from tkinter import messagebox, filedialog, simpledialog
from core.cart_manager import cart
from core.auth import authenticate, register_user
from core.payment_gateways import WebPay, MACH, BancoEstado, Transferencia
from core.order_manager import create_order, get_orders_by_user
import shutil

# Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Styles
BG = "#000000"
ENTRY_BG = "#1F1F1F"
ACCENT = "#00FF00"
TEXT = "#FFFFFF"
FONT = ("Courier", 12)

# Data paths
DATA_DIR = Path(__file__).parent / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"
IMAGES_DIR = DATA_DIR / "images"

def load_products():
    return json.loads(Path(PRODUCTS_FILE).read_text(encoding="utf-8"))["products"]

def save_products(products):
    Path(PRODUCTS_FILE).write_text(json.dumps({"products": products}, indent=2), encoding="utf-8")

def load_image(url, size):
    if not url:
        return None
    try:
        if url.startswith("images/"):
            path = Path(__file__).parent / "data" / url
            img = Image.open(path)
        else:
            data = urlopen(url).read()
            img = Image.open(BytesIO(data))
        return ctk.CTkImage(img, size=size)
    except:
        return None

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Ice Store")
        self.geometry("1200x800")
        self.configure(fg_color=BG)
        self.logged_user = None
        self.shipping_info = {}
        self.discount_code = None
        self.discount_rate = 0

        # Header
        header = ctk.CTkFrame(self, fg_color=BG, height=50)
        header.pack(fill="x", side="top")
        btns = [("≡", self.open_menu), ("Catálogo", self.show_catalog),
                ("👤", self.show_account), ("🔍", self.show_search),
                ("🛒", self.show_cart), ("📜", self.show_history)]
        for text, cmd in btns:
            ctk.CTkButton(header, text=text, fg_color=BG, text_color=ACCENT,
                          font=("Courier",20), command=cmd).pack(side="left", padx=5)
        # Admin icon
        ctk.CTkButton(header, text="⚙️", fg_color=BG, text_color=ACCENT,
                      font=("Courier",20), command=self.show_admin).pack(side="right", padx=5)

        # Container frames
        self.container = ctk.CTkFrame(self, fg_color=BG)
        self.container.pack(fill="both", expand=True)
        self.frames = {}
        for name in ["catalog","cart","account","search","shipping","payment","history","admin"]:
            f = ctk.CTkScrollableFrame(self.container, fg_color=BG)
            f.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.frames[name] = f

        # Build views
        self.build_catalog(); self.build_cart(); self.build_account()
        self.build_search(); self.build_shipping(); self.build_payment()
        self.build_history(); self.build_admin()
        self.show_catalog()

    def build_catalog(self):
        f = self.frames["catalog"]; [w.destroy() for w in f.winfo_children()]
        prods = load_products()
        grid = ctk.CTkScrollableFrame(f, fg_color=BG)
        grid.pack(fill="both", expand=True, padx=20, pady=10)
        for idx, p in enumerate(prods):
            card = ctk.CTkFrame(grid, fg_color=ENTRY_BG, corner_radius=8)
            card.grid(row=idx//4, column=idx%4, padx=10, pady=10)
            img = load_image(p.get("image_url",""), size=(120,120))
            if img:
                lbl = ctk.CTkLabel(card, image=img, text="")
                lbl.image = img; lbl.pack(pady=(10,5))
            ctk.CTkLabel(card, text=p["name"], text_color=TEXT, font=FONT).pack()
            ctk.CTkLabel(card, text=f"$ {p['price']:,}", text_color=ACCENT, font=FONT).pack(pady=(0,5))
            ctk.CTkButton(card, text="Agregar al carrito", fg_color=ACCENT, text_color=BG,
                          command=lambda pid=p["id"]: self.add_to_cart(pid)).pack(pady=(0,10))

    def build_cart(self):
        f = self.frames["cart"]; [w.destroy() for w in f.winfo_children()]
        ctk.CTkLabel(f, text="Mi Carrito", text_color=TEXT, font=("Courier",16)).pack(pady=10)
        items = cart.get_items()
        if not items:
            ctk.CTkLabel(f, text="Carrito vacío", text_color=TEXT, font=FONT).pack(pady=20)
        else:
            for pid, qty in items.items():
                prod = next(x for x in load_products() if x['id']==pid)
                row = ctk.CTkFrame(f, fg_color=ENTRY_BG, corner_radius=8); row.pack(fill="x", padx=20, pady=5)
                ctk.CTkLabel(row, text=f"{prod['name']} x{qty} - ${prod['price']*qty}",
                             text_color=TEXT, font=FONT).pack(side="left", padx=5)
                ctk.CTkButton(row, text="X", fg_color="#FF0000", text_color=BG, width=30,
                              command=lambda pid=pid: self.remove_from_cart(pid)).pack(side="right", padx=5)
            ctk.CTkButton(f, text="Checkout", fg_color=ACCENT, text_color=BG, command=self.show_shipping).pack(pady=20)

    def build_account(self):
        f = self.frames["account"]; [w.destroy() for w in f.winfo_children()]
        if not self.logged_user:
            ctk.CTkLabel(f, text="Login", text_color=TEXT, font=("Courier",16)).pack(pady=10)
            self.email_entry = ctk.CTkEntry(f, placeholder_text="Email"); self.email_entry.pack(pady=5)
            self.pwd_entry = ctk.CTkEntry(f, show="*", placeholder_text="Password"); self.pwd_entry.pack(pady=5)
            ctk.CTkButton(f, text="Iniciar sesión", fg_color=ACCENT, text_color=BG,
                          command=self.login_user).pack(pady=5)
            ctk.CTkLabel(f, text="--- o ---", text_color=TEXT).pack(pady=5)
            ctk.CTkLabel(f, text="Register", text_color=TEXT, font=("Courier",16)).pack(pady=10)
            self.reg_email = ctk.CTkEntry(f, placeholder_text="Email"); self.reg_email.pack(pady=5)
            self.reg_pwd = ctk.CTkEntry(f, show="*", placeholder_text="Password"); self.reg_pwd.pack(pady=5)
            self.reg_conf = ctk.CTkEntry(f, show="*", placeholder_text="Confirm Password"); self.reg_conf.pack(pady=5)
            ctk.CTkLabel(f, text="Nota: mayúsculas y números", text_color=TEXT, font=FONT).pack(pady=5)
            ctk.CTkButton(f, text="Registrar", fg_color=ACCENT, text_color=BG,
                          command=self.register_user).pack(pady=5)
        else:
            ctk.CTkLabel(f, text=f"Bienvenido, {self.logged_user}", text_color=TEXT, font=("Courier",16)).pack(pady=20)
            ctk.CTkButton(f, text="Cerrar sesión", fg_color=ACCENT, text_color=BG,
                          command=self.logout).pack(pady=5)

    def build_search(self):
        f = self.frames["search"]; [w.destroy() for w in f.winfo_children()]
        ctk.CTkEntry(f, placeholder_text="Buscar...").pack(pady=10)
        ctk.CTkButton(f, text="Buscar", fg_color=ACCENT, text_color=BG,
                      command=lambda q="": self.perform_search(q)).pack(pady=5)
        self.results = ctk.CTkScrollableFrame(f, fg_color=BG); self.results.pack(fill="both", expand=True, padx=10, pady=10)

    def perform_search(self, query):
        f = self.frames["search"]; [w.destroy() for w in f.winfo_children()]
        entry = ctk.CTkEntry(f, placeholder_text="Buscar..."); entry.pack(pady=10)
        ctk.CTkButton(f, text="Buscar", fg_color=ACCENT, text_color=BG,
                      command=lambda q=entry.get(): self.perform_search(q)).pack(pady=5)
        results = ctk.CTkScrollableFrame(f, fg_color=BG); results.pack(fill="both", expand=True, padx=10, pady=10)
        found = [p for p in load_products() if query.lower() in p['name'].lower()]
        if not found:
            ctk.CTkLabel(results, text="Sin resultados", text_color=TEXT, font=FONT).pack(pady=20)
        for p in found:
            row = ctk.CTkFrame(results, fg_color=ENTRY_BG, corner_radius=8); row.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(row, text=p['name'], text_color=TEXT, font=FONT).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"$ {p['price']:,}", text_color=ACCENT, font=FONT).pack(side="left", padx=10)
            ctk.CTkButton(row, text="Agregar al carrito", fg_color=ACCENT, text_color=BG,
                          command=lambda pid=p["id"]: self.add_to_cart(pid)).pack(side="right", padx=10)

    def build_shipping(self):
        f = self.frames["shipping"]; [w.destroy() for w in f.winfo_children()]
        ctk.CTkLabel(f, text="Datos de Envío", text_color=TEXT, font=("Courier",16)).pack(pady=10)
        self.ship_name = ctk.CTkEntry(f, placeholder_text="Nombre completo"); self.ship_name.pack(pady=5)
        self.ship_addr = ctk.CTkEntry(f, placeholder_text="Dirección"); self.ship_addr.pack(pady=5)
        self.ship_post = ctk.CTkEntry(f, placeholder_text="Código Postal"); self.ship_post.pack(pady=5)
        self.ship_rut = ctk.CTkEntry(f, placeholder_text="RUT"); self.ship_rut.pack(pady=5)
        ctk.CTkButton(f, text="Siguiente", fg_color=ACCENT, text_color=BG,
                      command=self.show_payment).pack(pady=20)

    def build_payment(self):
        f = self.frames["payment"]; [w.destroy() for w in f.winfo_children()]
        ctk.CTkLabel(f, text="Datos de Pago", text_color=TEXT, font=("Courier",16)).pack(pady=10)
        self.card_num = ctk.CTkEntry(f, placeholder_text="Número tarjeta"); self.card_num.pack(pady=5)
        self.card_exp = ctk.CTkEntry(f, placeholder_text="MM/AA"); self.card_exp.pack(pady=5)
        self.card_cvv = ctk.CTkEntry(f, placeholder_text="CVV"); self.card_cvv.pack(pady=5)
        self.pay_menu = ctk.CTkOptionMenu(f, values=["WebPay","MACH","BancoEstado","Transferencia"]); self.pay_menu.pack(pady=5)
        ctk.CTkButton(f, text="Pagar", fg_color=ACCENT, text_color=BG,
                      command=self.process_payment).pack(pady=20)

    def build_history(self):
        f = self.frames["history"]; [w.destroy() for w in f.winfo_children()]
        ctk.CTkLabel(f, text="Historial de Pedidos", text_color=TEXT, font=("Courier",16)).pack(pady=10)
        if not self.logged_user:
            ctk.CTkLabel(f, text="Inicia sesión", text_color=TEXT, font=FONT).pack(pady=20); return
        orders = get_orders_by_user(self.logged_user)
        if not orders:
            ctk.CTkLabel(f, text="No hay pedidos", text_color=TEXT, font=FONT).pack(pady=20)
        for o in orders:
            row = ctk.CTkFrame(f, fg_color=ENTRY_BG, corner_radius=8); row.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(row, text=f"Pedido {o['id']} - Total: ${o['discounted_total']}",
                         text_color=TEXT, font=FONT).pack(side="left", padx=10)

    def build_admin(self):
        f = self.frames["admin"]; [w.destroy() for w in f.winfo_children()]
        ctk.CTkLabel(f, text="Admin: Agregar Producto", text_color=TEXT, font=("Courier",16)).pack(pady=10)
        self.a_name = ctk.CTkEntry(f, placeholder_text="Nombre"); self.a_name.pack(pady=5)
        self.a_price = ctk.CTkEntry(f, placeholder_text="Precio"); self.a_price.pack(pady=5)
        self.a_stock = ctk.CTkEntry(f, placeholder_text="Stock"); self.a_stock.pack(pady=5)
        self.a_url = ctk.CTkEntry(f, placeholder_text="URL imagen o images/…"); self.a_url.pack(pady=5)
        ctk.CTkButton(f, text="📂 Subir producto", fg_color=ACCENT, text_color=BG,
                      command=self.upload_image).pack(pady=5)
        ctk.CTkButton(f, text="Agregar Producto", fg_color=ACCENT, text_color=BG,
                      command=self.add_product).pack(pady=10)

    def upload_image(self):
        path = filedialog.askopenfilename(filetypes=[("Imagen","*.png;*.jpg;*.jpeg")])
        if path:
            dst = IMAGES_DIR / Path(path).name
            shutil.copy(path, dst)
            rel = f"images/{Path(path).name}"
            self.a_url.delete(0,"end"); self.a_url.insert(0, rel)

    def add_product(self):
        prods = load_products()
        new_id = str(max(int(p["id"]) for p in prods)+1 if prods else 1)
        item = {"id": new_id, "name": self.a_name.get(),
                "price": int(self.a_price.get()), "stock": int(self.a_stock.get()),
                "image_url": self.a_url.get()}
        prods.append(item); save_products(prods)
        messagebox.showinfo("Admin","Producto agregado")
        self.build_catalog(); self.show_catalog()

    def open_menu(self):
        messagebox.showinfo("Menú","Menú en construcción")

    def show_catalog(self):
        self.frames["catalog"].lift()

    def show_cart(self):
        self.build_cart(); self.frames["cart"].lift()

    def show_account(self):
        self.build_account(); self.frames["account"].lift()

    def show_search(self):
        self.frames["search"].lift()

    def show_shipping(self):
        self.build_shipping(); self.frames["shipping"].lift()

    def show_payment(self):
        self.build_payment(); self.frames["payment"].lift()

    def show_history(self):
        self.build_history(); self.frames["history"].lift()

    def show_admin(self):
        # Solicitar clave admin antes de mostrar panel
        pwd = simpledialog.askstring("Acceso Admin", "Ingrese la clave de administrador:", show="*")
        if pwd == "admin":
            self.frames["admin"].lift()
        else:
            messagebox.showerror("Acceso denegado", "Clave inválida")

    def add_to_cart(self, pid):
        cart.add_item(pid)
        messagebox.showinfo("Carrito","Agregado exitoso al carrito")
        self.show_cart()

    def remove_from_cart(self, pid):
        cart.remove_item(pid)
        self.show_cart()

    def submit_shipping(self):
        self.shipping_info = {
            "name": self.ship_name.get(),
            "address": self.ship_addr.get(),
            "postal": self.ship_post.get(),
            "rut": self.ship_rut.get()
        }
        self.show_payment()

    def process_payment(self):
        method = self.pay_menu.get()
        items = cart.get_items()
        create_order(self.logged_user or "anonymous", items, self.shipping_info,
                     method, self.discount_code, self.discount_rate)
        messagebox.showinfo("Éxito","Pago realizado y orden creada")
        cart.items.clear()
        self.show_history()

    def login_user(self):
        user = authenticate(self.email_entry.get(), self.pwd_entry.get())
        if user:
            self.logged_user = self.email_entry.get()
            messagebox.showinfo("Éxito","Login exitoso")
            self.show_account()
        else:
            messagebox.showerror("Error","Credenciales inválidas")

    def register_user(self):
        email = self.reg_email.get(); pwd = self.reg_pwd.get(); conf = self.reg_conf.get()
        if pwd != conf:
            messagebox.showerror("Error","Las contraseñas no coinciden"); return
        ok, msg = register_user(email, pwd)
        if ok:
            messagebox.showinfo("Éxito", msg)
            self.show_account()
        else:
            messagebox.showerror("Error", msg)

    def logout(self):
        self.logged_user = None
        self.admin_btn.pack_forget()
        self.show_account()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = App()
    app.mainloop()