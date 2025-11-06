"""
Pantalla de activación de licencia para el Bot Didi
"""
import tkinter as tk
from tkinter import ttk, messagebox
import requests

from backend.license_utils import (
    generar_hardware_id,
    obtener_info_maquina,
    guardar_token_local,
    validar_formato_clave
)


class ActivationWindow:
    """Ventana de activación de licencia"""

    def __init__(self, root, on_activation_success):
        self.root = root
        self.on_activation_success = on_activation_success
        self.clave_activada = None

        # Configurar ventana
        self.root.title("Bot Didi - Activación de Licencia")
        self.root.geometry("500x750")
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
        """Crea la interfaz de activación"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Logo/Título
        titulo = tk.Label(
            main_frame,
            text="⚡ ACTIVACIÓN DE LICENCIA",
            font=("Arial", 24, "bold"),
            fg="#2C3E50"
        )
        titulo.pack(pady=(0, 10))

        subtitulo = tk.Label(
            main_frame,
            text="Bot Didi - Sistema de Automatización",
            font=("Arial", 11),
            fg="#7F8C8D"
        )
        subtitulo.pack(pady=(0, 30))

        # Info de la máquina
        info_frame = ttk.LabelFrame(main_frame, text="📋 Información de Esta Máquina", padding="15")
        info_frame.pack(fill=tk.X, pady=(0, 20))

        info_maquina = obtener_info_maquina()
        hardware_id, hw_componentes = generar_hardware_id()

        tk.Label(
            info_frame,
            text=f"Nombre: {info_maquina['nombre_maquina']}",
            font=("Consolas", 9),
            anchor='w'
        ).pack(fill=tk.X, pady=2)

        tk.Label(
            info_frame,
            text=f"Usuario: {info_maquina['usuario_sistema']}",
            font=("Consolas", 9),
            anchor='w'
        ).pack(fill=tk.X, pady=2)

        tk.Label(
            info_frame,
            text=f"Sistema: {info_maquina['sistema_operativo']}",
            font=("Consolas", 9),
            anchor='w'
        ).pack(fill=tk.X, pady=2)

        tk.Label(
            info_frame,
            text=f"Hardware ID: {hardware_id}",
            font=("Consolas", 8),
            fg="#3498DB",
            anchor='w'
        ).pack(fill=tk.X, pady=2)

        # Separador
        ttk.Separator(info_frame, orient='horizontal').pack(fill=tk.X, pady=5)

        # Mostrar componentes individuales
        tk.Label(
            info_frame,
            text="Componentes de Hardware:",
            font=("Consolas", 8, "bold"),
            anchor='w'
        ).pack(fill=tk.X, pady=(5, 2))

        tk.Label(
            info_frame,
            text=f"  MAC: {hw_componentes.get('mac_address', 'unknown')}",
            font=("Consolas", 7),
            fg="#555",
            anchor='w'
        ).pack(fill=tk.X, pady=1)

        tk.Label(
            info_frame,
            text=f"  Hostname: {hw_componentes.get('hostname', 'unknown')}",
            font=("Consolas", 7),
            fg="#555",
            anchor='w'
        ).pack(fill=tk.X, pady=1)

        tk.Label(
            info_frame,
            text=f"  OS: {hw_componentes.get('os_info', 'unknown')}",
            font=("Consolas", 7),
            fg="#555",
            anchor='w'
        ).pack(fill=tk.X, pady=1)

        tk.Label(
            info_frame,
            text=f"  CPU: {hw_componentes.get('processor', 'unknown')}",
            font=("Consolas", 7),
            fg="#555",
            anchor='w'
        ).pack(fill=tk.X, pady=1)

        mb_uuid = hw_componentes.get('motherboard_uuid', 'unknown')
        tk.Label(
            info_frame,
            text=f"  MB UUID: {mb_uuid[:30]}..." if len(mb_uuid) > 30 else f"  MB UUID: {mb_uuid}",
            font=("Consolas", 7),
            fg="#555",
            anchor='w'
        ).pack(fill=tk.X, pady=1)

        # Guardar hardware_id y componentes para usarlo después
        self.hardware_id = hardware_id
        self.hw_componentes = hw_componentes
        self.info_maquina = info_maquina

        # Instrucciones
        instrucciones = tk.Label(
            main_frame,
            text="Ingrese su clave de licencia para activar el bot en esta máquina.\n"
                 "La clave tiene el formato: DIDI-XXXX-XXXX-XXXX",
            font=("Arial", 9),
            fg="#555",
            justify=tk.LEFT
        )
        instrucciones.pack(pady=(0, 20))

        # Frame de activación
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=10)

        # Label de clave
        tk.Label(
            form_frame,
            text="Clave de Licencia:",
            font=("Arial", 10, "bold"),
            fg="#2C3E50"
        ).pack(anchor=tk.W, pady=(0, 5))

        # Entry de clave (con formato automático)
        self.clave_entry = ttk.Entry(form_frame, font=("Consolas", 14), width=25)
        self.clave_entry.pack(fill=tk.X, pady=(0, 5), ipady=8)
        self.clave_entry.focus()

        # Bind para formatear automáticamente
        self.clave_entry.bind('<KeyRelease>', self.formatear_clave)

        # Ayuda de formato
        formato_label = tk.Label(
            form_frame,
            text="Ejemplo: DIDI-A3F2-9B7E-4C12",
            font=("Arial", 8),
            fg="#95A5A6"
        )
        formato_label.pack(anchor=tk.W, pady=(0, 20))

        # Botón de activar
        self.btn_activar = tk.Button(
            form_frame,
            text="🔓 ACTIVAR LICENCIA",
            font=("Arial", 12, "bold"),
            bg="#27AE60",
            fg="white",
            height=2,
            cursor="hand2",
            command=self.activar_licencia
        )
        self.btn_activar.pack(fill=tk.X, pady=(0, 10))

        # Bind Enter para activar
        self.clave_entry.bind('<Return>', lambda e: self.activar_licencia())

        # Estado
        self.status_label = tk.Label(
            form_frame,
            text="",
            font=("Arial", 9),
            fg="#E74C3C"
        )
        self.status_label.pack(pady=(10, 0))

        # Verificar servidor
        self.verificar_servidor()

        # Información adicional
        info_box = tk.Text(
            main_frame,
            height=5,
            font=("Arial", 8),
            bg="#ECF0F1",
            fg="#34495E",
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        info_box.pack(fill=tk.X, pady=(20, 0))
        info_box.insert('1.0',
            "ℹ️ IMPORTANTE:\n"
            "• Cada clave solo puede activarse en UNA máquina\n"
            "• Una vez activada, la clave queda vinculada a esta máquina\n"
            "• Puede reactivar en esta máquina ilimitadas veces\n"
            "• No se puede transferir a otra máquina"
        )
        info_box.config(state=tk.DISABLED)

    def formatear_clave(self, event=None):
        """Formatea automáticamente la clave mientras se escribe"""
        texto = self.clave_entry.get().upper().replace('-', '').replace(' ', '')

        # Limitar a caracteres válidos
        texto = ''.join(c for c in texto if c.isalnum())

        # Limitar longitud (4+4+4+4 = 16 caracteres)
        texto = texto[:16]

        # Formatear con guiones
        if len(texto) > 0:
            partes = []
            partes.append(texto[:4])
            if len(texto) > 4:
                partes.append(texto[4:8])
            if len(texto) > 8:
                partes.append(texto[8:12])
            if len(texto) > 12:
                partes.append(texto[12:16])

            # Juntar con guiones (sin DIDI- prefijo aún)
            formatted = '-'.join(partes)

            # Guardar posición del cursor
            cursor_pos = self.clave_entry.index(tk.INSERT)

            # Actualizar entry
            self.clave_entry.delete(0, tk.END)
            self.clave_entry.insert(0, formatted)

            # Restaurar cursor (aproximadamente)
            new_pos = min(cursor_pos, len(formatted))
            self.clave_entry.icursor(new_pos)

    def verificar_servidor(self):
        """Verifica si el servidor Flask está disponible"""
        try:
            response = requests.get('http://localhost:5000/health', timeout=2)
            if response.status_code == 200:
                self.status_label.config(text="✓ Servidor conectado", fg="#27AE60")
                return True
        except Exception:
            self.status_label.config(
                text="✗ Error: Servidor no disponible. Reinicie la aplicación.",
                fg="#E74C3C"
            )
            self.btn_activar.config(state=tk.DISABLED)
            return False

    def activar_licencia(self):
        """Intenta activar la licencia con la clave ingresada"""
        clave_input = self.clave_entry.get().strip().upper()

        # Validar que no esté vacío
        if not clave_input:
            messagebox.showerror("Error", "Por favor ingrese una clave de licencia")
            self.clave_entry.focus()
            return

        # Agregar prefijo DIDI- si no lo tiene
        if not clave_input.startswith('DIDI-'):
            clave_input = f"DIDI-{clave_input}"

        # Validar formato
        if not validar_formato_clave(clave_input):
            messagebox.showerror(
                "Error de Formato",
                "La clave debe tener el formato:\nDIDI-XXXX-XXXX-XXXX\n\n"
                "Donde X son letras o números (sin 0, 1, O, I)"
            )
            self.clave_entry.focus()
            return

        # Deshabilitar botón mientras procesa
        self.btn_activar.config(state=tk.DISABLED, text="ACTIVANDO...")
        self.status_label.config(text="Validando con el servidor...", fg="#3498DB")
        self.root.update()

        try:
            # Hacer petición de activación
            response = requests.post(
                'http://localhost:5000/licencias/activar',
                json={
                    'clave': clave_input,
                    'hardware_id': self.hardware_id,
                    'nombre_maquina': self.info_maquina['nombre_maquina'],
                    'usuario_sistema': self.info_maquina['usuario_sistema'],
                    'hw_componentes': self.hw_componentes
                },
                timeout=10
            )

            data = response.json()

            if response.status_code == 200:
                # Activación exitosa
                messagebox.showinfo(
                    "¡Activación Exitosa! ✓",
                    f"Licencia activada correctamente en esta máquina.\n\n"
                    f"Clave: {clave_input}\n"
                    f"Máquina: {self.info_maquina['nombre_maquina']}\n\n"
                    f"Puede usar el bot normalmente."
                )

                # Guardar token local
                guardar_token_local(clave_input, self.hardware_id)

                # Guardar clave activada
                self.clave_activada = clave_input

                # Cerrar ventana y continuar
                self.root.destroy()
                self.on_activation_success(clave_input)

            else:
                # Error de activación
                mensaje_error = data.get('message', 'Error desconocido')
                messagebox.showerror("Error de Activación", mensaje_error)
                self.status_label.config(text="", fg="#E74C3C")

        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Error de Conexión",
                "No se pudo conectar al servidor.\n"
                "Asegúrese de que el backend esté ejecutándose."
            )
            self.status_label.config(text="Error de conexión", fg="#E74C3C")
        except requests.exceptions.Timeout:
            messagebox.showerror("Error", "Tiempo de espera agotado")
            self.status_label.config(text="Timeout", fg="#E74C3C")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
            self.status_label.config(text=f"Error: {str(e)}", fg="#E74C3C")
        finally:
            # Rehabilitar botón
            self.btn_activar.config(state=tk.NORMAL, text="🔓 ACTIVAR LICENCIA")


def mostrar_activacion(on_activation_success):
    """Muestra la ventana de activación"""
    root = tk.Tk()
    activation_window = ActivationWindow(root, on_activation_success)
    root.mainloop()
