# %%
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib.animation as animation # Para la animación, si la queremos visual
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec

# %%
# --- Parámetros del sistema ---
coils_number = 3             # Número de espiras
coils_step = 0.1               # Distancia entre espiras (en z)
coils_radius = 1             # Radio de cada espira
coils_points = 1000           # Puntos por espira (resolución)

i = 300                     # Corriente en Amperes (Esto es para el campo de la bobina, el imán es aparte)
mu_0 = 4 * np.pi * 1e-7     # Permeabilidad del vacío
km_biot_savart = mu_0 * i / (4 * np.pi) # Constante de Biot-Savart para la bobina

# --- Parámetros del Imán ---
magnet_magnetic_moment = [0, 0, -50] # Vector de momento magnético del imán (Am^2)
                                   # [0, 0, -mu_z] para Polo Norte abajo, Sur arriba (mu apunta de S a N)
                                   # Ajusta este valor para cambiar la fuerza del imán.
magnet_speed = 0.05                # Velocidad del imán a lo largo del eje Z (unidades/frame)
magnet_initial_z = 4.0             # Posición Z inicial del imán
magnet_final_z = -4.0              # Posición Z final del imán
magnet_current_z = magnet_initial_z # Posición Z actual del imán

# %%
# --- Geometría de las espiras ---
thetas = np.linspace(0, 2*np.pi, coils_points, endpoint=False)

# Posiciones (en plano XY)
coil_pos_x = coils_radius * np.cos(thetas)
coil_pos_y = coils_radius * np.sin(thetas)
coil_pos_z_single = np.zeros_like(coil_pos_x)  # Espira plana en z = 0

# Diferenciales dl (entre puntos consecutivos)
dl_x = np.diff(coil_pos_x, append=coil_pos_x[0])
dl_y = np.diff(coil_pos_y, append=coil_pos_y[0])
dl_z = np.zeros_like(dl_x)

all_segment_origins = []
all_dl_vectors = []
all_coil_z_positions = [] # Para almacenar las posiciones Z reales de cada espira

for k in range(coils_number):
    z_pos = k * coils_step # Empezando desde z=0 para la primera espira
    
    # Posiciones de origen de cada segmento en esta espira
    origin_x = coil_pos_x
    origin_y = coil_pos_y
    origin_z = np.full_like(coil_pos_x, z_pos)
    
    segment_origins = np.stack([origin_x, origin_y, origin_z], axis=1)
    dl_vectors_coil = np.stack([dl_x, dl_y, dl_z], axis=1) # dl para esta espira
    
    all_segment_origins.append(segment_origins)
    all_dl_vectors.append(dl_vectors_coil)
    all_coil_z_positions.append(z_pos)

# Concatenar todos los segmentos y diferenciales de las espiras
r_primes_coil = np.concatenate(all_segment_origins, axis=0)
dl_vectors_coil = np.concatenate(all_dl_vectors, axis=0)

# Calcular el centro promedio de las espiras para el punto de interés
coil_center_x = np.mean(r_primes_coil[:,0])
coil_center_y = np.mean(r_primes_coil[:,1])
coil_center_z = np.mean(all_coil_z_positions) # Centro Z de la pila de espiras

# --- Función para calcular el campo magnético de un dipolo puntual (imán) ---
def magnetic_field_from_dipole(r_point, r_dipole, m_dipole):
    """
    Calcula el campo magnético B en un punto r_point debido a un dipolo
    magnético puntual con momento m_dipole ubicado en r_dipole.
    Fórmula: B(r) = (mu_0 / 4*pi) * [ (3*r_hat*(m . r_hat)) - m ] / r^3
    Donde r = r_point - r_dipole, r_hat = r / |r|, y m es el momento dipolar.
    """
    r_vec = r_point - r_dipole
    r_mag = np.linalg.norm(r_vec)

    if r_mag == 0: # Evitar división por cero si el punto está exactamente en el dipolo
        return np.array([0.0, 0.0, 0.0])

    r_hat = r_vec / r_mag
    
    # Producto punto de m y r_hat
    m_dot_r_hat = np.dot(m_dipole, r_hat)
    
    # Término [ (3*r_hat*(m . r_hat)) - m ]
    term = 3 * r_hat * m_dot_r_hat - m_dipole
    
    B = (mu_0 / (4 * np.pi)) * term / (r_mag**3)
    return B

# --- Función para calcular el campo magnético de la bobina en un punto (Biot-Savart) ---
def magnetic_field_from_coil_at_point(r_point, r_primes, dl_vectors, km):
    """
    Calcula el campo magnético en un único punto r_point debido a la bobina
    usando la ley de Biot-Savart.
    """
    r_vector = r_point - r_primes
    r_norm = np.linalg.norm(r_vector, axis=-1)
    r_norm3 = np.where(r_norm == 0, np.inf, r_norm**3) # Evitar división por cero

    dB_contributions = km * (np.cross(dl_vectors, r_vector) / r_norm3[:, np.newaxis])
    B_total = np.sum(dB_contributions, axis=0)
    return B_total

# --- Preparación para la simulación de movimiento ---
center_point = np.array([coil_center_x, coil_center_y, coil_center_z])

# Listas para almacenar los resultados del campo en el centro
magnet_z_positions = []
B_magnitude_at_center = []
B_coil_at_center = magnetic_field_from_coil_at_point(center_point, r_primes_coil, dl_vectors_coil, km_biot_savart)
B_coil_magnitude_at_center = np.linalg.norm(B_coil_at_center)


# --- Configuración de la figura para la animación ---
fig = plt.figure(figsize=(14, 8))
gs = GridSpec(1, 2, width_ratios=[2, 1]) # 2/3 para el 3D, 1/3 para el gráfico de B vs Z

ax_3d = fig.add_subplot(gs[0, 0], projection='3d')
ax_plot = fig.add_subplot(gs[0, 1])

# Dibujar las espiras en 3D
for k in range(coils_number):
    z_pos = k * coils_step
    ax_3d.plot(coil_pos_x, coil_pos_y, np.full_like(coil_pos_x, z_pos), color='blue', linewidth=2)
ax_3d.set_xlabel('X')
ax_3d.set_ylabel('Y')
ax_3d.set_zlabel('Z')
ax_3d.set_title('Simulación 3D: Imán atravesando la Bobina')
ax_3d.set_xlim([-1.5, 1.5])
ax_3d.set_ylim([-1.5, 1.5])
ax_3d.set_zlim([-4.5, 4.5]) # Ajustar límites Z para la trayectoria del imán

# Representación del imán (usando un pequeño cilindro o un rectángulo 3D para simplificar)
magnet_patch_3d, = ax_3d.plot([], [], [], 'o', color='red', markersize=10, label='Imán')
magnet_poles_text = []
magnet_poles_text.append(ax_3d.text2D(0, 0, '', transform=ax_3d.transAxes, color='white')) # Norte
magnet_poles_text.append(ax_3d.text2D(0, 0, '', transform=ax_3d.transAxes, color='black')) # Sur

# Graficar el punto central de la bobina
ax_3d.plot([center_point[0]], [center_point[1]], [center_point[2]], 'x', color='purple', markersize=8, label='Centro de Bobina')
ax_3d.legend()

# Configurar el gráfico de campo magnético
line_B_mag, = ax_plot.plot([], [], 'r-', linewidth=2)
ax_plot.set_xlabel('Posición Z del Imán')
ax_plot.set_ylabel('Magnitud de B en el Centro (T)')
ax_plot.set_title('Magnitud de B en el Centro de la Bobina')
ax_plot.grid(True, linestyle='--', alpha=0.7)
ax_plot.set_xlim([magnet_final_z - 0.5, magnet_initial_z + 0.5])
ax_plot.set_ylim([0, B_coil_magnitude_at_center * 2]) # Un límite inicial aproximado

# Leyenda para el valor actual del campo en el gráfico 3D
B_mag_text = ax_3d.text2D(0.05, 0.95, '', transform=ax_3d.transAxes, fontsize=10, color='red')
B_coil_text = ax_3d.text2D(0.05, 0.90, f'B Bobina: {B_coil_magnitude_at_center:.2e} T', transform=ax_3d.transAxes, fontsize=10, color='blue')


# --- Función de inicialización para la animación ---
def init():
    magnet_patch_3d.set_data([], [])
    magnet_patch_3d.set_3d_properties([])
    for text in magnet_poles_text:
        text.set_text('')
    line_B_mag.set_data([], [])
    B_mag_text.set_text('')
    return [magnet_patch_3d, line_B_mag, B_mag_text] + magnet_poles_text

# --- Función de animación ---
def animate(frame):
    global magnet_current_z

    # Mover el imán
    magnet_current_z -= magnet_speed
    if magnet_current_z < magnet_final_z:
        magnet_current_z = magnet_initial_z # Reiniciar la animación

    magnet_pos = np.array([coil_center_x, coil_center_y, magnet_current_z])
    magnet_patch_3d.set_data([magnet_pos[0]], [magnet_pos[1]])
    magnet_patch_3d.set_3d_properties([magnet_pos[2]])

    # Actualizar la posición de los textos de los polos
    # Esto es complicado en 3D, requiere convertir coordenadas 3D a 2D de la pantalla
    # Para simplificar, los textos se mantendrán fijos en el imán pero su renderizado en 3D es el desafío
    # Vamos a estimar una posición relativa en el plano XY de la pantalla
    
    # Para la visualización de los polos, podemos dibujar dos puntos.
    # Polo Norte (abajo):
    north_pole_pos = magnet_pos + np.array([0, 0, magnet_magnetic_moment[2]/np.linalg.norm(magnet_magnetic_moment) * 0.1]) # Pequeño desplazamiento en Z
    # Polo Sur (arriba):
    south_pole_pos = magnet_pos - np.array([0, 0, magnet_magnetic_moment[2]/np.linalg.norm(magnet_magnetic_moment) * 0.1])
    
    # Actualizar la posición de los textos de los polos en el imán
    # Es más sencillo dibujar dos puntos de colores diferentes para los polos
    # Redibujar el imán como un segmento y puntos de colores
    magnet_patch_3d.set_data_3d([magnet_pos[0]], [magnet_pos[1]], [magnet_pos[2]]) # Solo el centro del imán como marcador
    
    # Calcular el campo magnético del imán en el centro de la bobina
    B_magnet_at_center = magnetic_field_from_dipole(center_point, magnet_pos, magnet_magnetic_moment)
    
    # Calcular el campo magnético total (bobina + imán)
    # B_total = B_coil_at_center + B_magnet_at_center
    # La pregunta pide "como varia la magnitud del campo en el centro a medida que el iman se acerca y aleja?"
    # Esto implica el campo del imán, ya que el campo de la bobina es constante.
    # Si quisieras el campo total, sumarías B_coil_at_center.
    # Por ahora, nos enfocamos en el campo del imán, que es lo que varía.
    B_magnitude_current = np.linalg.norm(B_magnet_at_center)
    
    magnet_z_positions.append(magnet_current_z)
    B_magnitude_at_center.append(B_magnitude_current)
    
    # Actualizar el gráfico de campo magnético vs Z
    line_B_mag.set_data(magnet_z_positions, B_magnitude_at_center)
    
    # Ajustar dinámicamente los límites del eje Y del gráfico de B si es necesario
    min_b = min(B_magnitude_at_center) if B_magnitude_at_center else 0
    max_b = max(B_magnitude_at_center) if B_magnitude_at_center else 0
    ax_plot.set_ylim([min(0, min_b), max_b * 1.1 + B_coil_magnitude_at_center]) # Un poco de margen superior
    ax_plot.set_xlim([magnet_final_z - 0.5, magnet_initial_z + 0.5]) # Asegurar límites correctos

    B_mag_text.set_text(f'B Imán en Centro: {B_magnitude_current:.2e} T')
    
    return [magnet_patch_3d, line_B_mag, B_mag_text] + magnet_poles_text

# --- Crear la animación ---
ani = animation.FuncAnimation(fig, animate, frames=np.arange(0, (magnet_initial_z - magnet_final_z) / magnet_speed).astype(int),
                              init_func=init, blit=True, interval=50)

plt.tight_layout()
plt.show()

# %%