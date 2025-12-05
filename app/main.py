import sys
import os
import datetime
import json
import shutil
import customtkinter as ctk
from tkinter import messagebox
import billetera, transaccion, verificador


ctk.set_appearance_mode("dark") 
ctk.set_default_color_theme("blue")  
ARCHIVO_REGISTROS="crypto_wallet_logs.txt"

class AppBilleteraCrypto:
    def __init__(self):
        self.direccion_actual=None
        self.app = ctk.CTk()
        self.app.title("Billetera-Crypto Almacenamiento Frío - GUI Completa")
        self.app.geometry("950x720")
        
        # Barra lateral 
        self.barra_lateral=ctk.CTkFrame(self.app,width=220,corner_radius=10)
        self.barra_lateral.pack(side="left", fill="y", padx=10, pady=10)
        ctk.CTkLabel(self.barra_lateral, text="Billetera-Crypto", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        self.etiqueta_estado = ctk.CTkLabel(self.barra_lateral, text="Sin billetera cargada", font=ctk.CTkFont(size=12))
        self.etiqueta_estado.pack(pady=10)
        ctk.CTkLabel(self.barra_lateral, text=f"Registros: {os.path.abspath(ARCHIVO_REGISTROS)}", 
                    font=ctk.CTkFont(size=9), text_color="gray").pack(pady=5)

        # Botones principales
        ctk.CTkButton(self.barra_lateral, text="1. Crear billetera", command=self.opcion1, width=200).pack(pady=15, padx=20)
        ctk.CTkButton(self.barra_lateral, text="2. Cargar billetera", command=self.opcion2, width=200).pack(pady=15, padx=20)
        ctk.CTkButton(self.barra_lateral, text="3. Enviar TX (auto-copia)", command=self.enviar_tx_auto, 
                     width=200, fg_color="#1f6aa5", hover_color="#144870").pack(pady=15, padx=20)
        ctk.CTkButton(self.barra_lateral, text="4. Procesar bandeja", command=self.opcion4, width=200).pack(pady=15, padx=20)
        
        # BOTÓN VER LOGS
        ctk.CTkButton(self.barra_lateral, text="Ver Registros", command=self.ver_registros, 
                     width=200, fg_color="#2191ba", hover_color="#15566d").pack(pady=15, padx=20)

        ctk.CTkButton(self.barra_lateral, text="Salir", command=self.app.destroy, 
                     width=200, fg_color="red", hover_color="#910A0A").pack(pady=30, padx=20)

        # Principal con pestañas
        area_principal=ctk.CTkFrame(self.app)
        area_principal.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.vista_pestanas=ctk.CTkTabview(area_principal)
        self.vista_pestanas.pack(fill="both", expand=True, pady=10)
        self.vista_pestanas.add("Salida")
        self.vista_pestanas.add("Entrada")
        self.vista_pestanas.add("Verificados")
        self.marcos = {}
        for pestana in ["Salida", "Entrada", "Verificados"]:
            marco = ctk.CTkScrollableFrame(self.vista_pestanas.tab(pestana))
            marco.pack(fill="both", expand=True, padx=10, pady=10)
            self.marcos[pestana.lower()] = marco
        self.refrescar_carpetas()
        self.agregar_registro("Aplicación iniciada")
    
    def agregar_registro(self, texto):
        linea=f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {texto}\n"
        with open(ARCHIVO_REGISTROS, "a",encoding="utf-8") as f:
            f.write(linea)

    def ver_registros(self):
        "Abre el archivo de registros con el editor predeterminado"
        if not os.path.exists(ARCHIVO_REGISTROS):
            messagebox.showinfo("Registros","Aún no hay registros generados.")
            return
        try:
            os.startfile(os.path.abspath(ARCHIVO_REGISTROS))  
        except:
            subprocess.Popen(["notepad", os.path.abspath(ARCHIVO_REGISTROS)])

    def refrescar_carpetas(self):
        # Mapeo de carpetas físicas a pestañas lógicas
        carpetas={"outbox": "Salida", "inbox": "Entrada", "verified": "Verificados"}
        for carpeta,nombre_pestana in carpetas.items():
            ruta=carpeta
            if not os.path.exists(ruta):
                os.makedirs(ruta)
            marco=self.marcos[nombre_pestana.lower()]
            for widget in marco.winfo_children():
                widget.destroy()
            archivos=[a for a in os.listdir(ruta) if a.endswith(".json")]
            if not archivos:
                ctk.CTkLabel(marco, text="Carpeta vacía", text_color="gray").pack(pady=20)
            else:
                for archivo in sorted(archivos):
                    ruta_archivo = os.path.join(ruta, archivo)
                    estadisticas=os.stat(ruta_archivo)
                    tamano= f"{estadisticas.st_size:,} B"
                    fecha_mod=datetime.datetime.fromtimestamp(estadisticas.st_mtime).strftime("%Y-%m-%d %H:%M")
                    ctk.CTkLabel(marco, text=f"{archivo}  |  {tamano}  |  {fecha_mod}", 
                                anchor="w",font=ctk.CTkFont(size=11)).pack(fill="x", padx=15, pady=2)

    ## def actualizar_estado
    def actualizar_estado(self, direccion=None):
        if direccion:
            self.direccion_actual=direccion
            self.etiqueta_estado.configure(text=f"Dirección: {direccion[:10]}...",text_color="#00ff00")
        else:
            self.direccion_actual=None
            self.etiqueta_estado.configure(text="Sin billetera cargada", text_color="white")
    
    def opcion1(self): ###
        dialogo=ctk.CTkInputDialog(text="Define una contraseña segura:", title="Crear Billetera")
        contra=dialogo.get_input()
        if not contra: return
        resultado=billetera.crear_billetera(contra)
        if resultado["exito"]:
            self.agregar_registro(f"Billetera creada: {resultado['direccion']}")
            self.actualizar_estado(resultado["direccion"])
            messagebox.showinfo("Exito", "Billetera creada correctamente")
        else:
            messagebox.showerror("Error", resultado["error"])
    
    def opcion2(self): ###
        dialogo=ctk.CTkInputDialog(text="Ingresa tu contraseña:", title="Cargar Billetera")
        contra=dialogo.get_input()
        if not contra: return
        llave, resultado=billetera.cargar_billetera(contra)
        if resultado["exito"]:
            self.agregar_registro(f"Billetera cargada: {resultado['direccion']}")
            self.actualizar_estado(resultado["direccion"])
            messagebox.showinfo("Éxito", "Billetera cargada")
        else:
            messagebox.showerror("Error", resultado["error"])
    
    #### def enviar_tx_auto
    def enviar_tx_auto(self):
        if not self.direccion_actual:
            messagebox.showerror("Error", "No hay billetera cargada")
            return

    
    def opcion4(self):
        resultado = verificador.procesar_inbox()
        if resultado["exito"]:
            self.agregar_registro(f"Bandeja procesada: {resultado['validos']} válidos, {resultado['invalidos']} rechazados")
            messagebox.showinfo("Éxito", resultado["mensaje"])
        else:
            messagebox.showerror("Error", resultado["error"])
        self.refrescar_carpetas()
    
    def ejecutar(self):
        self.app.mainloop()

if __name__ == "__main__":
    app = AppBilleteraCrypto()
    app.ejecutar()
