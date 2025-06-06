import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import hashlib
import re
from datetime import datetime
import shutil
from PIL import Image, ImageTk
import uuid

# Configuración de CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class DataManager:
    """Gestor de datos para persistencia en JSON"""
    
    def __init__(self):
        self.data_dir = "data"
        self.images_dir = os.path.join(self.data_dir, "product_images")
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.products_file = os.path.join(self.data_dir, "products.json")
        self.sales_file = os.path.join(self.data_dir, "sales.json")
        self.admin_file = os.path.join(self.data_dir, "admin.json")
        self.suppliers_file = os.path.join(self.data_dir, "suppliers.json")
        
        # Crear directorios si no existen
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Inicializar archivos JSON
        self._init_json_files()
    
    def _init_json_files(self):
        """Inicializa archivos JSON si no existen"""
        for file_path in [self.users_file, self.products_file, self.sales_file, self.suppliers_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump([], f)

        if not os.path.exists(self.admin_file):
            admin_data = [{
                "id": "admin-001",
                "rut": "11111111-1",
                "email": "admin@sistema.com",
                "password": "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f",
                "type": "admin",
                "name": "Administrador del Sistema",
                "created_at": "2024-01-01T00:00:00"
            }]
            with open(self.admin_file, 'w') as f:
                json.dump(admin_data, f, indent=2, ensure_ascii=False)
    
    def load_data(self, file_type):
        """Carga datos desde archivo JSON"""
        file_map = {
            'users': self.users_file,
            'products': self.products_file,
            'sales': self.sales_file,
            'admin': self.admin_file,
            'suppliers': self.suppliers_file
        }
        
        try:
            with open(file_map[file_type], 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando {file_type}: {e}")
            return []
        
        try:
            with open(file_map[file_type], 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando {file_type}: {e}")
            return []
    
    def save_data(self, file_type, data):
        """Guarda datos en archivo JSON"""
        file_map = {
            'users': self.users_file,
            'products': self.products_file,
            'sales': self.sales_file,
            'admin': self.admin_file,
            'suppliers': self.suppliers_file
        }
        
        try:
            with open(file_map[file_type], 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando {file_type}: {e}")
            return False

class Validator:
    """Clase para validaciones"""

    @staticmethod
    def validate_rut(rut):
        """Valida el formato y dígito verificador del RUT chileno"""
        rut = rut.replace(".", "").replace("-", "").upper()
        if len(rut) < 2:
            return False
        cuerpo = rut[:-1]
        dv = rut[-1]

        try:
            cuerpo_int = list(map(int, reversed(cuerpo)))
        except ValueError:
            return False

        suma = 0
        multiplicador = 2
        for d in cuerpo_int:
            suma += d * multiplicador
            multiplicador = 2 if multiplicador == 7 else multiplicador + 1

        resto = suma % 11
        dv_calculado = 11 - resto
        if dv_calculado == 11:
            dv_calculado = "0"
        elif dv_calculado == 10:
            dv_calculado = "K"
        else:
            dv_calculado = str(dv_calculado)

        return dv == dv_calculado

    @staticmethod
    def validate_email(email):
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def hash_password(password):
        """Hashea contraseña con SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()


class AuthManager:
    """Gestor de autenticación"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.current_user = None
    
    def register_user(self, rut, email, password, user_type, name):
        """Registra nuevo usuario"""
        # Validaciones
        if not Validator.validate_rut(rut):
            return False, "RUT inválido"
        
        if not Validator.validate_email(email):
            return False, "Email inválido"
        
        if len(password) < 6:
            return False, "Contraseña debe tener al menos 6 caracteres"
        
        # Cargar usuarios existentes
        users = self.data_manager.load_data('users')
        
        # Verificar si el usuario ya existe
        for user in users:
            if user['rut'] == rut or user['email'] == email:
                return False, "Usuario ya existe"
        
        # Crear nuevo usuario
        new_user = {
            'id': str(uuid.uuid4()),
            'rut': rut,
            'email': email,
            'password': Validator.hash_password(password),
            'type': user_type,
            'name': name,
            'created_at': datetime.now().isoformat()
        }
        
        users.append(new_user)
        
        if self.data_manager.save_data('users', users):
            return True, "Usuario registrado exitosamente"
        else:
            return False, "Error al guardar usuario"
    
    def login_user(self, email, password):
        """Autentica usuario"""
        # Verificar admin primero
        admins = self.data_manager.load_data('admin')
        hashed_password = Validator.hash_password(password)
        
        for admin in admins:
            if admin['email'] == email and admin['password'] == hashed_password:
                self.current_user = admin
                return True, "Login exitoso"
        
        # Verificar usuarios normales
        users = self.data_manager.load_data('users')
        
        for user in users:
            if user['email'] == email and user['password'] == hashed_password:
                self.current_user = user
                return True, "Login exitoso"
        
        return False, "Email o contraseña incorrectos"
    
    def logout_user(self):
        """Cierra sesión"""
        self.current_user = None

class ProductManager:
    """Gestor de productos"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    def add_product(self, name, description, price, stock, category, image_path, supplier_id):
        """Agrega nuevo producto"""
        if price < 0 or stock < 0:
            return False, "Precio y stock no pueden ser negativos"
        
        products = self.data_manager.load_data('products')
        
        new_product = {
            'id': str(uuid.uuid4()),
            'name': name,
            'description': description,
            'price': float(price),
            'stock': int(stock),
            'category': category,
            'image_path': image_path,
            'supplier_id': supplier_id,
            'created_at': datetime.now().isoformat()
        }
        
        products.append(new_product)
        
        if self.data_manager.save_data('products', products):
            return True, "Producto agregado exitosamente"
        else:
            return False, "Error al guardar producto"
    
    def update_product(self, product_id, name, description, price, stock, category, image_path):
        """Actualiza producto existente"""
        if price < 0 or stock < 0:
            return False, "Precio y stock no pueden ser negativos"
        
        products = self.data_manager.load_data('products')
        
        for product in products:
            if product['id'] == product_id:
                product['name'] = name
                product['description'] = description
                product['price'] = float(price)
                product['stock'] = int(stock)
                product['category'] = category
                if image_path:
                    product['image_path'] = image_path
                product['updated_at'] = datetime.now().isoformat()
                
                if self.data_manager.save_data('products', products):
                    return True, "Producto actualizado exitosamente"
                else:
                    return False, "Error al guardar producto"
        
        return False, "Producto no encontrado"
    
    def delete_product(self, product_id):
        """Elimina producto"""
        products = self.data_manager.load_data('products')
        
        for i, product in enumerate(products):
            if product['id'] == product_id:
                # Eliminar imagen si existe
                if product.get('image_path') and os.path.exists(product['image_path']):
                    try:
                        os.remove(product['image_path'])
                    except:
                        pass
                
                products.pop(i)
                
                if self.data_manager.save_data('products', products):
                    return True, "Producto eliminado exitosamente"
                else:
                    return False, "Error al eliminar producto"
        
        return False, "Producto no encontrado"
    
    def get_products_by_supplier(self, supplier_id):
        """Obtiene productos de un proveedor"""
        products = self.data_manager.load_data('products')
        return [p for p in products if p['supplier_id'] == supplier_id]
    
    def get_all_products(self):
        """Obtiene todos los productos"""
        return self.data_manager.load_data('products')
    
    def update_stock(self, product_id, quantity):
        """Actualiza stock de producto"""
        products = self.data_manager.load_data('products')
        
        for product in products:
            if product['id'] == product_id:
                if product['stock'] >= quantity:
                    product['stock'] -= quantity
                    self.data_manager.save_data('products', products)
                    return True
                else:
                    return False
        
        return False

class SalesManager:
    """Gestor de ventas"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager

    
    def make_purchase(self, customer_id, products_cart):
        """Realiza una compra"""
        sales = self.data_manager.load_data('sales')
        
        total_amount = 0
        sale_items = []
        
        for item in products_cart:
            product_id = item['product_id']
            quantity = item['quantity']
            price = item['price']
            
            total_amount += price * quantity
            sale_items.append({
                'product_id': product_id,
                'quantity': quantity,
                'price': price,
                'subtotal': price * quantity
            })
        
        new_sale = {
            'id': str(uuid.uuid4()),
            'customer_id': customer_id,
            'items': sale_items,
            'total_amount': total_amount,
            'date': datetime.now().isoformat()
        }
        
        sales.append(new_sale)
        
        if self.data_manager.save_data('sales', sales):
            return True, "Compra realizada exitosamente"
        else:
            return False, "Error al procesar compra"
    
    def get_customer_purchases(self, customer_id):
        """Obtiene compras de un cliente"""
        sales = self.data_manager.load_data('sales')
        return [s for s in sales if s['customer_id'] == customer_id]
    
    def get_supplier_sales(self, supplier_id):
        """Obtiene ventas de productos de un proveedor"""
        sales = self.data_manager.load_data('sales')
        products = self.data_manager.load_data('products')
        
        # Mapear productos por proveedor
        supplier_products = {p['id']: p for p in products if p['supplier_id'] == supplier_id}
        
        supplier_sales = []
        for sale in sales:
            for item in sale['items']:
                if item['product_id'] in supplier_products:
                    supplier_sales.append({
                        'sale_id': sale['id'],
                        'product_name': supplier_products[item['product_id']]['name'],
                        'quantity': item['quantity'],
                        'price': item['price'],
                        'subtotal': item['subtotal'],
                        'date': sale['date']
                    })
        
        return supplier_sales
    def update_sale(self, sale_id, new_status=None, tracking_number=None):
        """Actualiza el estado de pago o número de seguimiento de una venta"""
        sales = self.data_manager.load_data('sales')
    
        for sale in sales:
            if sale['id'] == sale_id:
                if new_status is not None:
                    sale['payment_status'] = new_status
                if tracking_number is not None:
                    sale['tracking_number'] = tracking_number
                sale['updated_at'] = datetime.now().isoformat()
                saved = self.data_manager.save_data('sales', sales)
                return saved, "Venta actualizada exitosamente" if saved else "Error al guardar cambios"
    
        return False, "Venta no encontrada"

    def delete_sale(self, sale_id):
        """Elimina una venta"""
        sales = self.data_manager.load_data('sales')
    
        for i, sale in enumerate(sales):
            if sale['id'] == sale_id:
                sales.pop(i)
                saved = self.data_manager.save_data('sales', sales)
                return saved, "Venta eliminada exitosamente" if saved else "Error al eliminar venta"
    
        return False, "Venta no encontrada"

    
class SupplierManager:
    """Gestor de proveedores"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    def get_all_suppliers(self):
        """Obtiene todos los proveedores"""
        users = self.data_manager.load_data('users')
        return [user for user in users if user['type'] == 'proveedor']
    
    def delete_supplier(self, supplier_id):
        """Elimina un proveedor"""
        users = self.data_manager.load_data('users')
        
        for i, user in enumerate(users):
            if user['id'] == supplier_id and user['type'] == 'proveedor':
                users.pop(i)
                if self.data_manager.save_data('users', users):
                    return True, "Proveedor eliminado exitosamente"
                else:
                    return False, "Error al eliminar proveedor"
        
        return False, "Proveedor no encontrado"
    
    def update_supplier_info(self, supplier_id, store_name, store_description, contact_phone):
        """Actualiza información de tienda del proveedor"""
        users = self.data_manager.load_data('users')
        
        for user in users:
            if user['id'] == supplier_id and user['type'] == 'proveedor':
                user['store_name'] = store_name
                user['store_description'] = store_description
                user['contact_phone'] = contact_phone
                user['updated_at'] = datetime.now().isoformat()
                
                if self.data_manager.save_data('users', users):
                    return True, "Información actualizada exitosamente"
                else:
                    return False, "Error al actualizar información"
        
        return False, "Proveedor no encontrado"

class LoginWindow:
    """Ventana de login"""
    
    def __init__(self, app):
        self.app = app
        self.window = ctk.CTkToplevel()
        self.window.title("Login - E-commerce Platform")
        self.window.geometry("400x500")
        self.window.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        # Título
        title = ctk.CTkLabel(self.window, text="Iniciar Sesión", 
                            font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=30)
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(pady=20, padx=40, fill="both", expand=True)
        
        # Email
        ctk.CTkLabel(main_frame, text="Email:").pack(pady=(20, 5))
        self.email_entry = ctk.CTkEntry(main_frame, placeholder_text="ejemplo@correo.com")
        self.email_entry.pack(pady=5, padx=20, fill="x")
        
        # Contraseña
        ctk.CTkLabel(main_frame, text="Contraseña:").pack(pady=(15, 5))
        self.password_entry = ctk.CTkEntry(main_frame, placeholder_text="Contraseña", show="*")
        self.password_entry.pack(pady=5, padx=20, fill="x")
        
        # Botón login
        login_btn = ctk.CTkButton(main_frame, text="Iniciar Sesión", 
                                 command=self.login_user, height=40)
        login_btn.pack(pady=20, padx=20, fill="x")
        
        # Separador
        ctk.CTkLabel(main_frame, text="¿No tienes cuenta?").pack(pady=(10, 5))
        
        # Botón registro
        register_btn = ctk.CTkButton(main_frame, text="Registrarse", 
                                   command=self.open_register, height=40,
                                   fg_color="transparent", border_width=2)
        register_btn.pack(pady=5, padx=20, fill="x")
    
    def login_user(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        
        if not email or not password:
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return
        
        success, message = self.app.auth_manager.login_user(email, password)
        
        if success:
            messagebox.showinfo("Éxito", message)
            self.window.destroy()
            self.app.show_main_interface()
        else:
            messagebox.showerror("Error", message)
    
    def open_register(self):
        self.window.destroy()
        RegisterWindow(self.app)

class RegisterWindow:
    """Ventana de registro"""
    
    def __init__(self, app):
        self.app = app
        self.window = ctk.CTkToplevel()
        self.window.title("Registro - E-commerce Platform")
        self.window.geometry("450x600")
        self.window.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        # Título
        title = ctk.CTkLabel(self.window, text="Crear Cuenta", 
                            font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=20)
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(pady=10, padx=40, fill="both", expand=True)
        
        # Nombre
        ctk.CTkLabel(main_frame, text="Nombre Completo:").pack(pady=(20, 5))
        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text="Juan Pérez")
        self.name_entry.pack(pady=5, padx=20, fill="x")
        
        # RUT
        ctk.CTkLabel(main_frame, text="RUT:").pack(pady=(15, 5))
        self.rut_entry = ctk.CTkEntry(main_frame, placeholder_text="12345678-9")
        self.rut_entry.pack(pady=5, padx=20, fill="x")
        
        # Email
        ctk.CTkLabel(main_frame, text="Email:").pack(pady=(15, 5))
        self.email_entry = ctk.CTkEntry(main_frame, placeholder_text="ejemplo@correo.com")
        self.email_entry.pack(pady=5, padx=20, fill="x")
        
        # Contraseña
        ctk.CTkLabel(main_frame, text="Contraseña:").pack(pady=(15, 5))
        self.password_entry = ctk.CTkEntry(main_frame, placeholder_text="Mínimo 6 caracteres", show="*")
        self.password_entry.pack(pady=5, padx=20, fill="x")
        
        # Tipo de usuario
        ctk.CTkLabel(main_frame, text="Tipo de Usuario:").pack(pady=(15, 5))
        self.user_type = ctk.CTkOptionMenu(main_frame, values=["Cliente", "Proveedor"])
        self.user_type.pack(pady=5, padx=20, fill="x")
        
        # Botón registro
        register_btn = ctk.CTkButton(main_frame, text="Registrarse", 
                                   command=self.register_user, height=40)
        register_btn.pack(pady=20, padx=20, fill="x")
        
        # Botón volver
        back_btn = ctk.CTkButton(main_frame, text="Volver al Login", 
                               command=self.back_to_login, height=40,
                               fg_color="transparent", border_width=2)
        back_btn.pack(pady=5, padx=20, fill="x")
    
    def register_user(self):
        name = self.name_entry.get()
        rut = self.rut_entry.get()
        email = self.email_entry.get()
        password = self.password_entry.get()
        user_type = self.user_type.get().lower()
        
        if not all([name, rut, email, password]):
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return
        
        success, message = self.app.auth_manager.register_user(
            rut, email, password, user_type, name
        )
        
        if success:
            messagebox.showinfo("Éxito", message)
            self.window.destroy()
            LoginWindow(self.app)
        else:
            messagebox.showerror("Error", message)
    
    def back_to_login(self):
        self.window.destroy()
        LoginWindow(self.app)

class ProductFormWindow:
    """Ventana para agregar/editar productos"""
    
    def __init__(self, app, product=None):
        self.app = app
        self.product = product
        self.image_path = None
        self.img_preview = None
        
        self.window = ctk.CTkToplevel()
        self.window.title("Agregar Producto" if not product else "Editar Producto")
        self.window.geometry("500x700")
        self.window.grab_set()
        
        self.setup_ui()
        
        if product:
            self.fill_form()
    
    def setup_ui(self):
        # Título
        title = ctk.CTkLabel(self.window, 
                            text="Agregar Producto" if not self.product else "Editar Producto",
                            font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=20)
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Nombre
        ctk.CTkLabel(main_frame, text="Nombre:").pack(pady=(20, 5))
        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text="Nombre del producto")
        self.name_entry.pack(pady=5, padx=20, fill="x")
        
        # Descripción
        ctk.CTkLabel(main_frame, text="Descripción:").pack(pady=(15, 5))
        self.description_entry = ctk.CTkTextbox(main_frame, height=80)
        self.description_entry.pack(pady=5, padx=20, fill="x")
        
        # Precio
        ctk.CTkLabel(main_frame, text="Precio:").pack(pady=(15, 5))
        self.price_entry = ctk.CTkEntry(main_frame, placeholder_text="0.00")
        self.price_entry.pack(pady=5, padx=20, fill="x")
        
        # Stock
        ctk.CTkLabel(main_frame, text="Stock:").pack(pady=(15, 5))
        self.stock_entry = ctk.CTkEntry(main_frame, placeholder_text="0")
        self.stock_entry.pack(pady=5, padx=20, fill="x")
        
        # Categoría
        ctk.CTkLabel(main_frame, text="Categoría:").pack(pady=(15, 5))
        self.category_entry = ctk.CTkEntry(main_frame, placeholder_text="Electrónicos, Ropa, etc.")
        self.category_entry.pack(pady=5, padx=20, fill="x")
        
        # Imagen
        ctk.CTkLabel(main_frame, text="Imagen:").pack(pady=(15, 5))
        
        # Frame para imagen
        img_frame = ctk.CTkFrame(main_frame)
        img_frame.pack(pady=5, padx=20, fill="x")
        
        # Botón seleccionar imagen
        select_img_btn = ctk.CTkButton(img_frame, text="Seleccionar Imagen", 
                                      command=self.select_image)
        select_img_btn.pack(pady=10)
        
        # Label para previsualización
        self.img_label = ctk.CTkLabel(img_frame, text="Sin imagen seleccionada")
        self.img_label.pack(pady=10)
        
        # Botones
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(pady=20, padx=20, fill="x")
        
        save_btn = ctk.CTkButton(btn_frame, text="Guardar", 
                               command=self.save_product, height=40)
        save_btn.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancelar", 
                                 command=self.window.destroy, height=40,
                                 fg_color="transparent", border_width=2)
        cancel_btn.pack(side="right", padx=(10, 0), expand=True, fill="x")
    
    def select_image(self):
        """Selecciona imagen para el producto"""
        filepath = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.gif *.bmp")]
        )
        
        if filepath:
            try:
                # Crear nombre único para la imagen
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"product_{timestamp}.jpg"
                destino = os.path.join(self.app.data_manager.images_dir, filename)
                
                # Copiar imagen
                shutil.copy(filepath, destino)
                self.image_path = destino
                
                # Mostrar previsualización
                img = Image.open(destino)
                img.thumbnail((150, 150))
                self.img_preview = ImageTk.PhotoImage(img)
                
                self.img_label.configure(image=self.img_preview, text="")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar imagen: {str(e)}")
    
    def fill_form(self):
        """Llena el formulario con datos del producto"""
        self.name_entry.insert(0, self.product['name'])
        self.description_entry.insert("1.0", self.product['description'])
        self.price_entry.insert(0, str(self.product['price']))
        self.stock_entry.insert(0, str(self.product['stock']))
        self.category_entry.insert(0, self.product['category'])
        
        # Cargar imagen si existe
        if self.product.get('image_path') and os.path.exists(self.product['image_path']):
            try:
                img = Image.open(self.product['image_path'])
                img.thumbnail((150, 150))
                self.img_preview = ImageTk.PhotoImage(img)
                self.img_label.configure(image=self.img_preview, text="")
                self.image_path = self.product['image_path']
            except:
                pass
    
    def save_product(self):
        """Guarda el producto"""
        name = self.name_entry.get()
        description = self.description_entry.get("1.0", "end-1c")
        price = self.price_entry.get()
        stock = self.stock_entry.get()
        category = self.category_entry.get()
        
        if not all([name, description, price, stock, category]):
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return
        
        try:
            price = float(price)
            stock = int(stock)
        except ValueError:
            messagebox.showerror("Error", "Precio y stock deben ser números válidos")
            return
        
        if self.product:  # Editar
            success, message = self.app.product_manager.update_product(
                self.product['id'], name, description, price, stock, category, self.image_path
            )
        else:  # Agregar
            success, message = self.app.product_manager.add_product(
                name, description, price, stock, category, self.image_path,
                self.app.auth_manager.current_user['id']
            )
        
        if success:
            messagebox.showinfo("Éxito", message)
            self.window.destroy()
            self.app.refresh_products()
        else:
            messagebox.showerror("Error", message)

class EcommerceApp:
    """Aplicación principal"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("E-commerce Platform")
        self.root.geometry("1000x700")
        
        # Inicializar managers
        self.data_manager = DataManager()
        self.auth_manager = AuthManager(self.data_manager)
        self.product_manager = ProductManager(self.data_manager)
        self.sales_manager = SalesManager(self.data_manager)
        self.supplier_manager = SupplierManager(self.data_manager)
        
        # Mostrar login
        self.show_login()
    
    def show_login(self):
        """Muestra ventana de login"""
        # Ocultar ventana principal
        self.root.withdraw()
        LoginWindow(self)
    
    def show_main_interface(self):
        """Muestra interfaz principal según tipo de usuario"""
        # Mostrar ventana principal
        self.root.deiconify()
        
        # Limpiar ventana
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Configurar interfaz según tipo de usuario
        if self.auth_manager.current_user['type'] == 'admin':
            self.setup_admin_interface()
        elif self.auth_manager.current_user['type'] == 'proveedor':
            self.setup_supplier_interface()
        else:
            self.setup_customer_interface()
    
    def setup_supplier_interface(self):
        """Configura interfaz para proveedores"""
        # Header
        header_frame = ctk.CTkFrame(self.root)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        # Título y usuario
        title_label = ctk.CTkLabel(header_frame, text="Panel de Proveedor", 
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(side="left", padx=20, pady=10)
        
        user_label = ctk.CTkLabel(header_frame, 
                                 text=f"Usuario: {self.auth_manager.current_user['name']}")
        user_label.pack(side="right", padx=20, pady=10)
        
        # Frame de navegación
        nav_frame = ctk.CTkFrame(self.root)
        nav_frame.pack(fill="x", padx=10, pady=5)
        
        # Botones de navegación
        self.inventory_btn = ctk.CTkButton(nav_frame, text="Inventario", 
                                          command=self.show_inventory)
        self.inventory_btn.pack(side="left", padx=5, pady=5)
        
        self.sales_btn = ctk.CTkButton(nav_frame, text="Ventas", 
                                      command=self.show_sales_report)
        self.sales_btn.pack(side="left", padx=5, pady=5)
        
        self.store_btn = ctk.CTkButton(nav_frame, text="Datos de Tienda", 
                                      command=self.show_store_settings)
        self.store_btn.pack(side="left", padx=5, pady=5)
        
        logout_btn = ctk.CTkButton(nav_frame, text="Cerrar Sesión", 
                                  command=self.logout, fg_color="red")
        logout_btn.pack(side="right", padx=5, pady=5)
        
        # Frame de contenido
        self.content_frame = ctk.CTkFrame(self.root)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Mostrar inventario por defecto
        self.show_inventory()
        
    def show_store_settings(self):
        """Muestra configuración de tienda para proveedores"""
        # Limpiar contenido
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Título
        title = ctk.CTkLabel(self.content_frame, text="Configuración de Tienda", 
                            font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=20)
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.content_frame)
        main_frame.pack(pady=10, padx=50, fill="both", expand=True)
        
        # Obtener datos actuales del proveedor
        current_user = self.auth_manager.current_user
        
        # Nombre de la tienda
        ctk.CTkLabel(main_frame, text="Nombre de la Tienda:").pack(pady=(20, 5))
        self.store_name_entry = ctk.CTkEntry(main_frame, placeholder_text="Nombre de tu tienda")
        self.store_name_entry.pack(pady=5, padx=20, fill="x")
        
        # Descripción de la tienda
        ctk.CTkLabel(main_frame, text="Descripción de la Tienda:").pack(pady=(15, 5))
        self.store_description_entry = ctk.CTkTextbox(main_frame, height=100)
        self.store_description_entry.pack(pady=5, padx=20, fill="x")
        
        # Teléfono de contacto
        ctk.CTkLabel(main_frame, text="Teléfono de Contacto:").pack(pady=(15, 5))
        self.contact_phone_entry = ctk.CTkEntry(main_frame, placeholder_text="+56 9 1234 5678")
        self.contact_phone_entry.pack(pady=5, padx=20, fill="x")
        
        # Llenar campos con datos existentes
        if current_user.get('store_name'):
            self.store_name_entry.insert(0, current_user['store_name'])
        if current_user.get('store_description'):
            self.store_description_entry.insert("1.0", current_user['store_description'])
        if current_user.get('contact_phone'):
            self.contact_phone_entry.insert(0, current_user['contact_phone'])
        
        # Botón guardar
        save_btn = ctk.CTkButton(main_frame, text="Guardar Cambios", 
                               command=self.save_store_settings, height=40)
        save_btn.pack(pady=30, padx=20, fill="x")
    
    def save_store_settings(self):
        """Guarda configuración de tienda"""
        store_name = self.store_name_entry.get()
        store_description = self.store_description_entry.get("1.0", "end-1c")
        contact_phone = self.contact_phone_entry.get()
        
        if not store_name:
            messagebox.showerror("Error", "El nombre de la tienda es obligatorio")
            return
        
        success, message = self.supplier_manager.update_supplier_info(
            self.auth_manager.current_user['id'], 
            store_name, 
            store_description, 
            contact_phone
        )
        
        if success:
            # Actualizar datos del usuario actual
            self.auth_manager.current_user['store_name'] = store_name
            self.auth_manager.current_user['store_description'] = store_description
            self.auth_manager.current_user['contact_phone'] = contact_phone
            
            messagebox.showinfo("Éxito", message)
        else:
            messagebox.showerror("Error", message)

    def setup_admin_interface(self):
        """Configura interfaz para admin"""
        # Header
        header_frame = ctk.CTkFrame(self.root)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        # Título y usuario
        title_label = ctk.CTkLabel(header_frame, text="Panel de Administrador", 
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(side="left", padx=20, pady=10)
        
        user_label = ctk.CTkLabel(header_frame, 
                                 text=f"Usuario: {self.auth_manager.current_user['name']}")
        user_label.pack(side="right", padx=20, pady=10)
        
        # Frame de navegación
        nav_frame = ctk.CTkFrame(self.root)
        nav_frame.pack(fill="x", padx=10, pady=5)
        
        # Botones de navegación
        self.suppliers_btn = ctk.CTkButton(nav_frame, text="Gestionar Proveedores", 
                                          command=self.show_suppliers_management)
        self.suppliers_btn.pack(side="left", padx=5, pady=5)
        
        logout_btn = ctk.CTkButton(nav_frame, text="Cerrar Sesión", 
                                  command=self.logout, fg_color="red")
        logout_btn.pack(side="right", padx=5, pady=5)
        
        # Frame de contenido
        self.content_frame = ctk.CTkFrame(self.root)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Mostrar gestión de proveedores por defecto
        self.show_suppliers_management()

    def show_suppliers_management(self):
        """Muestra gestión de proveedores"""
        # Limpiar contenido
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Título
        title = ctk.CTkLabel(self.content_frame, text="Gestión de Proveedores", 
                            font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=10)
        
        # Frame para proveedores
        suppliers_frame = ctk.CTkScrollableFrame(self.content_frame)
        suppliers_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Cargar proveedores
        suppliers = self.supplier_manager.get_all_suppliers()
        
        if not suppliers:
            no_suppliers_label = ctk.CTkLabel(suppliers_frame, 
                                            text="No hay proveedores registrados")
            no_suppliers_label.pack(pady=20)
            return
        
        # Mostrar proveedores
        for supplier in suppliers:
            self.create_supplier_card(suppliers_frame, supplier)
    
    def create_supplier_card(self, parent, supplier):
        """Crea tarjeta de proveedor"""
        # Frame principal
        card_frame = ctk.CTkFrame(parent)
        card_frame.pack(fill="x", padx=5, pady=5)
        
        # Información del proveedor
        info_frame = ctk.CTkFrame(card_frame)
        info_frame.pack(side="left", fill="both", expand=True)
        
        # Nombre
        name_label = ctk.CTkLabel(info_frame, text=supplier['name'], 
                                 font=ctk.CTkFont(size=16, weight="bold"))
        name_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Email y RUT
        email_label = ctk.CTkLabel(info_frame, text=f"Email: {supplier['email']}")
        email_label.pack(anchor="w", padx=10, pady=2)
        
        rut_label = ctk.CTkLabel(info_frame, text=f"RUT: {supplier['rut']}")
        rut_label.pack(anchor="w", padx=10, pady=2)
        
        # Información de tienda (si existe)
        if supplier.get('store_name'):
            store_label = ctk.CTkLabel(info_frame, text=f"Tienda: {supplier['store_name']}")
            store_label.pack(anchor="w", padx=10, pady=2)
        
        if supplier.get('contact_phone'):
            phone_label = ctk.CTkLabel(info_frame, text=f"Teléfono: {supplier['contact_phone']}")
            phone_label.pack(anchor="w", padx=10, pady=(2, 10))
        else:
            ctk.CTkLabel(info_frame, text="").pack(pady=(2, 10))  # Espaciado
        
        # Frame para botones
        btn_frame = ctk.CTkFrame(card_frame)
        btn_frame.pack(side="right", padx=10)
        
        # Botón eliminar
        delete_btn = ctk.CTkButton(btn_frame, text="Eliminar", 
                                 command=lambda s=supplier: self.delete_supplier(s),
                                 fg_color="red")
        delete_btn.pack(pady=10, padx=10)
    
    def delete_supplier(self, supplier):
        """Elimina proveedor"""
        if messagebox.askyesno("Confirmar", 
                              f"¿Estás seguro de eliminar al proveedor '{supplier['name']}'?\n\nEsta acción eliminará también todos sus productos."):
            # Eliminar productos del proveedor
            products = self.product_manager.get_products_by_supplier(supplier['id'])
            for product in products:
                self.product_manager.delete_product(product['id'])
            
            # Eliminar proveedor
            success, message = self.supplier_manager.delete_supplier(supplier['id'])
            if success:
                messagebox.showinfo("Éxito", message)
                self.show_suppliers_management()
            else:
                messagebox.showerror("Error", message)

    
    def setup_customer_interface(self):
        """Configura interfaz para clientes"""
        # Header
        header_frame = ctk.CTkFrame(self.root)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        # Título y usuario
        title_label = ctk.CTkLabel(header_frame, text="Catálogo de Productos", 
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(side="left", padx=20, pady=10)
        
        user_label = ctk.CTkLabel(header_frame, 
                                 text=f"Usuario: {self.auth_manager.current_user['name']}")
        user_label.pack(side="right", padx=20, pady=10)
        
        # Frame de navegación
        nav_frame = ctk.CTkFrame(self.root)
        nav_frame.pack(fill="x", padx=10, pady=5)
        
        # Botones de navegación
        self.catalog_btn = ctk.CTkButton(nav_frame, text="Catálogo", 
                                        command=self.show_catalog)
        self.catalog_btn.pack(side="left", padx=5, pady=5)
        
        self.history_btn = ctk.CTkButton(nav_frame, text="Mis Compras", 
                                        command=self.show_purchase_history)
        self.history_btn.pack(side="left", padx=5, pady=5)
        
        # Carrito
        self.cart_btn = ctk.CTkButton(nav_frame, text="Carrito (0)", 
                                     command=self.show_cart)
        self.cart_btn.pack(side="left", padx=5, pady=5)
        
        logout_btn = ctk.CTkButton(nav_frame, text="Cerrar Sesión", 
                                  command=self.logout, fg_color="red")
        logout_btn.pack(side="right", padx=5, pady=5)
        
        # Frame de contenido
        self.content_frame = ctk.CTkFrame(self.root)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Inicializar carrito
        self.cart = []
        
        # Mostrar catálogo por defecto
        self.show_catalog()
    
    def show_inventory(self):
        """Muestra inventario de productos del proveedor"""
        # Limpiar contenido
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Título
        title = ctk.CTkLabel(self.content_frame, text="Mi Inventario", 
                            font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=10)
        
        # Botón agregar producto
        add_btn = ctk.CTkButton(self.content_frame, text="Agregar Producto", 
                               command=self.add_product)
        add_btn.pack(pady=10)
        
        # Frame para productos
        products_frame = ctk.CTkScrollableFrame(self.content_frame)
        products_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Cargar productos del proveedor
        products = self.product_manager.get_products_by_supplier(
            self.auth_manager.current_user['id']
        )
        
        if not products:
            no_products_label = ctk.CTkLabel(products_frame, 
                                           text="No tienes productos registrados")
            no_products_label.pack(pady=20)
            return
        
        # Mostrar productos
        for product in products:
            self.create_product_card(products_frame, product, is_supplier=True)
        
        self.products_frame = products_frame
    
    def show_catalog(self):
        """Muestra catálogo de productos para clientes"""
        # Limpiar contenido
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Título
        title = ctk.CTkLabel(self.content_frame, text="Catálogo de Productos", 
                            font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=10)
        
        # Frame para productos
        products_frame = ctk.CTkScrollableFrame(self.content_frame)
        products_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Cargar todos los productos
        products = self.product_manager.get_all_products()
        
        if not products:
            no_products_label = ctk.CTkLabel(products_frame, 
                                           text="No hay productos disponibles")
            no_products_label.pack(pady=20)
            return
        
        # Mostrar productos
        for product in products:
            if product['stock'] > 0:  # Solo mostrar productos con stock
                self.create_product_card(products_frame, product, is_supplier=False)
    
    def create_product_card(self, parent, product, is_supplier=False):
        """Crea tarjeta de producto"""
        # Frame principal del producto
        card_frame = ctk.CTkFrame(parent)
        card_frame.pack(fill="x", padx=5, pady=5)
        
        # Frame horizontal para imagen y contenido
        content_frame = ctk.CTkFrame(card_frame)
        content_frame.pack(fill="x", padx=10, pady=10)
        
        # Frame para imagen
        img_frame = ctk.CTkFrame(content_frame)
        img_frame.pack(side="left", padx=(0, 10))
        
        # Cargar imagen
        if product.get('image_path') and os.path.exists(product['image_path']):
            try:
                img = Image.open(product['image_path'])
                img.thumbnail((100, 100))
                photo = ImageTk.PhotoImage(img)
                img_label = ctk.CTkLabel(img_frame, image=photo, text="")
                img_label.image = photo  # Mantener referencia
                img_label.pack(padx=10, pady=10)
            except:
                img_label = ctk.CTkLabel(img_frame, text="Sin\nImagen", 
                                       width=100, height=100)
                img_label.pack(padx=10, pady=10)
        else:
            img_label = ctk.CTkLabel(img_frame, text="Sin\nImagen", 
                                   width=100, height=100)
            img_label.pack(padx=10, pady=10)
        
        # Frame para información
        info_frame = ctk.CTkFrame(content_frame)
        info_frame.pack(side="left", fill="both", expand=True)
        
        # Nombre del producto
        name_label = ctk.CTkLabel(info_frame, text=product['name'], 
                                 font=ctk.CTkFont(size=16, weight="bold"))
        name_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Descripción
        desc_label = ctk.CTkLabel(info_frame, text=product['description'], 
                                 wraplength=300, justify="left")
        desc_label.pack(anchor="w", padx=10, pady=2)
        
        # Precio y stock
        price_label = ctk.CTkLabel(info_frame, text=f"Precio: ${product['price']:.2f}", 
                                  font=ctk.CTkFont(weight="bold"))
        price_label.pack(anchor="w", padx=10, pady=2)
        
        stock_label = ctk.CTkLabel(info_frame, text=f"Stock: {product['stock']} unidades")
        stock_label.pack(anchor="w", padx=10, pady=2)
        
        category_label = ctk.CTkLabel(info_frame, text=f"Categoría: {product['category']}")
        category_label.pack(anchor="w", padx=10, pady=(2, 10))
        
        # Frame para botones
        btn_frame = ctk.CTkFrame(content_frame)
        btn_frame.pack(side="right", padx=(10, 0))
        
        if is_supplier:
            # Botones para proveedor
            edit_btn = ctk.CTkButton(btn_frame, text="Editar", 
                                   command=lambda p=product: self.edit_product(p))
            edit_btn.pack(pady=5, padx=10)
            
            delete_btn = ctk.CTkButton(btn_frame, text="Eliminar", 
                                     command=lambda p=product: self.delete_product(p),
                                     fg_color="red")
            delete_btn.pack(pady=5, padx=10)
        else:
            # Botones para cliente
            if product['stock'] > 0:
                add_cart_btn = ctk.CTkButton(btn_frame, text="Agregar al Carrito", 
                                           command=lambda p=product: self.add_to_cart(p))
                add_cart_btn.pack(pady=5, padx=10)
            else:
                out_stock_label = ctk.CTkLabel(btn_frame, text="Sin Stock", 
                                             text_color="red")
                out_stock_label.pack(pady=5, padx=10)
    
    def add_product(self):
        """Abre ventana para agregar producto"""
        ProductFormWindow(self)
    
    def edit_product(self, product):
        """Abre ventana para editar producto"""
        ProductFormWindow(self, product)
    
    def delete_product(self, product):
        """Elimina producto"""
        if messagebox.askyesno("Confirmar", 
                              f"¿Estás seguro de eliminar '{product['name']}'?"):
            success, message = self.product_manager.delete_product(product['id'])
            if success:
                messagebox.showinfo("Éxito", message)
                self.refresh_products()
            else:
                messagebox.showerror("Error", message)
    
    def add_to_cart(self, product):
        """Agrega producto al carrito"""
        # Verificar si el producto ya está en el carrito
        for item in self.cart:
            if item['product_id'] == product['id']:
                if item['quantity'] < product['stock']:
                    item['quantity'] += 1
                    self.update_cart_button()
                    messagebox.showinfo("Éxito", f"Agregado al carrito: {product['name']}")
                else:
                    messagebox.showwarning("Advertencia", "No hay suficiente stock")
                return
        
        # Agregar nuevo producto al carrito
        self.cart.append({
            'product_id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'quantity': 1,
            'max_stock': product['stock']
        })
        
        self.update_cart_button()
        messagebox.showinfo("Éxito", f"Agregado al carrito: {product['name']}")
    
    def update_cart_button(self):
        """Actualiza contador del carrito"""
        total_items = sum(item['quantity'] for item in self.cart)
        self.cart_btn.configure(text=f"Carrito ({total_items})")
    
    def show_cart(self):
        """Muestra carrito de compras"""
        if not self.cart:
            messagebox.showinfo("Carrito", "Tu carrito está vacío")
            return
        
        # Ventana del carrito
        cart_window = ctk.CTkToplevel(self.root)
        cart_window.title("Carrito de Compras")
        cart_window.geometry("600x500")
        cart_window.grab_set()
        
        # Título
        title = ctk.CTkLabel(cart_window, text="Carrito de Compras", 
                            font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=10)
        
        # Frame para productos
        products_frame = ctk.CTkScrollableFrame(cart_window)
        products_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        total_amount = 0
        
        for i, item in enumerate(self.cart):
            # Frame del producto
            item_frame = ctk.CTkFrame(products_frame)
            item_frame.pack(fill="x", pady=5)
            
            # Información del producto
            info_label = ctk.CTkLabel(item_frame, text=f"{item['name']} - ${item['price']:.2f}")
            info_label.pack(side="left", padx=10, pady=10)
            
            # Cantidad
            qty_frame = ctk.CTkFrame(item_frame)
            qty_frame.pack(side="right", padx=10, pady=5)
            
            # Botón disminuir
            minus_btn = ctk.CTkButton(qty_frame, text="-", width=30,
                                    command=lambda idx=i: self.update_cart_quantity(idx, -1, cart_window))
            minus_btn.pack(side="left", padx=2)
            
            # Cantidad actual
            qty_label = ctk.CTkLabel(qty_frame, text=str(item['quantity']))
            qty_label.pack(side="left", padx=10)
            
            # Botón aumentar
            plus_btn = ctk.CTkButton(qty_frame, text="+", width=30,
                                   command=lambda idx=i: self.update_cart_quantity(idx, 1, cart_window))
            plus_btn.pack(side="left", padx=2)
            
            # Botón eliminar
            remove_btn = ctk.CTkButton(qty_frame, text="Eliminar", fg_color="red",
                                     command=lambda idx=i: self.remove_from_cart(idx, cart_window))
            remove_btn.pack(side="left", padx=5)
            
            # Subtotal
            subtotal = item['price'] * item['quantity']
            subtotal_label = ctk.CTkLabel(item_frame, text=f"Subtotal: ${subtotal:.2f}")
            subtotal_label.pack(side="right", padx=10, pady=10)
            
            total_amount += subtotal
        
        # Total
        total_frame = ctk.CTkFrame(cart_window)
        total_frame.pack(fill="x", padx=20, pady=10)
        
        total_label = ctk.CTkLabel(total_frame, text=f"Total: ${total_amount:.2f}", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        total_label.pack(side="left", padx=10, pady=10)
        
        # Botón comprar
        buy_btn = ctk.CTkButton(total_frame, text="Realizar Compra", 
                               command=lambda: self.process_purchase(cart_window))
        buy_btn.pack(side="right", padx=10, pady=10)
    
    def update_cart_quantity(self, item_index, change, cart_window):
        """Actualiza cantidad en el carrito"""
        if 0 <= item_index < len(self.cart):
            item = self.cart[item_index]
            new_quantity = item['quantity'] + change
            
            if new_quantity <= 0:
                self.cart.pop(item_index)
            elif new_quantity <= item['max_stock']:
                item['quantity'] = new_quantity
            else:
                messagebox.showwarning("Advertencia", "No hay suficiente stock")
                return
            
            self.update_cart_button()
            cart_window.destroy()
            self.show_cart()
    
    def remove_from_cart(self, item_index, cart_window):
        """Elimina producto del carrito"""
        if 0 <= item_index < len(self.cart):
            self.cart.pop(item_index)
            self.update_cart_button()
            cart_window.destroy()
            if self.cart:
                self.show_cart()
    
    def process_purchase(self, cart_window):
        """Procesa la compra"""
        if not self.cart:
            return
        
        # Verificar stock disponible
        for item in self.cart:
            if not self.product_manager.update_stock(item['product_id'], item['quantity']):
                messagebox.showerror("Error", f"No hay suficiente stock para {item['name']}")
                return
        
        # Registrar venta
        success, message = self.sales_manager.make_purchase(
            self.auth_manager.current_user['id'], self.cart
        )
        
        if success:
            messagebox.showinfo("Éxito", "Compra realizada exitosamente")
            self.cart = []
            self.update_cart_button()
            cart_window.destroy()
        else:
            messagebox.showerror("Error", message)
    
    def show_purchase_history(self):
        """Muestra historial de compras"""
        # Limpiar contenido
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Título
        title = ctk.CTkLabel(self.content_frame, text="Historial de Compras", 
                            font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=10)
        
        # Frame para compras
        purchases_frame = ctk.CTkScrollableFrame(self.content_frame)
        purchases_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Cargar compras del cliente
        purchases = self.sales_manager.get_customer_purchases(
            self.auth_manager.current_user['id']
        )
        
        if not purchases:
            no_purchases_label = ctk.CTkLabel(purchases_frame, 
                                            text="No tienes compras registradas")
            no_purchases_label.pack(pady=20)
            return
        
        # Mostrar compras
        for purchase in purchases:
            self.create_purchase_card(purchases_frame, purchase)
    
    def create_purchase_card(self, parent, purchase):
        """Crea tarjeta de compra"""
        # Frame principal
        card_frame = ctk.CTkFrame(parent)
        card_frame.pack(fill="x", padx=5, pady=5)
        
        # Información de la compra
        date_str = datetime.fromisoformat(purchase['date']).strftime('%d/%m/%Y %H:%M')
        
        header_label = ctk.CTkLabel(card_frame, 
                                   text=f"Compra del {date_str} - Total: ${purchase['total_amount']:.2f}",
                                   font=ctk.CTkFont(size=14, weight="bold"))
        header_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Productos comprados
        for item in purchase['items']:
            item_label = ctk.CTkLabel(card_frame, 
                                    text=f"  • Producto ID: {item['product_id']} - Cantidad: {item['quantity']} - Precio: ${item['price']:.2f}")
            item_label.pack(anchor="w", padx=20, pady=2)
    
    def show_sales_report(self):
        """Muestra reporte de ventas para proveedores"""
        # Limpiar contenido
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Título
        title = ctk.CTkLabel(self.content_frame, text="Reporte de Ventas", 
                            font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=10)
        
        # Frame para ventas
        sales_frame = ctk.CTkScrollableFrame(self.content_frame)
        sales_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Cargar ventas del proveedor
        sales = self.sales_manager.get_supplier_sales(
            self.auth_manager.current_user['id']
        )
        
        if not sales:
            no_sales_label = ctk.CTkLabel(sales_frame, 
                                        text="No tienes ventas registradas")
            no_sales_label.pack(pady=20)
            return
        
        # Calcular totales
        total_sales = len(sales)
        total_revenue = sum(sale['subtotal'] for sale in sales)
        
        # Mostrar resumen
        summary_frame = ctk.CTkFrame(sales_frame)
        summary_frame.pack(fill="x", padx=5, pady=10)
        
        summary_label = ctk.CTkLabel(summary_frame, 
                                   text=f"Total de ventas: {total_sales} | Ingresos totales: ${total_revenue:.2f}",
                                   font=ctk.CTkFont(size=14, weight="bold"))
        summary_label.pack(pady=10)
        
        # Mostrar ventas
        for sale in sales:
            self.create_sale_card(sales_frame, sale)
    
    def create_sale_card(self, parent, sale):
        """Crea tarjeta de venta"""
        # Frame principal
        card_frame = ctk.CTkFrame(parent)
        card_frame.pack(fill="x", padx=5, pady=5)
        
        # Información de la venta
        date_str = datetime.fromisoformat(sale['date']).strftime('%d/%m/%Y %H:%M')
        
        info_text = f"Producto: {sale['product_name']} | Cantidad: {sale['quantity']} | Precio: ${sale['price']:.2f} | Total: ${sale['subtotal']:.2f} | Fecha: {date_str}"
        
        info_label = ctk.CTkLabel(card_frame, text=info_text)
        info_label.pack(anchor="w", padx=10, pady=10)
    
    def refresh_products(self):
        """Refresca la vista de productos"""
        if self.auth_manager.current_user['type'] == 'proveedor':
            self.show_inventory()
        else:
            self.show_catalog()
    
    def logout(self):
        """Cierra sesión"""
        self.auth_manager.logout_user()
        self.root.withdraw()
        self.show_login()
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()

if __name__ == "__main__":
    app = EcommerceApp()
    app.run()