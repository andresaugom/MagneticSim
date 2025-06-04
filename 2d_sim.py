import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Parámetros físicos
mu_0 = 4 * np.pi * 1e-7  # Permeabilidad magnética del vacío
N = 1                    # Número de vueltas de la espira
A = 1e-4                 # Área de la espira (m^2)
v = 0.02                 # Velocidad del imán (m/s)
m = 1                   # Momento magnético del imán (arbitrario)
coil_position = 0.5      # Posición fija de la espira en eje x

# Tiempo
dt = 0.05
t_max = 10
frames = int(t_max / dt)

# Estado inicial del imán
x0 = -0.5  # Posición inicial del imán

# Función del campo B (modelo dipolar simplificado en eje x)
def B_field(x):
    r = coil_position - x
    return mu_0 * m / (2 * np.pi * (r**3 + 1e-9))  # Evita división por cero

# Inicializar arrays
x_vals = []
flux_vals = []
emf_vals = []

# Inicializar gráfico
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
line_flux, = ax1.plot([], [], lw=2, label='Flujo magnético (Wb)')
line_emf, = ax2.plot([], [], lw=2, color='r', label='fem inducida (V)')
dot, = ax1.plot([], [], 'ko', label='Imán')
arrow = ax1.arrow(coil_position, 0, 0, 0, head_width=0.02, head_length=0.02, color='g')

ax1.set_xlim(-1, 1)
ax1.set_ylim(-1e-6, 1e-6)
ax1.set_ylabel("Flujo magnético (Wb)")
ax1.legend()

ax2.set_xlim(0, t_max)
ax2.set_ylim(-1e-6, 1e-6)
ax2.set_xlabel("Tiempo (s)")
ax2.set_ylabel("fem inducida (V)")
ax2.legend()

def init():
    line_flux.set_data([], [])
    line_emf.set_data([], [])
    dot.set_data([], [])
    return line_flux, line_emf, dot

def update(frame):
    t = frame * dt
    x = x0 + v * t
    B = B_field(x)
    flux = N * A * B

    x_vals.append(t)
    flux_vals.append(flux)

    if frame == 0:
        emf = 0
    else:
        emf = -(flux_vals[-1] - flux_vals[-2]) / dt  # dΦ/dt con signo negativo (Ley de Lenz)
    emf_vals.append(emf)

    line_flux.set_data(x_vals, flux_vals)
    line_emf.set_data(x_vals, emf_vals)
    dot.set_data([x], [B])

    # Actualizar flecha de corriente inducida (sentido cualitativo)
    ax1.patches.clear()
    arrow_dir = np.sign(emf)
    arrow = ax1.arrow(coil_position, 0, 0, arrow_dir * 0.5e-6, head_width=0.02, head_length=1e-7, color='g')

    return line_flux, line_emf, dot, arrow

ani = FuncAnimation(fig, update, frames=frames, init_func=init, blit=False, interval=50)
plt.tight_layout()
plt.show()
