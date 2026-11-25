import csv
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk
import serial
import serial.tools.list_ports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import metodos_numericos as mn

ctk.set_appearance_mode("dark")

# Paleta: cálidos (naranja, ámbar, carmesí) + azul eléctrico
COLOR_BG = "#12161E"
COLOR_PANEL = "#1B2230"
COLOR_AZUL = "#1E90FF"
COLOR_NARANJA = "#F3701E"
COLOR_AMBAR = "#FFB300"
COLOR_CARMESI = "#E63946"
COLOR_TEXTO = "#F1F5F9"
COLOR_GRIS = "#94A3B8"


class AppTelemetria(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Estación Telemétrica — Proyecto Integrador de Métodos Numéricos")
        self.geometry("1280x780")
        self.configure(fg_color=COLOR_BG)

        self.ser = None
        self.conectado = False
        self.hilo_serial = None

        self.datos_t = []
        self.datos_x = []
        self.ultimo_resumen = {}

        self._construir_interfaz()
        self.actualizar_puertos()
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    def _construir_interfaz(self):
        # ---------------- BARRA SUPERIOR ----------------
        top = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=10)
        top.pack(fill="x", padx=12, pady=(12, 6))

        ctk.CTkLabel(
            top, text="Puerto:", text_color=COLOR_TEXTO, font=("Segoe UI", 13, "bold")
        ).pack(side="left", padx=(12, 6), pady=10)

        self.combo_puertos = ctk.CTkComboBox(top, width=180, values=["Sin puertos"])
        self.combo_puertos.pack(side="left", padx=4, pady=10)

        ctk.CTkButton(
            top, text="↻", width=36, fg_color="#2A3447", hover_color="#3B4963",
            command=self.actualizar_puertos
        ).pack(side="left", padx=4, pady=10)

        self.btn_conectar = ctk.CTkButton(
            top, text="Conectar Arduino", width=140,
            fg_color=COLOR_AZUL, hover_color="#1470CC",
            command=self.alternar_conexion
        )
        self.btn_conectar.pack(side="left", padx=8, pady=10)

        self.btn_capturar = ctk.CTkButton(
            top, text="▶ Capturar Ráfaga (3 s)", width=180,
            fg_color=COLOR_NARANJA, hover_color="#D95B0E",
            state="disabled", command=self.iniciar_captura
        )
        self.btn_capturar.pack(side="left", padx=8, pady=10)

        self.lbl_vivo = ctk.CTkLabel(
            top, text="En vivo: --- cm", text_color=COLOR_AMBAR,
            font=("Consolas", 16, "bold")
        )
        self.lbl_vivo.pack(side="left", padx=18, pady=10)

        # Botones de archivo (CSV y PNG)
        ctk.CTkButton(
            top, text="Exportar PNG", width=110, fg_color="#2A3447",
            hover_color="#3B4963", command=self.exportar_png
        ).pack(side="right", padx=(4, 12), pady=10)

        ctk.CTkButton(
            top, text="Guardar CSV", width=105, fg_color="#2A3447",
            hover_color="#3B4963", command=self.guardar_csv
        ).pack(side="right", padx=4, pady=10)

        ctk.CTkButton(
            top, text="Cargar CSV", width=100, fg_color="#2A3447",
            hover_color="#3B4963", command=self.cargar_csv
        ).pack(side="right", padx=4, pady=10)

        # ---------------- CUERPO PRINCIPAL ----------------
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        # Panel izquierdo: Gráficas Matplotlib
        panel_graf = ctk.CTkFrame(cuerpo, fg_color=COLOR_PANEL, corner_radius=10)
        panel_graf.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        controles_graf = ctk.CTkFrame(panel_graf, fg_color="transparent")
        controles_graf.pack(fill="x", padx=12, pady=(8, 0))

        self.var_limitar_y = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            controles_graf,
            text="Acotar eje Y al rango del sensor (evita que Runge aplaste el Spline)",
            variable=self.var_limitar_y,
            fg_color=COLOR_NARANJA,
            command=self._redibujar_si_hay_datos
        ).pack(side="left")

        self.lbl_estado = ctk.CTkLabel(
            controles_graf, text="Estado: Desconectado", text_color=COLOR_GRIS
        )
        self.lbl_estado.pack(side="right")

        self.fig = Figure(figsize=(8.5, 6.2), dpi=100, facecolor=COLOR_PANEL)
        self.ax_pos = self.fig.add_subplot(211)
        self.ax_vel = self.fig.add_subplot(212)
        self._estilizar_ejes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=panel_graf)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        # Panel derecho: Resultados numéricos, error y tabla
        panel_der = ctk.CTkFrame(cuerpo, fg_color=COLOR_PANEL, corner_radius=10)
        panel_der.grid(row=0, column=1, sticky="nsew")

        # Campo de distancia real medida con regla
        ref_frame = ctk.CTkFrame(panel_der, fg_color="#232C3D", corner_radius=8)
        ref_frame.pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkLabel(
            ref_frame, text="Distancia real con regla (cm):",
            text_color=COLOR_TEXTO, font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=10, pady=(8, 2))

        fila_ref = ctk.CTkFrame(ref_frame, fg_color="transparent")
        fila_ref.pack(fill="x", padx=10, pady=(2, 8))

        self.entry_real = ctk.CTkEntry(
            fila_ref, placeholder_text="Ej. 20.0", width=130
        )
        self.entry_real.pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            fila_ref, text="Calcular Error", width=110,
            fg_color=COLOR_CARMESI, hover_color="#C12935",
            command=self._redibujar_si_hay_datos
        ).pack(side="left")

        # Pestañas: Resultados vs Tabla de datos
        tabs = ctk.CTkTabview(
            panel_der, fg_color="#161C27",
            segmented_button_selected_color=COLOR_AZUL,
            segmented_button_selected_hover_color="#1470CC"
        )
        tabs.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        tab_res = tabs.add("Resultados")
        tab_tab = tabs.add("Tabla (t, x, v, a)")

        self.txt_resultados = ctk.CTkTextbox(
            tab_res, font=("Consolas", 12), fg_color="#12161E", text_color=COLOR_TEXTO
        )
        self.txt_resultados.pack(fill="both", expand=True, padx=4, pady=4)
        self.txt_resultados.insert(
            "end",
            "Conecta el Arduino Uno o carga un archivo CSV\n"
            "para ejecutar:\n\n"
            "• Unidad 5: Newton vs. Splines Cúbicos\n"
            "• Unidad 4: Diferencias Finitas O(h²)\n"
            "• Unidad 4: Trapecio y Simpson 1/3\n"
            "• Análisis de Error Relativo Porcentual"
        )

        self.txt_tabla = ctk.CTkTextbox(
            tab_tab, font=("Consolas", 11), fg_color="#12161E", text_color=COLOR_TEXTO
        )
        self.txt_tabla.pack(fill="both", expand=True, padx=4, pady=4)

    def _estilizar_ejes(self):
        for ax in (self.ax_pos, self.ax_vel):
            ax.clear()
            ax.set_facecolor("#12161E")
            ax.tick_params(colors=COLOR_TEXTO, labelsize=9)
            ax.grid(True, linestyle="--", alpha=0.25, color=COLOR_GRIS)
            for spine in ax.spines.values():
                spine.set_color("#334155")

        self.ax_pos.set_title(
            "Unidad 5: Reconstrucción de Posición x(t) — Newton vs. Splines Cúbicos",
            color=COLOR_TEXTO, fontsize=10, fontweight="bold"
        )
        self.ax_pos.set_xlabel("Tiempo t (s)", color=COLOR_GRIS, fontsize=9)
        self.ax_pos.set_ylabel("Posición x (cm)", color=COLOR_GRIS, fontsize=9)

        self.ax_vel.set_title(
            "Unidad 4: Velocidad Instantánea v(t) por Diferencias Finitas O(h²)",
            color=COLOR_TEXTO, fontsize=10, fontweight="bold"
        )
        self.ax_vel.set_xlabel("Tiempo t (s)", color=COLOR_GRIS, fontsize=9)
        self.ax_vel.set_ylabel("Velocidad v (cm/s)", color=COLOR_GRIS, fontsize=9)
        self.fig.tight_layout(pad=2.0)

    # ---------------- CONEXIÓN SERIAL ----------------
    def actualizar_puertos(self):
        puertos = [p.device for p in serial.tools.list_ports.comports()]
        if puertos:
            self.combo_puertos.configure(values=puertos)
            self.combo_puertos.set(puertos[0])
        else:
            self.combo_puertos.configure(values=["Sin puertos"])
            self.combo_puertos.set("Sin puertos")

    def alternar_conexion(self):
        if not self.conectado:
            puerto = self.combo_puertos.get()
            if puerto == "Sin puertos":
                messagebox.showwarning("Sin puerto", "No se detectó ningún puerto serial.")
                return
            try:
                self.ser = serial.Serial(puerto, 115200, timeout=0.5)
                self.conectado = True
                self.btn_conectar.configure(
                    text="Desconectar", fg_color=COLOR_CARMESI, hover_color="#B91C1C"
                )
                self.lbl_estado.configure(
                    text=f"Estado: Inicializando {puerto}...", text_color=COLOR_AMBAR
                )
                self.hilo_serial = threading.Thread(target=self._leer_serial, daemon=True)
                self.hilo_serial.start()
                # El Arduino Uno se reinicia al abrir el puerto (~2 s)
                self.after(2200, self._habilitar_captura_post_boot)
            except Exception as e:
                messagebox.showerror("Error Serial", f"No se pudo abrir {puerto}:\n{e}")
        else:
            self._desconectar()

    def _habilitar_captura_post_boot(self):
        if self.conectado:
            self.btn_capturar.configure(state="normal")
            self.lbl_estado.configure(text="Estado: Listo para capturar", text_color=COLOR_AZUL)

    def _desconectar(self):
        self.conectado = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None
        self.btn_conectar.configure(
            text="Conectar Arduino", fg_color=COLOR_AZUL, hover_color="#1470CC"
        )
        self.btn_capturar.configure(state="disabled")
        self.lbl_estado.configure(text="Estado: Desconectado", text_color=COLOR_GRIS)
        self.lbl_vivo.configure(text="En vivo: --- cm")

    def iniciar_captura(self):
        if self.conectado and self.ser and self.ser.is_open:
            self.btn_capturar.configure(state="disabled")
            self.lbl_estado.configure(text="Estado: Capturando ráfaga...", text_color=COLOR_NARANJA)
            try:
                self.ser.write(b"S\n")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo enviar comando de captura:\n{e}")
                self.btn_capturar.configure(state="normal")

    def _leer_serial(self):
        capturando = False
        t_buf, x_buf = [], []

        while self.conectado and self.ser and self.ser.is_open:
            try:
                raw = self.ser.readline()
                if not raw:
                    continue
                linea = raw.decode("utf-8", errors="ignore").strip()
                if not linea:
                    continue

                if linea == "START":
                    capturando = True
                    t_buf, x_buf = [], []
                    self.after(0, lambda: self.lbl_estado.configure(
                        text="Estado: Capturando (0/13)...", text_color=COLOR_NARANJA
                    ))
                elif linea == "END" and capturando:
                    capturando = False
                    self.after(0, self._finalizar_captura, list(t_buf), list(x_buf))
                elif capturando and "," in linea:
                    partes = linea.split(",")
                    if len(partes) == 2:
                        t_val = float(partes[0])
                        x_val = float(partes[1])
                        t_buf.append(t_val)
                        x_buf.append(x_val)
                        cnt = len(t_buf)
                        self.after(0, lambda c=cnt, xv=x_val: (
                            self.lbl_estado.configure(text=f"Estado: Capturando ({c}/13)..."),
                            self.lbl_vivo.configure(text=f"En vivo: {xv:.1f} cm")
                        ))
                elif linea.startswith("LIVE,"):
                    val = float(linea.split(",")[1])
                    texto = f"En vivo: {val:.1f} cm" if val > 0 else "En vivo: --- cm"
                    self.after(0, lambda s=texto: self.lbl_vivo.configure(text=s))
            except Exception:
                continue

    def _finalizar_captura(self, t_list, x_list):
        if self.conectado:
            self.btn_capturar.configure(state="normal")
        if len(t_list) < 5:
            self.lbl_estado.configure(text="Estado: Captura incompleta", text_color=COLOR_CARMESI)
            return
        self.datos_t = t_list
        self.datos_x = x_list
        self.lbl_estado.configure(
            text=f"Estado: Captura completada ({len(t_list)} muestras)", text_color=COLOR_AZUL
        )
        self._procesar_y_graficar()

    # ---------------- CÁLCULO NUMÉRICO Y GRÁFICAS ----------------
    def _redibujar_si_hay_datos(self):
        if len(self.datos_t) >= 5:
            self._procesar_y_graficar()

    def _procesar_y_graficar(self):
        t = self.datos_t
        x = self.datos_x
        m = len(t)
        h = (t[-1] - t[0]) / (m - 1)

        # Unidad 5: Interpolación desde cero
        coef_newton = mn.coeficientes_newton(t, x)
        coef_spline = mn.splines_cubicos_naturales(t, x)

        # Malla fina de 241 puntos para visualizar Runge vs Splines
        pasos_finos = 240
        t_fino = [t[0] + i * (t[-1] - t[0]) / pasos_finos for i in range(pasos_finos + 1)]
        x_newton = [mn.evaluar_newton(t, coef_newton, ti) for ti in t_fino]
        x_spline = [mn.evaluar_spline(t, coef_spline, ti) for ti in t_fino]
        max_runge = max(abs(yn - ys) for yn, ys in zip(x_newton, x_spline))

        # Unidad 4: Diferenciación finita O(h^2)
        v = mn.diferenciacion_finita(x, h)
        a = mn.aceleracion_finita(x, h)
        v_abs = [abs(vi) for vi in v]

        # Unidad 4: Integración numérica (desplazamiento neto y distancia recorrida)
        desp_trap = mn.trapecio_compuesto(v, h)
        dist_trap = mn.trapecio_compuesto(v_abs, h)

        simpson_disponible = ((m - 1) % 2 == 0)
        if simpson_disponible:
            desp_simp = mn.simpson_13_compuesto(v, h)
            dist_simp = mn.simpson_13_compuesto(v_abs, h)
            err_trap_vs_simp = mn.error_relativo_porcentual(dist_simp, dist_trap)
        else:
            desp_simp = dist_simp = err_trap_vs_simp = None

        desp_directo = x[-1] - x[0]

        # Error contra distancia real medida con regla (si el usuario ingresó el dato)
        real_str = self.entry_real.get().strip().replace(",", ".")
        bloque_error_real = "  (Ingresa distancia real con regla para calcular)"
        if real_str:
            try:
                val_real = float(real_str)
                if val_real > 0:
                    err_real_trap = mn.error_relativo_porcentual(val_real, dist_trap)
                    lineas_err = [f"  • Trapecio vs Regla ({val_real:.2f} cm): {err_real_trap:.2f} %"]
                    if simpson_disponible:
                        err_real_simp = mn.error_relativo_porcentual(val_real, dist_simp)
                        lineas_err.append(
                            f"  • Simpson 1/3 vs Regla ({val_real:.2f} cm): {err_real_simp:.2f} %"
                        )
                    bloque_error_real = "\n".join(lineas_err)
            except ValueError:
                bloque_error_real = "  (Valor numérico inválido en distancia real)"

        # ---------------- ACTUALIZAR GRÁFICAS ----------------
        self._estilizar_ejes()

        # Gráfica 1: Posición x(t)
        self.ax_pos.plot(
            t_fino, x_newton, linestyle="--", linewidth=1.7, color=COLOR_NARANJA,
            label=f"Polinomio de Newton (grado {m - 1})"
        )
        self.ax_pos.plot(
            t_fino, x_spline, linewidth=2.3, color=COLOR_AZUL,
            label="Splines Cúbicos Naturales"
        )
        self.ax_pos.scatter(
            t, x, color=COLOR_AMBAR, edgecolor="#000000", s=45, zorder=5,
            label="Muestras HC-SR04"
        )
        if self.var_limitar_y.get():
            margen = max(3.0, (max(x) - min(x)) * 0.35)
            self.ax_pos.set_ylim(min(x) - margen, max(x) + margen)
        self.ax_pos.legend(
            loc="best", fontsize=8, facecolor="#1B2230", edgecolor="#334155", labelcolor=COLOR_TEXTO
        )

        # Gráfica 2: Velocidad v(t) y área integrada
        self.ax_vel.axhline(0, color=COLOR_GRIS, linewidth=0.9, linestyle=":")
        self.ax_vel.plot(
            t, v, marker="o", linewidth=2.0, color=COLOR_CARMESI, label="Velocidad v(t)"
        )
        self.ax_vel.fill_between(
            t, v, 0, color=COLOR_CARMESI, alpha=0.22, label="Área = ∫ v(t) dt"
        )
        self.ax_vel.legend(
            loc="best", fontsize=8, facecolor="#1B2230", edgecolor="#334155", labelcolor=COLOR_TEXTO
        )

        self.fig.tight_layout(pad=2.0)
        self.canvas.draw()

        # ---------------- ACTUALIZAR REPORTE NUMÉRICO ----------------
        v_max = max(v, key=abs)
        a_max = max(a, key=abs)

        resumen = (
            f"=== RESUMEN DE ADQUISICIÓN ===\n"
            f"  Muestras (N): {m}  |  Subintervalos (n): {m - 1}\n"
            f"  Paso uniforme (h): {h:.3f} s\n"
            f"  Rango x(t): [{min(x):.2f}, {max(x):.2f}] cm\n\n"
            f"=== UNIDAD 5: INTERPOLACIÓN ===\n"
            f"  Desviación máx. |Newton - Spline|\n"
            f"  (Fenómeno de Runge): {max_runge:.2f} cm\n\n"
            f"=== UNIDAD 4: DIFERENCIACIÓN O(h²) ===\n"
            f"  Velocidad pico:     {v_max:+.2f} cm/s\n"
            f"  Aceleración pico:   {a_max:+.2f} cm/s²\n\n"
            f"=== UNIDAD 4: INTEGRACIÓN NUMÉRICA ===\n"
            f"  Desplazamiento directo (x_n - x_0): {desp_directo:+.2f} cm\n"
            f"  Trapecio  ∫ v(t) dt  (neto):        {desp_trap:+.2f} cm\n"
            f"  Trapecio  ∫|v(t)|dt  (recorrida):   {dist_trap:.2f} cm\n"
        )
        if simpson_disponible:
            resumen += (
                f"  Simpson 1/3 ∫ v(t) dt (neto):       {desp_simp:+.2f} cm\n"
                f"  Simpson 1/3 ∫|v(t)|dt (recorrida):  {dist_simp:.2f} cm\n\n"
                f"=== ANÁLISIS DE ERROR RELATIVO ===\n"
                f"  • Trapecio vs Simpson 1/3: {err_trap_vs_simp:.2f} %\n"
                f"{bloque_error_real}\n"
            )
        else:
            resumen += (
                f"  Simpson 1/3: requiere N impar (n par).\n\n"
                f"=== ANÁLISIS DE ERROR RELATIVO ===\n"
                f"{bloque_error_real}\n"
            )

        self.txt_resultados.delete("1.0", "end")
        self.txt_resultados.insert("end", resumen)

        # ---------------- ACTUALIZAR TABLA DE DATOS ----------------
        encabezado = f"{'i':>2} | {'t(s)':>5} | {'x(cm)':>7} | {'v(cm/s)':>8} | {'a(cm/s²)':>9}\n"
        sep = "-" * 44 + "\n"
        filas = [
            f"{i:>2} | {t[i]:>5.2f} | {x[i]:>7.2f} | {v[i]:>+8.2f} | {a[i]:>+9.2f}"
            for i in range(m)
        ]
        self.txt_tabla.delete("1.0", "end")
        self.txt_tabla.insert("end", encabezado + sep + "\n".join(filas))

    # ---------------- ARCHIVOS CSV Y PNG ----------------
    def guardar_csv(self):
        if not self.datos_t:
            messagebox.showinfo("Sin datos", "Primero captura una ráfaga o carga un CSV.")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("Archivo CSV", "*.csv")]
        )
        if not ruta:
            return
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["t_s", "x_cm"])
            for ti, xi in zip(self.datos_t, self.datos_x):
                writer.writerow([f"{ti:.3f}", f"{xi:.3f}"])
        messagebox.showinfo("Guardado", f"Datos guardados en:\n{ruta}")

    def cargar_csv(self):
        ruta = filedialog.askopenfilename(filetypes=[("Archivo CSV", "*.csv")])
        if not ruta:
            return
        t_list, x_list = [], []
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for fila in reader:
                    if len(fila) >= 2:
                        try:
                            t_list.append(float(fila[0]))
                            x_list.append(float(fila[1]))
                        except ValueError:
                            continue
            if len(t_list) < 5:
                raise ValueError("El archivo necesita al menos 5 filas numéricas.")
            self.datos_t = t_list
            self.datos_x = x_list
            self.lbl_estado.configure(
                text=f"Estado: CSV cargado ({len(t_list)} muestras)", text_color=COLOR_AMBAR
            )
            self._procesar_y_graficar()
        except Exception as e:
            messagebox.showerror("Error al cargar CSV", str(e))

    def exportar_png(self):
        if not self.datos_t:
            messagebox.showinfo("Sin gráficas", "Primero genera una captura o carga un CSV.")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("Imagen PNG", "*.png")]
        )
        if not ruta:
            return
        self.fig.savefig(ruta, dpi=200, facecolor=self.fig.get_facecolor())
        messagebox.showinfo("Exportado", f"Gráficas guardadas en:\n{ruta}")

    def _al_cerrar(self):
        self._desconectar()
        self.destroy()


if __name__ == "__main__":
    app = AppTelemetria()
    app.mainloop()