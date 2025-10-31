"""
Interfaz gráfica con Tkinter para el Bot Didi
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import queue
import csv
import requests
from datetime import datetime
from threading import Thread

import config.settings as settings
from config.settings import log_queue, stats_queue


class BotDidiGUI:
    def __init__(self, root, ejecutar_bot_callback, token, usuario):
        self.root = root
        self.root.title("🤖 Bot Didi - Sistema Automatizado")
        self.root.geometry("700x750")
        self.root.resizable(True, True)

        self.ejecutar_bot_callback = ejecutar_bot_callback
        self.token = token
        self.usuario = usuario

        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')

        # Variables
        self.estado_var = tk.StringVar(value="LISTO")
        self.clientes_var = tk.StringVar(value="0")
        self.exitosos_var = tk.StringVar(value="0")
        self.errores_var = tk.StringVar(value="0")
        self.pagina_var = tk.StringVar(value="0")

        self.crear_interfaz()

        # Iniciar actualización del log
        self.actualizar_log()
        self.actualizar_stats()

    def crear_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título y usuario
        titulo = tk.Label(main_frame, text="🤖 BOT DIDI", font=("Arial", 20, "bold"), fg="#2C3E50")
        titulo.pack(pady=10)

        # Mostrar usuario logueado
        nombre_usuario = self.usuario.get('nombre_completo') or self.usuario.get('username')
        usuario_label = tk.Label(main_frame,
                                 text=f"Usuario: {nombre_usuario} ({self.usuario.get('rol', 'operador').title()})",
                                 font=("Arial", 9), fg="#7F8C8D")
        usuario_label.pack(pady=(0, 10))

        # Estado
        estado_frame = ttk.Frame(main_frame)
        estado_frame.pack(fill=tk.X, pady=5)

        tk.Label(estado_frame, text="Estado:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.estado_label = tk.Label(estado_frame, textvariable=self.estado_var,
                                     font=("Arial", 10), fg="#27AE60")
        self.estado_label.pack(side=tk.LEFT, padx=10)

        # Botones de control
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)

        self.btn_iniciar = tk.Button(btn_frame, text="▶  INICIAR BOT",
                                     font=("Arial", 14, "bold"),
                                     bg="#27AE60", fg="white",
                                     width=20, height=2,
                                     command=self.iniciar_bot)
        self.btn_iniciar.pack(side=tk.LEFT, padx=5)

        self.btn_detener = tk.Button(btn_frame, text="⬛  DETENER",
                                     font=("Arial", 14, "bold"),
                                     bg="#E74C3C", fg="white",
                                     width=15, height=2,
                                     command=self.detener_bot,
                                     state=tk.DISABLED)
        self.btn_detener.pack(side=tk.LEFT, padx=5)

        # Estadísticas
        stats_frame = ttk.LabelFrame(main_frame, text="📊 Estadísticas en Vivo", padding="10")
        stats_frame.pack(fill=tk.X, pady=10)

        # Grid de estadísticas
        tk.Label(stats_frame, text="Clientes procesados:", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
        tk.Label(stats_frame, textvariable=self.clientes_var, font=("Arial", 9, "bold"), fg="#3498DB").grid(row=0, column=1, sticky=tk.W, padx=10)

        tk.Label(stats_frame, text="Exitosos:", font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
        tk.Label(stats_frame, textvariable=self.exitosos_var, font=("Arial", 9, "bold"), fg="#27AE60").grid(row=1, column=1, sticky=tk.W, padx=10)

        tk.Label(stats_frame, text="Errores:", font=("Arial", 9)).grid(row=2, column=0, sticky=tk.W, pady=2)
        tk.Label(stats_frame, textvariable=self.errores_var, font=("Arial", 9, "bold"), fg="#E74C3C").grid(row=2, column=1, sticky=tk.W, padx=10)

        tk.Label(stats_frame, text="Página actual:", font=("Arial", 9)).grid(row=3, column=0, sticky=tk.W, pady=2)
        tk.Label(stats_frame, textvariable=self.pagina_var, font=("Arial", 9, "bold"), fg="#8E44AD").grid(row=3, column=1, sticky=tk.W, padx=10)

        # Log
        log_frame = ttk.LabelFrame(main_frame, text="📝 Log de Actividad", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, state=tk.DISABLED,
                                                  font=("Consolas", 9), bg="#2C3E50", fg="#ECF0F1")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Botones de reportes
        reportes_frame = ttk.Frame(main_frame)
        reportes_frame.pack(pady=5)

        btn_stats = tk.Button(reportes_frame, text="📊 Ver Estadísticas Completas",
                             font=("Arial", 10),
                             bg="#3498DB", fg="white",
                             command=self.ver_estadisticas)
        btn_stats.pack(side=tk.LEFT, padx=5)

        btn_reporte = tk.Button(reportes_frame, text="💾 Descargar Reporte CSV",
                               font=("Arial", 10),
                               bg="#9B59B6", fg="white",
                               command=self.generar_reporte)
        btn_reporte.pack(side=tk.LEFT, padx=5)

    def agregar_log(self, mensaje):
        """Agrega mensaje al log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, mensaje + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def actualizar_log(self):
        """Actualiza el log desde la cola"""
        try:
            while True:
                mensaje = log_queue.get_nowait()
                self.agregar_log(mensaje)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.actualizar_log)

    def actualizar_stats(self):
        """Actualiza las estadísticas desde la cola"""
        try:
            while True:
                stats = stats_queue.get_nowait()
                self.clientes_var.set(str(stats['total']))
                self.exitosos_var.set(str(stats['exitosos']))
                self.errores_var.set(str(stats['errores']))
                self.pagina_var.set(str(stats['pagina']))
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.actualizar_stats)

    def iniciar_bot(self):
        """Inicia el bot en un thread separado"""
        if settings.bot_corriendo:
            messagebox.showwarning("Bot en ejecución", "El bot ya está corriendo")
            return

        self.estado_var.set("PROCESANDO")
        self.estado_label.config(fg="#E67E22")
        self.btn_iniciar.config(state=tk.DISABLED)
        self.btn_detener.config(state=tk.NORMAL)

        # Iniciar bot en thread pasándole el token
        bot_thread = Thread(target=lambda: self.ejecutar_bot_callback(self.token), daemon=True)
        bot_thread.start()

        # Verificar cuando termine
        self.verificar_estado_bot()

    def detener_bot(self):
        """Detiene el bot"""
        respuesta = messagebox.askyesno("Detener Bot",
                                        "¿Estás seguro de que quieres detener el bot?")
        if respuesta:
            settings.detener_bot = True
            log_queue.put("[!] Deteniendo bot...")

    def verificar_estado_bot(self):
        """Verifica el estado del bot periódicamente"""
        if not settings.bot_corriendo:
            self.estado_var.set("LISTO")
            self.estado_label.config(fg="#27AE60")
            self.btn_iniciar.config(state=tk.NORMAL)
            self.btn_detener.config(state=tk.DISABLED)
        else:
            self.root.after(1000, self.verificar_estado_bot)

    def ver_estadisticas(self):
        """Muestra ventana con estadísticas completas"""
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get('http://localhost:5000/estadisticas?dias=30',
                                  headers=headers, timeout=5)
            if response.status_code == 200:
                datos = response.json()['datos']

                # Crear ventana de estadísticas
                stats_window = tk.Toplevel(self.root)
                stats_window.title("Estadísticas Completas (últimos 30 días)")
                stats_window.geometry("500x400")

                # Tabla de estadísticas
                tree = ttk.Treeview(stats_window, columns=('Fecha', 'Clientes'), show='headings')
                tree.heading('Fecha', text='Fecha')
                tree.heading('Clientes', text='Clientes Procesados')

                tree.column('Fecha', width=200)
                tree.column('Clientes', width=200)

                for dato in datos:
                    tree.insert('', tk.END, values=(dato['fecha'], dato['clientes_procesados']))

                tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            else:
                messagebox.showerror("Error", "No se pudieron obtener las estadísticas")
        except Exception as e:
            messagebox.showerror("Error", f"Backend no disponible: {e}")

    def generar_reporte(self):
        """Genera y descarga un reporte CSV de clientes procesados hoy"""
        try:
            # Obtener clientes procesados hoy desde el backend
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get('http://localhost:5000/clientes_hoy',
                                  headers=headers, timeout=5)
            if response.status_code != 200:
                messagebox.showerror("Error", "No se pudieron obtener los datos del reporte")
                return

            datos = response.json()
            clientes = datos.get('clientes', [])
            total = datos.get('total', 0)
            exitosos = datos.get('exitosos', 0)
            errores = datos.get('errores', 0)

            if total == 0:
                messagebox.showinfo("Reporte", "No hay clientes procesados hoy para generar reporte")
                return

            # Pedir al usuario dónde guardar el archivo
            fecha_hoy = datetime.now().strftime('%Y-%m-%d')
            archivo_default = f"Reporte_Clientes_{fecha_hoy}.csv"

            archivo = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=archivo_default,
                title="Guardar Reporte"
            )

            if not archivo:  # Usuario canceló
                return

            # Crear el archivo CSV
            with open(archivo, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)

                # Encabezado del reporte
                writer.writerow(['REPORTE DE CLIENTES PROCESADOS'])
                writer.writerow(['Fecha', fecha_hoy])
                writer.writerow(['Total de clientes', total])
                writer.writerow(['Exitosos', exitosos])
                writer.writerow(['Errores', errores])
                writer.writerow([])  # Línea en blanco

                # Encabezados de la tabla
                writer.writerow(['ID', 'Nombre del Cliente', 'CFRNID', 'Monto Total', 'Estado', 'Fecha/Hora Procesado'])

                # Datos de clientes
                for cliente in clientes:
                    writer.writerow([
                        cliente['id'],
                        cliente['nombre_cliente'],
                        cliente.get('cfrnid', 'N/A'),
                        cliente.get('monto_total', 'N/A'),
                        cliente['estado'].upper(),
                        cliente['fecha_procesado']
                    ])

            messagebox.showinfo("Éxito", f"Reporte generado exitosamente:\n{archivo}\n\nTotal: {total} clientes ({exitosos} exitosos, {errores} errores)")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte: {e}")
