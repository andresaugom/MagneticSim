# %%
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

# %%
# ------------------- Parámetros del sistema -------------------
coils_number = 3             # Número de espiras
coils_step = 0.1               # Distancia entre espiras (en z)
coils_radius = 1             # Radio de cada espira
coils_points = 1000           # Puntos por espira (resolución)

i = 300                     # Corriente en Amperes
mu_0 = 4 * np.pi * 1e-7     # Permeabilidad del vacío
km = mu_0 * i / (4 * np.pi) # Constante de Biot-Savart

# %%
# ------------------- Geometría de una espira -------------------
thetas = np.linspace(0, 2*np.pi, coils_points, endpoint=False)

# Posiciones (en plano XY)
coil_pos_x = coils_radius * np.cos(thetas)
coil_pos_y = coils_radius * np.sin(thetas)
coil_pos_z = np.zeros_like(coil_pos_x)  # Espira plana en z = 0

# Diferenciales dl (entre puntos consecutivos)
dl_x = np.diff(coil_pos_x, append=coil_pos_x[0])
dl_y = np.diff(coil_pos_y, append=coil_pos_y[0])
dl_z = np.zeros_like(dl_x)

# %%
# ------------------- Repetición en espiras -------------------
all_segment_origins = []
all_dl_vectors = []

for z_pos in np.arange(0, coils_number * coils_step + coils_step, coils_step):
    # Posiciones de origen de cada segmento en esta espira
    origin_x = coil_pos_x
    origin_y = coil_pos_y
    origin_z = np.full_like(coil_pos_x, z_pos)
    
    segment_origins = np.stack([origin_x, origin_y, origin_z], axis=1)
    dl_vectors = np.stack([dl_x, dl_y, dl_z], axis=1)
    
    all_segment_origins.append(segment_origins)
    all_dl_vectors.append(dl_vectors)

r_primes = np.concatenate(all_segment_origins, axis=0)
dl_vectors = np.concatenate(all_dl_vectors, axis=0)

# %%
# ------------------- Cálculo del campo magnético -------------------
space_res = 0.5 # Resolucion espacial

# Definicion del espacio
x_dim = np.arange(-2, 2 +space_res, space_res).reshape(-1, 1)
y_dim = np.arange(-3, 3 +space_res, space_res).reshape(-1, 1)
z_dim = np.arange(-4, 4 +space_res, space_res).reshape(-1, 1)
# Campo magnetico
Bx, By, Bz = np.meshgrid(x_dim, y_dim, z_dim, indexing='ij')

B = np.stack([Bx, By, Bz], axis = -1)
r = B[np.newaxis, ...]
r_prime = r_primes[:, np.newaxis, np.newaxis, np.newaxis, :]

r_vector = r - r_prime
dl = dl_vectors[:, np.newaxis, np.newaxis, np.newaxis, :]

r_norm = np.linalg.norm(r_vector, axis=-1)
r_norm3 = np.where(r_norm == 0, np.inf, r_norm**3)

dB = km * (np.cross(dl, r_vector)/r_norm3[..., np.newaxis])
B = np.sum(dB, axis=0)
# %%
# ------------------- Mapa de calor de la magnitud de B en el plano z = 0 -------------------
x_index = np.argmin(x_dim)  # Índice del plano más cercano a z=0

# Extrae componentes del campo en el plano z=0
By_plane = B[..., 1][x_index, :, :]
Bz_plane = B[..., 2][x_index, :, :]

# Magnitud del campo
B_magnitude = np.sqrt(Bz_plane**2 + By_plane**2)

# Crea la malla de coordenadas
Y_plane, Z_plane = np.meshgrid(y_dim, z_dim, indexing='ij')

plt.figure(figsize=(8, 6))
heatmap = plt.contourf(Y_plane, Z_plane, B_magnitude, levels=100, cmap='inferno')
plt.colorbar(heatmap, label='|B| (T)')
plt.xlabel('Y')
plt.ylabel('Z')
plt.title('Magnitud del campo magnético en el plano x = 0')
plt.axis('equal')
plt.grid(True, linestyle='--', alpha=0.3)
plt.show()

# %%
# ------------------- Visualización del campo magnético en 3D -------------------
# Selecciona un subconjunto de puntos para visualizar (para no saturar el gráfico)
step = 2  # Ajusta este valor para más/menos flechas
Xq = Bx[::step, ::step, ::step]
Yq = By[::step, ::step, ::step]
Zq = Bz[::step, ::step, ::step]
U = B[::step, ::step, ::step, 0]
V = B[::step, ::step, ::step, 1]
W = B[::step, ::step, ::step, 2]

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
ax.quiver(Xq, Yq, Zq, U, V, W, length=0.2, normalize=True, color='blue', linewidth=0.5)

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('Campo magnético 3D (quiver)')
plt.tight_layout()
plt.show()
# %%
