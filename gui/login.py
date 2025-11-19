"""
Pantalla de login para el Bot Didi
"""
import tkinter as tk
from tkinter import ttk, messagebox
import requests


class LoginWindow:
    """Ventana de login con Tkinter"""

    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.token = None
        self.usuario = None

        # Configurar ventana
        self.root.title("Bot Didi - Login")
        self.root.geometry("400x580")
        self.root.resizable(False, False)

        # Centrar ventana
        self.centrar_ventana()

        # Crear interfaz
        self.crear_interfaz()

    def centrar_ventana(self):
        """Centra la ventana en la pantalla"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def crear_interfaz(self):
        """Crea la interfaz de login"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="40")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Logo/Título
        titulo = tk.Label(
            main_frame,
            text="BOT DIDI",
            font=("Arial", 28, "bold"),
            fg="#2C3E50"
        )
        titulo.pack(pady=(0, 10))

        subtitulo = tk.Label(
            main_frame,
            text="Sistema de Automatizacion",
            font=("Arial", 12),
            fg="#7F8C8D"
        )
        subtitulo.pack(pady=(0, 40))

        # Frame del formulario
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=20)

        # Username
        tk.Label(
            form_frame,
            text="Usuario:",
            font=("Arial", 10, "bold"),
            fg="#2C3E50"
        ).pack(anchor=tk.W, pady=(0, 5))

        self.username_entry = ttk.Entry(form_frame, font=("Arial", 11))
        self.username_entry.pack(fill=tk.X, pady=(0, 20), ipady=5)
        self.username_entry.focus()

        # Password
        tk.Label(
            form_frame,
            text="Contrasena:",
            font=("Arial", 10, "bold"),
            fg="#2C3E50"
        ).pack(anchor=tk.W, pady=(0, 5))

        self.password_entry = ttk.Entry(form_frame, font=("Arial", 11), show="*")
        self.password_entry.pack(fill=tk.X, pady=(0, 10), ipady=5)

        # Checkbox "Mostrar contraseña"
        self.mostrar_password_var = tk.BooleanVar()
        mostrar_check = ttk.Checkbutton(
            form_frame,
            text="Mostrar contrasena",
            variable=self.mostrar_password_var,
            command=self.toggle_password
        )
        mostrar_check.pack(anchor=tk.W, pady=(0, 20))

        # Tipo de recorrido
        tk.Label(
            form_frame,
            text="Tipo de Recorrido:",
            font=("Arial", 10, "bold"),
            fg="#2C3E50"
        ).pack(anchor=tk.W, pady=(0, 5))

        self.tipo_recorrido_var = tk.StringVar(value="CreditCard")
        tipo_combo = ttk.Combobox(
            form_frame,
            textvariable=self.tipo_recorrido_var,
            values=["CreditCard", "Loan"],
            state="readonly",
            font=("Arial", 11)
        )
        tipo_combo.pack(fill=tk.X, pady=(0, 30), ipady=5)
        tipo_combo.current(0)

        # Botón de login
        self.btn_login = tk.Button(
            form_frame,
            text="INICIAR SESION",
            font=("Arial", 12, "bold"),
            bg="#27AE60",
            fg="white",
            height=2,
            cursor="hand2",
            command=self.intentar_login
        )
        self.btn_login.pack(fill=tk.X, pady=(0, 15))

        # Bind Enter key para submit
        self.username_entry.bind('<Return>', lambda e: self.intentar_login())
        self.password_entry.bind('<Return>', lambda e: self.intentar_login())

        # Estado del servidor
        self.status_label = tk.Label(
            form_frame,
            text="",
            font=("Arial", 9),
            fg="#E74C3C"
        )
        self.status_label.pack(pady=(10, 0))

        # Verificar estado del servidor
        self.verificar_servidor()

        # Footer
        footer = tk.Label(
            main_frame,
            text="v1.0 - Sistema de Automatizacion RPA",
            font=("Arial", 8),
            fg="#95A5A6"
        )
        footer.pack(side=tk.BOTTOM, pady=(20, 0))

    def toggle_password(self):
        """Muestra u oculta la contraseña"""
        if self.mostrar_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def verificar_servidor(self):
        """Verifica si el servidor Flask está disponible"""
        try:
            response = requests.get('http://localhost:5000/health', timeout=2)
            if response.status_code == 200:
                self.status_label.config(text="Servidor conectado", fg="#27AE60")
                return True
        except Exception:
            self.status_label.config(
                text="Error: Servidor no disponible",
                fg="#E74C3C"
            )
            return False

    def intentar_login(self):
        """Intenta hacer login con las credenciales"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        # Validaciones básicas
        if not username:
            messagebox.showerror("Error", "Por favor ingrese su usuario")
            self.username_entry.focus()
            return

        if not password:
            messagebox.showerror("Error", "Por favor ingrese su contrasena")
            self.password_entry.focus()
            return

        # Deshabilitar botón mientras se procesa
        self.btn_login.config(state=tk.DISABLED, text="VERIFICANDO...")
        self.root.update()

        try:
            # Hacer petición de login (timeout aumentado a 15 segundos)
            response = requests.post(
                'http://localhost:5000/auth/login',
                json={'username': username, 'password': password},
                timeout=15
            )

            data = response.json()

            if response.status_code == 200:
                # Login exitoso
                self.token = data['token']
                self.usuario = data['usuario']
                tipo_recorrido = self.tipo_recorrido_var.get()

                messagebox.showinfo(
                    "Exito",
                    f"Bienvenido, {self.usuario.get('nombre_completo', username)}!\nTipo: {tipo_recorrido}"
                )

                # Cerrar ventana de login y continuar
                self.root.destroy()
                self.on_login_success(self.token, self.usuario, tipo_recorrido)

            else:
                # Error de login
                messagebox.showerror("Error de autenticacion", data.get('message', 'Credenciales invalidas'))
                self.password_entry.delete(0, tk.END)
                self.password_entry.focus()

        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Error de conexion",
                "No se pudo conectar al servidor.\nAsegurese de que el backend este ejecutandose."
            )
        except requests.exceptions.Timeout:
            messagebox.showerror("Error", "Tiempo de espera agotado")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
        finally:
            # Rehabilitar botón
            self.btn_login.config(state=tk.NORMAL, text="INICIAR SESION")


def mostrar_login(on_login_success):
    """Muestra la ventana de login y retorna el token y usuario"""
    root = tk.Tk()
    login_window = LoginWindow(root, on_login_success)
    root.mainloop()
