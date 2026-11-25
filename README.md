# Estación Telemétrica de Cinemática 1D — Proyecto Integrador de Métodos Numéricos

Prototipo físico (IoT) y aplicación de escritorio en Python para la adquisición en tiempo real de datos discretos de posición $(t_i, x_i)$ mediante un **Arduino Uno**, un sensor ultrasónico **HC-SR04** y una pantalla **OLED 0.96" I2C**.

El software reconstruye la trayectoria continua y calcula magnitudes cinemáticas implementando **desde cero** (sin depender de librerías de caja negra como `scipy` o `numpy`) los métodos numéricos de la **Unidad 5 (Interpolación)** y la **Unidad 4 (Diferenciación e Integración Numérica)**.

## Tabla de Contenidos

 1. [Características Principales](#características-principales)

 2. [Estructura del Repositorio](#estructura-del-repositorio)

 3. [Hardware y Conexiones](#hardware-y-conexiones)

 4. [Requisitos Previos](#requisitos-previos)

 5. [Instalación Paso a Paso](#instalación-paso-a-paso)

 6. [Guía de Uso y Protocolo Experimental](#guía-de-uso-y-protocolo-experimental)

 7. [Fundamento Matemático Implementado](#fundamento-matemático-implementado)

 8. [Protocolo de Comunicación Serial](#protocolo-de-comunicación-serial)

 9. [Solución de Problemas Frecuentes](#solución-de-problemas-frecuentes)

10. [Bibliografía](#bibliografía)

11. [Equipo de Desarrollo](#equipo-de-desarrollo)

## Características Principales

* **Adquisición en tiempo real:** Captura $N = 13$ muestras discretas con un paso temporal uniforme $h = \Delta t = 0.25\text{ s}$ (duración total de $3.0\text{ s}$), garantizando $n = 12$ subintervalos pares para aplicar la Regla de Simpson $1/3$ compuesto sin ajustes en el último tramo.

* **Visualización dual:** Monitoreo instantáneo de la distancia en la pantalla OLED del hardware y en la interfaz gráfica de escritorio.

* **Algoritmos numéricos propios (`metodos_numericos.py`):**

  * **Unidad 5:** Polinomio de Interpolación de Newton (Diferencias Divididas + evaluación de Horner) y Splines Cúbicos Naturales (resueltos mediante el Algoritmo de Thomas).

  * **Unidad 4:** Diferencias Finitas de orden $O(h^2)$ para velocidad $v(t)$ y aceleración $a(t)$, Regla del Trapecio Compuesto y Regla de Simpson $1/3$ Compuesto.

* **Análisis visual e interactivo:** Comparativa gráfica directa del **Fenómeno de Runge** frente a la estabilidad de los Splines Cúbicos, con opción para acotar el eje $Y$.

* **Validación experimental:** Cálculo automático del error relativo porcentual comparando Trapecio vs. Simpson $1/3$ y las integrales contra la distancia real medida físicamente con una regla.

* **Exportación y respaldo:** Guardado/carga de corridas experimentales en formato `.csv` y exportación de gráficas en alta resolución (`.png`).

## Estructura del Repositorio

```
telemetria-metodos-numericos/
├── firmware/
│   └── telemetria_uno/
│       └── telemetria_uno.ino   # Código para Arduino Uno (HC-SR04 + OLED SSD1306)
├── metodos_numericos.py         # Algoritmos matemáticos programados desde cero
├── app_telemetria.py            # Interfaz gráfica (CustomTkinter + Matplotlib + PySerial)
├── datos_ejemplo/
│   └── corrida_respaldo.csv     # Datos experimentales de ejemplo para pruebas sin hardware
├── requirements.txt             # Dependencias de Python
└── README.md                    # Documentación del proyecto

```

## Hardware y Conexiones

### Lista de Materiales

* 1 Arduino Uno (con cable USB tipo A-B).

* 1 Sensor ultrasónico HC-SR04.

* 1 Pantalla OLED 0.96" I2C ($128 \times 64$, controlador SSD1306, dirección `0x3C`).

* Protoboard y cables jumper macho-macho / hembra-macho.

* Regla o cinta métrica y un objeto plano reflectante (caja o libreta).

### Tabla de Pinout (Arduino Uno)

Al trabajar el Arduino Uno con lógica nativa de $5\text{ V}$, el sensor HC-SR04 se conecta de forma directa sin requerir divisor de voltaje en el pin `ECHO`.

| Componente | Pin del Módulo | Pin en Arduino Uno | Observaciones | 
| ----- | ----- | ----- | ----- | 
| **HC-SR04** | `VCC` | `5V` | Alimentación directa desde USB | 
| **HC-SR04** | `GND` | `GND` | Tierra común | 
| **HC-SR04** | `TRIG` | Pin digital `5` | Señal de disparo | 
| **HC-SR04** | `ECHO` | Pin digital `6` | Conexión directa ($5\text{ V}$) | 
| **OLED 0.96" I2C** | `GND` | `GND` | Tierra común | 
| **OLED 0.96" I2C** | `VCC` | `3.3V` (o `5V`) | Verificar serigrafía del módulo (`3.3V-5V`) | 
| **OLED 0.96" I2C** | `SDA` | `A4` | Bus I2C estándar del Arduino Uno | 
| **OLED 0.96" I2C** | `SCL` | `A5` | Bus I2C estándar del Arduino Uno | 

### Diagrama Esquemático

```
+-------------------+                                +-------------------+
|    ARDUINO UNO    |                                |   SENSOR HC-SR04  |
|                   |                                |                   |
|               5V  +--------------------------------+ VCC (5V)          |
|            Pin 5  +--------------------------------+ TRIG              |
|            Pin 6  +--------------------------------+ ECHO              |
|              GND  +-------+------------------------+ GND               |
|                   |       |                        +-------------------+
|                   |       |
|                   |       |                        +-------------------+
|                   |       |                        |  OLED 0.96" I2C   |
|                   |       +------------------------+ GND               |
|             3.3V  +--------------------------------+ VCC               |
|               A4  +--------------------------------+ SDA               |
|               A5  +--------------------------------+ SCL               |
+-------------------+                                +-------------------+

```

## Requisitos Previos

* **Python:** Versión $3.9$ o superior.

* **Arduino IDE:** Versión $1.8.x$ o $2.x$.

* **Librerías de Arduino:**

  * `Adafruit SSD1306`

  * `Adafruit GFX Library` (y su dependencia `Adafruit BusIO`)

* **Librerías de Python:**

  * `customtkinter`

  * `matplotlib`

  * `pyserial`

## Instalación Paso a Paso

### 1. Clonar el repositorio

```
git clone https://github.com/TU_USUARIO/telemetria-metodos-numericos.git
cd telemetria-metodos-numericos

```

### 2. Cargar el firmware al Arduino Uno

1. Abre el archivo `firmware/telemetria_uno/telemetria_uno.ino` en **Arduino IDE**.

2. Ve al **Gestor de Bibliotecas** e instala **Adafruit SSD1306** (aceptando instalar todas sus dependencias).

3. Conecta el Arduino Uno por USB y selecciona:

   * **Herramientas > Placa:** `Arduino Uno`

   * **Herramientas > Puerto:** `COMx` (Windows) o `/dev/ttyACM0` / `/dev/ttyUSB0` (Linux).

4. Haz clic en **Subir (Upload)**. Al terminar, la pantalla OLED mostrará `TELEMETRIA MET. NUM.` y la distancia en vivo.

5. **Importante:** Cierra el Monitor Serie de Arduino IDE antes de iniciar la aplicación en Python para liberar el puerto serial.

### 3. Configurar permisos del puerto serial (solo Linux)

Si en Linux aparece `Permission denied` al acceder a `/dev/ttyACM0`, agrega tu usuario al grupo `dialout` y reinicia tu sesión:

```
sudo usermod -aG dialout $USER

```

### 4. Instalar dependencias de Python y ejecutar la app

Se recomienda usar un entorno virtual:

```
python3 -m venv venv
# En Linux / macOS:
source venv/bin/activate
# En Windows (PowerShell):
.\venv\Scripts\Activate.ps1

pip install customtkinter matplotlib pyserial
python3 app_telemetria.py

```

*(Opcionalmente, si agregas un archivo `requirements.txt` con esas tres librerías, basta con ejecutar `pip install -r requirements.txt`).*

## Guía de Uso y Protocolo Experimental

1. **Conexión:** Ejecuta `python3 app_telemetria.py`, selecciona el puerto serial de tu Arduino Uno y presiona **Conectar Arduino**. Espera $2\text{ s}$ a que la placa finalice su reinicio automático y verifica que el indicador `En vivo: xx.x cm` cambie al mover tu mano frente al sensor.

2. **Montaje físico:** Coloca una regla sobre la mesa alineada frente al HC-SR04 y posiciona un objeto plano en la marca inicial (por ejemplo, $10.0\text{ cm}$).

3. **Captura de ráfaga:** Haz clic en **Capturar Ráfaga (3 s)** y desliza suavemente el objeto hasta la marca final (por ejemplo, $30.0\text{ cm}$). Al completarse las $13$ muestras, las gráficas y la tabla `(t, x, v, a)` se actualizarán automáticamente.

4. **Comparativa de Runge vs. Splines:** Desmarca temporalmente la casilla *Acotar eje Y* para visualizar las oscilaciones de gran amplitud producidas por el polinomio global de Newton en los extremos del intervalo.

5. **Cálculo de error real:** Ingresa la distancia física desplazada según la regla (ej. `20.0`) en el panel derecho y haz clic en **Calcular Error** para cuantificar el error relativo porcentual de Trapecio y Simpson $1/3$.

6. **Respaldo y reportes:** Usa **Guardar CSV** para conservar los datos crudos, **Cargar CSV** para analizar corridas sin tener el Arduino conectado y **Exportar PNG** para guardar las gráficas en alta resolución.

## Fundamento Matemático Implementado

Todos los algoritmos residen en `metodos_numericos.py` implementados en Python puro:

### Unidad 5: Interpolación

* **Polinomio de Newton (grado** $n = 12$**):** Construye la tabla de diferencias divididas $f[t_0, \dots, t_k]$ y evalúa mediante el esquema de Horner:
  

  $$
  P_n(t) = f[t_0] + \sum_{k=1}^{n} f[t_0, \dots, t_k] \prod_{j=0}^{k-1} (t - t_j)
  $$

* **Splines Cúbicos Naturales:** Ajusta un polinomio cúbico $S_i(t) = a_i + b_i(t - t_i) + c_i(t - t_i)^2 + d_i(t - t_i)^3$ por cada subintervalo $[t_i, t_{i+1}]$ con continuidad $C^2$ y condiciones de frontera naturales $S''(t_0) = S''(t_n) = 0$, resolviendo el sistema lineal tridiagonal mediante el **Algoritmo de Thomas**.

### Unidad 4: Diferenciación Numérica

Con paso uniforme $h = 0.25\text{ s}$, la velocidad $v(t_i) = \frac{dx}{dt}\big\vert{}_{t_i}$ se calcula manteniendo precisión $O(h^2)$ en todo el dominio:

* **Frontera inicial (**$i = 0$**):** $v_0 \approx \frac{-3x_0 + 4x_1 - x_2}{2h}$

* **Nodos interiores (**$0 < i < n$**):** $v_i \approx \frac{x_{i+1} - x_{i-1}}{2h}$

* **Frontera final (**$i = n$**):** $v_n \approx \frac{3x_n - 4x_{n-1} + x_{n-2}}{2h}$

De forma análoga se calcula la aceleración instantánea $a(t_i) = \frac{d^2x}{dt^2}\big\vert{}_{t_i}$ con esquemas de $4$ puntos en fronteras y $3$ puntos centrados en el interior con orden $O(h^2)$.

### Unidad 4: Integración Numérica y Análisis de Error

Se evalúan tanto el desplazamiento neto $\Delta x = \int_{t_0}^{t_n} v(t)\,dt$ como la distancia total recorrida $D = \int_{t_0}^{t_n} \vert{}v(t)\vert{}\,dt$ mediante:

* **Regla del Trapecio Compuesto** (error global $O(h^2)$):
  

  $$
  I_T = \frac{h}{2}\left[f(t_0) + 2\sum_{i=1}^{n-1} f(t_i) + f(t_n)\right]
  $$

* **Regla de Simpson** $1/3$ **Compuesto** (error global $O(h^4)$, requiere $n$ par):
  

  $$
  I_S = \frac{h}{3}\left[f(t_0) + 4\sum_{i=1,3,\dots}^{n-1} f(t_i) + 2\sum_{i=2,4,\dots}^{n-2} f(t_i) + f(t_n)\right]
  $$

* **Error Relativo Porcentual:**
  

  $$
  E_r = \left\vert{}\frac{V_{\text{real}} - V_{\text{aprox}}}{V_{\text{real}}}\right\vert{} \times 100\%
  $$

## Protocolo de Comunicación Serial

Configuración UART: `115200 baudios`, `8N1`.

* **PC** $\rightarrow$ **Arduino:** Enviar el carácter `S` (o `s`) inicia la captura de una ráfaga de $13$ muestras.

* **Arduino** $\rightarrow$ **PC (en espera):** Envía lecturas continuas cada $150\text{ ms}$ en el formato `LIVE,<distancia_cm>`.

* **Arduino** $\rightarrow$ **PC (durante ráfaga):** Envía un bloque delimitado:

```
START
0.000,10.120
0.250,11.850
...
3.000,30.040
END

```

## Solución de Problemas Frecuentes

| Síntoma | Causa probable | Solución | 
| ----- | ----- | ----- | 
| Error `Port is busy` al conectar en Python | El Monitor Serie de Arduino IDE sigue abierto | Cierra el Monitor Serie en Arduino IDE y reconecta | 
| `Permission denied` en Linux (`/dev/ttyACM0`) | El usuario no pertenece al grupo `dialout` | Ejecuta `sudo usermod -aG dialout $USER` y reinicia sesión | 
| La OLED muestra `--- cm` constantemente | Objeto fuera de rango ($< 2\text{ cm}$ o $> 400\text{ cm}$) o cable `TRIG`/`ECHO` flojo | Verifica pines `5` y `6`, alimentación de $5\text{ V}$ y coloca una superficie plana a $15\text{ cm}$ | 
| La OLED no enciende | Dirección I2C diferente o `SDA`/`SCL` invertidos | Confirma `A4` (`SDA`) y `A5` (`SCL`), o cambia `0x3C` por `0x3D` en el sketch | 

## Bibliografía

1. Chapra, S. C., & Canale, R. P. (2015). *Métodos numéricos para ingenieros* (7.ª ed.). McGraw-Hill Education.

2. Burden, R. L., Faires, J. D., & Burden, A. M. (2017). *Análisis numérico* (10.ª ed.). Cengage Learning.

3. Nieves Hurtado, A., & Domínguez Sánchez, F. C. (2014). *Métodos numéricos aplicados a la ingeniería* (4.ª ed.). Grupo Editorial Patria.

## Equipo de Desarrollo

Proyecto Integrador desarrollado para la asignatura de **Métodos Numéricos**.

* **Integrante 1:** *\[Giovan Stefano Trujillo Nieto\]*

* **Integrante 2:** *\[Leonardo Romero Ramirez\]*

* **Integrante 3:** *\[Juan Alberto Gonzalez Rivera\]*
