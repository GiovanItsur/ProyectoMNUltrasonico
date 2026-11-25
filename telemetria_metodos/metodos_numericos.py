"""
Algoritmos de Métodos Numéricos programados desde cero (sin librerías de caja negra):
- Unidad 5: Polinomio de Newton (Diferencias Divididas) y Splines Cúbicos Naturales.
- Unidad 4: Diferencias Finitas O(h^2) (1a y 2a derivada), Trapecio Compuesto y Simpson 1/3 Compuesto.
"""

# =========================================================
# UNIDAD 5: INTERPOLACIÓN
# =========================================================

def coeficientes_newton(x, y):
    """Calcula los coeficientes del polinomio interpolante de Newton."""
    n = len(x)
    coef = [float(val) for val in y]
    for j in range(1, n):
        for i in range(n - 1, j - 1, -1):
            coef[i] = (coef[i] - coef[i - 1]) / (x[i] - x[i - j])
    return coef


def evaluar_newton(x_nodos, coef, t):
    """Evalúa el polinomio de Newton en un valor t usando el esquema de Horner."""
    n = len(coef)
    resultado = coef[n - 1]
    for k in range(n - 2, -1, -1):
        resultado = resultado * (t - x_nodos[k]) + coef[k]
    return resultado


def splines_cubicos_naturales(x, y):
    """
    Calcula los coeficientes (a, b, c, d) de los splines cúbicos naturales
    resolviendo el sistema tridiagonal mediante el algoritmo de Thomas.
    S_i(t) = a_i + b_i(t - x_i) + c_i(t - x_i)^2 + d_i(t - x_i)^3
    """
    n = len(x) - 1
    h = [x[i + 1] - x[i] for i in range(n)]

    alpha = [0.0] * (n + 1)
    for i in range(1, n):
        alpha[i] = (3.0 / h[i]) * (y[i + 1] - y[i]) - (3.0 / h[i - 1]) * (y[i] - y[i - 1])

    # Eliminación hacia adelante (sistema tridiagonal)
    l = [1.0] + [0.0] * n
    mu = [0.0] * (n + 1)
    z = [0.0] * (n + 1)

    for i in range(1, n):
        l[i] = 2.0 * (x[i + 1] - x[i - 1]) - h[i - 1] * mu[i - 1]
        mu[i] = h[i] / l[i]
        z[i] = (alpha[i] - h[i - 1] * z[i - 1]) / l[i]

    l[n] = 1.0
    c = [0.0] * (n + 1)
    b = [0.0] * n
    d = [0.0] * n
    a = [float(y[i]) for i in range(n)]

    # Sustitución hacia atrás
    for j in range(n - 1, -1, -1):
        c[j] = z[j] - mu[j] * c[j + 1]
        b[j] = (y[j + 1] - y[j]) / h[j] - h[j] * (c[j + 1] + 2.0 * c[j]) / 3.0
        d[j] = (c[j + 1] - c[j]) / (3.0 * h[j])

    return a, b, c[:-1], d


def evaluar_spline(x_nodos, coeffs, t):
    """Evalúa el spline cúbico natural en un punto t dentro de [x_0, x_n]."""
    a, b, c, d = coeffs
    n = len(a)
    idx = n - 1
    for i in range(n):
        if x_nodos[i] <= t <= x_nodos[i + 1]:
            idx = i
            break
    dx = t - x_nodos[idx]
    return a[idx] + b[idx] * dx + c[idx] * (dx ** 2) + d[idx] * (dx ** 3)


# =========================================================
# UNIDAD 4: DIFERENCIACIÓN E INTEGRACIÓN NUMÉRICA
# =========================================================

def diferenciacion_finita(y, h):
    """
    Primera derivada dy/dt con precisión O(h^2):
    - Adelante de 3 puntos en i = 0
    - Centrada en nodos interiores
    - Atrás de 3 puntos en i = n
    """
    m = len(y)
    if m < 3:
        raise ValueError("Se requieren al menos 3 puntos para diferencias O(h^2).")
    dy = [0.0] * m
    dy[0] = (-3.0 * y[0] + 4.0 * y[1] - y[2]) / (2.0 * h)
    for i in range(1, m - 1):
        dy[i] = (y[i + 1] - y[i - 1]) / (2.0 * h)
    dy[m - 1] = (3.0 * y[m - 1] - 4.0 * y[m - 2] + y[m - 3]) / (2.0 * h)
    return dy


def aceleracion_finita(y, h):
    """
    Segunda derivada d^2y/dt^2 con precisión O(h^2):
    - Adelante de 4 puntos en i = 0
    - Centrada de 3 puntos en nodos interiores
    - Atrás de 4 puntos en i = n
    """
    m = len(y)
    if m < 4:
        raise ValueError("Se requieren al menos 4 puntos para segunda derivada O(h^2).")
    d2y = [0.0] * m
    h2 = h * h
    d2y[0] = (2.0 * y[0] - 5.0 * y[1] + 4.0 * y[2] - y[3]) / h2
    for i in range(1, m - 1):
        d2y[i] = (y[i + 1] - 2.0 * y[i] + y[i - 1]) / h2
    d2y[m - 1] = (2.0 * y[m - 1] - 5.0 * y[m - 2] + 4.0 * y[m - 3] - y[m - 4]) / h2
    return d2y


def trapecio_compuesto(y, h):
    """Integración numérica mediante la Regla del Trapecio Compuesto."""
    n = len(y) - 1
    suma_interna = sum(y[1:n])
    return (h / 2.0) * (y[0] + 2.0 * suma_interna + y[n])


def simpson_13_compuesto(y, h):
    """Integración numérica mediante la Regla de Simpson 1/3 Compuesto (n par)."""
    n = len(y) - 1
    if n < 2 or n % 2 != 0:
        raise ValueError("Simpson 1/3 requiere un número par de subintervalos (N impar).")
    suma_impares = sum(y[i] for i in range(1, n, 2))
    suma_pares = sum(y[i] for i in range(2, n, 2))
    return (h / 3.0) * (y[0] + 4.0 * suma_impares + 2.0 * suma_pares + y[n])


def error_relativo_porcentual(valor_ref, valor_aprox):
    """Calcula el error relativo porcentual |ref - aprox| / |ref| * 100."""
    if abs(valor_ref) < 1e-12:
        return 0.0
    return abs((valor_ref - valor_aprox) / valor_ref) * 100.0