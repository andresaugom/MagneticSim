import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle, FancyArrow

# --- Parámetros de la simulación ---
# Coil (Espira)
coil_x = 0
coil_y = 0
coil_width = 1.5  # Ancho de la espira
coil_height = 1.5 # Alto de la espira
num_turns = 10    # Número de vueltas (para un efecto de bobina simple)
coil_resistance = 1.0 # Resistencia de la espira (Ohms)

# Magnet (Imán)
magnet_length = 0.8
magnet_width = 0.4
initial_magnet_x = -3.0
initial_magnet_y = 0.0
magnet_speed = 0.1  # Velocidad del imán (unidades/frame)

# Campo magnético (simplificado para un imán en movimiento)
# Asumimos que el campo magnético de un imán puntual disminuye con 1/r^2
# Para una simulación 2D y simplificada, podemos usar una función de caída más suave.
# Para el campo magnético del imán, vamos a simplificar asumiendo un dipolo magnético
# y luego enfocarnos en el flujo a través de la espira.
# La fuerza del campo magnético será más conceptual para esta visualización.
B_field_strength = 1.0 # Una constante para la "intensidad" del campo magnético del imán

# --- Configuración de la figura y ejes ---
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_xlim([-5, 5])
ax.set_ylim([-3, 3])
ax.set_aspect('equal')
ax.set_title("Ley de Faraday y Ley de Lenz (Simulación 2D)")
ax.grid(True, linestyle='--', alpha=0.7)

# --- Dibujar la espira ---
# Usamos un Rectángulo para la espira. Para simplificar, la corriente se indicará en el centro.
coil_patch = Rectangle((coil_x - coil_width/2, coil_y - coil_height/2),
                       coil_width, coil_height,
                       edgecolor='blue', facecolor='none', linewidth=2, linestyle='-')
ax.add_patch(coil_patch)
coil_center_x = coil_x
coil_center_y = coil_y
ax.text(coil_center_x, coil_center_y + coil_height/2 + 0.3, "Bobina", ha='center', color='blue')

# --- Dibujar el imán ---
magnet_patch = Rectangle((initial_magnet_x - magnet_length/2, initial_magnet_y - magnet_width/2),
                         magnet_length, magnet_width,
                         edgecolor='black', facecolor='red', linewidth=2)
ax.add_patch(magnet_patch)
# Polo Norte y Sur (simplificado para visualización)
north_pole_text = ax.text(initial_magnet_x + magnet_length/4, initial_magnet_y, 'N', ha='center', va='center', color='white', fontsize=12, fontweight='bold')
south_pole_text = ax.text(initial_magnet_x - magnet_length/4, initial_magnet_y, 'S', ha='center', va='center', color='black', fontsize=12, fontweight='bold')

# --- Indicadores de corriente y campo magnético inducido ---
current_arrow = FancyArrow(coil_center_x, coil_center_y, 0, 0, width=0.1, head_width=0.3, head_length=0.3,
                           facecolor='green', edgecolor='green', alpha=0.0) # Inicialmente invisible
ax.add_patch(current_arrow)
current_text = ax.text(coil_center_x, coil_center_y - coil_height/2 - 0.3, "Corriente Inducida: 0 A", ha='center', color='green')

induced_B_arrow_in = FancyArrow(coil_center_x + 0.5, coil_center_y, 0, -0.5, width=0.05, head_width=0.15, head_length=0.15,
                                facecolor='purple', edgecolor='purple', alpha=0.0, label="B Inducido (Entrando)")
induced_B_arrow_out = FancyArrow(coil_center_x + 0.5, coil_center_y, 0, 0.5, width=0.05, head_width=0.15, head_length=0.15,
                                 facecolor='purple', edgecolor='purple', alpha=0.0, label="B Inducido (Saliendo)")
ax.add_patch(induced_B_arrow_in)
ax.add_patch(induced_B_arrow_out)
induced_B_text = ax.text(coil_center_x + 0.5, coil_center_y + 0.8, "B Inducido", ha='center', color='purple', alpha=0.0)

# --- Líneas de campo magnético del imán (ilustrativas) ---
field_lines = []
for _ in range(8): # Número de líneas ilustrativas
    line, = ax.plot([], [], 'r--', alpha=0.5)
    field_lines.append(line)

# --- Variables para la animación ---
magnet_x = initial_magnet_x
flux_history = []
emf_history = []
current_history = []
time_steps = []

# --- Funciones para calcular el flujo magnético (simplificado) ---
def calculate_magnetic_field_at_coil(magnet_pos_x, coil_pos_x, coil_width, B_strength):
    """
    Calcula una representación simplificada del campo magnético efectivo
    que atraviesa la espira debido al imán.
    Esto no es una ley física exacta, sino una aproximación para la simulación.
    Asumimos que el campo es más fuerte cerca del imán y cae con la distancia.
    """
    distance = abs(magnet_pos_x - coil_pos_x)
    # Una función que disminuye con la distancia, e.g., 1/(distance^2 + epsilon)
    # Agregamos un pequeño epsilon para evitar división por cero cuando el imán está justo encima.
    epsilon = 0.1
    # Multiplicamos por coil_width para simular que un imán más ancho "cubre" más de la espira.
    # El signo depende de si el polo N se acerca o se aleja (asumimos N a la derecha del imán)
    # Si el imán se acerca desde la izquierda, el polo N está a la derecha del imán,
    # entonces las líneas de campo entran a la espira (flujo positivo si entra).
    # Si el imán se aleja hacia la derecha, el flujo sigue siendo positivo.
    # Si el imán se acerca desde la derecha, el polo S estaría a la izquierda, flujo negativo.
    # Para simplificar, asumimos que el imán siempre presenta su polo N hacia la espira
    # cuando se acerca desde la izquierda y S desde la derecha, o viceversa, dependiendo de la dirección.
    # Aquí, asumimos que el campo siempre es positivo cuando el imán se acerca desde la izquierda,
    # y negativo cuando se aleja o se acerca desde la derecha.
    # La dirección del campo es crucial para la Ley de Lenz.
    # Vamos a suponer que el imán se mueve horizontalmente y su polo N está orientado hacia la derecha.
    # Cuando se acerca, el flujo aumenta. Cuando se aleja, el flujo disminuye.
    # Para el cálculo del flujo, simplemente consideramos la magnitud y la dirección relativa.
    # Si el imán está a la izquierda de la espira (x_magnet < x_coil), el flujo entrante (desde la derecha)
    # puede considerarse positivo.
    # Si el imán está a la derecha de la espira (x_magnet > x_coil), el flujo saliente (desde la izquierda)
    # puede considerarse negativo.
    # Esto es una gran simplificación, pero suficiente para ilustrar el concepto.
    B_magnitude = B_strength / (distance**2 + epsilon)

    # Determinar el signo del campo basándose en la posición relativa del imán
    # Si el imán está a la izquierda y se mueve hacia la espira, el campo es entrante.
    # Si el imán está a la derecha y se mueve hacia la espira, el campo es saliente.
    # Para esta simulación, asumimos que el polo N del imán siempre está apuntando hacia la espira cuando el imán se mueve horizontalmente.
    # Si el imán se mueve de izquierda a derecha, el polo N entra, generando flujo positivo.
    # Si el imán se mueve de derecha a izquierda, el polo S entra, generando flujo negativo.
    # Sin embargo, la ley de Faraday se basa en el *cambio* de flujo.
    # Vamos a mantener la magnitud y el signo se determinará por el cambio.
    return B_magnitude

# --- Inicialización de la animación ---
def init():
    magnet_patch.set_xy((initial_magnet_x - magnet_length/2, initial_magnet_y - magnet_width/2))
    north_pole_text.set_position((initial_magnet_x + magnet_length/4, initial_magnet_y))
    south_pole_text.set_position((initial_magnet_x - magnet_length/4, initial_magnet_y))
    current_arrow.set_alpha(0.0)
    current_text.set_text("Corriente Inducida: 0 A")
    induced_B_arrow_in.set_alpha(0.0)
    induced_B_arrow_out.set_alpha(0.0)
    induced_B_text.set_alpha(0.0)
    for line in field_lines:
        line.set_data([], [])
    flux_history.clear()
    emf_history.clear()
    current_history.clear()
    time_steps.clear()
    return [magnet_patch, north_pole_text, south_pole_text, current_arrow, current_text,
            induced_B_arrow_in, induced_B_arrow_out, induced_B_text] + field_lines

# --- Función de animación ---
def animate(frame):
    global magnet_x
    global flux_history, emf_history, current_history, time_steps

    # Mover el imán
    magnet_x += magnet_speed
    if magnet_x > ax.get_xlim()[1] + magnet_length/2: # Si el imán sale por la derecha, reinicia por la izquierda
        magnet_x = ax.get_xlim()[0] - magnet_length/2

    magnet_patch.set_xy((magnet_x - magnet_length/2, initial_magnet_y - magnet_width/2))
    north_pole_text.set_position((magnet_x + magnet_length/4, initial_magnet_y))
    south_pole_text.set_position((magnet_x - magnet_length/4, initial_magnet_y))

    # --- Calcular el flujo magnético (Phi_B) ---
    # Simplificación: el flujo es proporcional al campo magnético efectivo en la espira
    # y al área de la espira (que es constante).
    # Aquí, el campo es una función de la posición del imán.
    B_at_coil = calculate_magnetic_field_at_coil(magnet_x, coil_center_x, coil_width, B_field_strength)
    # Asumimos que el área efectiva es coil_width * coil_height
    # Flujo = B * A * cos(theta). Como es 2D y el imán se mueve perpendicular, cos(theta) = 1.
    # El signo del flujo dependerá de la dirección del campo.
    # Para esta simulación, asumamos que cuando el polo N se acerca a la bobina, el flujo es positivo.
    # Si el imán se mueve de izquierda a derecha (magnet_speed > 0):
    # Cuando se acerca a la espira (magnet_x < coil_center_x), el flujo aumenta (positivo).
    # Cuando se aleja de la espira (magnet_x > coil_center_x), el flujo disminuye (positivo pero su cambio es negativo).
    # Esto es una simplificación muy grande. Para mayor rigor, necesitaríamos integrar el campo.
    # Aquí, vamos a modelar el flujo de forma más conceptual para ilustrar el cambio.
    # Podemos hacer que el flujo sea máximo cuando el imán está en el centro de la bobina
    # y disminuya a medida que se aleja.
    # Use una función gaussiana o similar para el flujo para que sea suave.
    # phi_B = B_strength * np.exp(-((magnet_x - coil_center_x)**2) / (2 * (coil_width/2)**2)) * coil_width * coil_height
    # Para que el flujo tenga un signo y el cambio sea claro:
    # Si el imán viene de la izquierda y se acerca, el flujo entrante es positivo.
    # Si el imán viene de la derecha y se acerca, el flujo saliente es negativo.
    # Consideraremos que el polo Norte del imán genera líneas de campo que salen de él.
    # Si el polo Norte se acerca a la bobina desde la izquierda, las líneas entran a la bobina, flujo POSITIVO.
    # Si el polo Norte se aleja de la bobina hacia la derecha, las líneas que entran a la bobina DISMINUYEN.
    # Si el polo Sur se acerca a la bobina desde la izquierda, las líneas salen de la bobina, flujo NEGATIVO.
    # Si el polo Sur se aleja de la bobina hacia la derecha, las líneas que salen de la bobina DISMINUYEN (se hacen menos negativas).

    # Vamos a asumir que el imán tiene su polo N a la derecha y S a la izquierda, y se mueve horizontalmente.
    # Cuando el imán se mueve de izquierda a derecha, el polo N se acerca a la espira, el flujo entrante (en dirección -y) aumenta.
    # Cuando el imán se mueve de derecha a izquierda, el polo S se acerca a la espira, el flujo saliente (en dirección +y) aumenta.
    # Para simplificar el flujo, usaremos una función que sea cero lejos y máxima cuando el imán está en el centro.
    # Y el signo del flujo dependerá de la dirección del movimiento del imán.
    # Para una simulación 2D, consideremos el flujo que atraviesa el área de la espira.
    # Una aproximación razonable para el campo axial de un dipolo es B_x ~ 1/x^3.
    # Sin embargo, para la visualización, una función de tipo Lorentziana o Gaussiana es más manejable
    # para representar la "influencia" del imán.
    
    # Campo efectivo (magnitud) en la espira:
    # Usamos una función de tipo Lorentziana centrada en la espira.
    # Esto simula que el campo es más fuerte cuando el imán está sobre la espira.
    # El factor (coil_width/2) es como una "escala" de la influencia.
    # Esto es una simplificación: estamos asumiendo que el campo es uniforme a través del área de la espira
    # en la región donde el imán la está influenciando.
    magnetic_field_magnitude = B_field_strength / ((magnet_x - coil_center_x)**2 + (coil_width/2)**2)

    # El signo del flujo depende de la dirección del campo y la orientación de la espira.
    # Si el imán se mueve de izquierda a derecha, asumimos que el polo N está hacia la espira.
    # Esto genera un flujo que "entra" en la espira (por ejemplo, en la dirección negativa del eje Y si la espira está en el plano XY).
    # Entonces el flujo es positivo.
    phi_B = magnetic_field_magnitude * coil_width * coil_height * num_turns # Multiplicamos por num_turns para simular una bobina

    # --- Líneas de campo del imán (ilustrativas) ---
    # Simular líneas que salen del N y entran al S
    magnet_n_x = magnet_x + magnet_length/2 * 0.7 # Punto N del imán
    magnet_s_x = magnet_x - magnet_length/2 * 0.7 # Punto S del imán
    for i, line in enumerate(field_lines):
        # Generar puntos de línea de campo, simplificado
        # Para que salgan del N y lleguen al S (o se extiendan)
        if i % 2 == 0: # Líneas superiores
            x_pts = np.linspace(magnet_n_x, magnet_x + 5, 20)
            y_pts = (i * 0.2 + 0.5) * np.exp(-(x_pts - magnet_n_x)**2 / 2) + initial_magnet_y
        else: # Líneas inferiores
            x_pts = np.linspace(magnet_n_x, magnet_x + 5, 20)
            y_pts = -(i * 0.2 + 0.5) * np.exp(-(x_pts - magnet_n_x)**2 / 2) + initial_magnet_y

        # También líneas que entran por el S
        x_pts_s = np.linspace(magnet_s_x, magnet_x - 5, 20)
        y_pts_s = (i * 0.2 + 0.5) * np.exp(-(x_pts_s - magnet_s_x)**2 / 2) + initial_magnet_y

        line.set_data(np.concatenate((x_pts_s[::-1], x_pts)), np.concatenate((y_pts_s[::-1], y_pts)))


    # --- Ley de Faraday: FEM = -d(Phi_B)/dt ---
    # Para el cálculo numérico de la derivada, necesitamos el flujo anterior.
    # Guardamos el flujo y el tiempo (frames).
    time_steps.append(frame)
    flux_history.append(phi_B)

    emf_induced = 0
    if len(flux_history) > 1:
        # Aproximación de la derivada numérica: (Phi_B_actual - Phi_B_anterior) / (tiempo_actual - tiempo_anterior)
        # Como los frames son constantes, podemos usar (Phi_B_actual - Phi_B_anterior) / (velocidad_simulada_dt)
        # La velocidad del imán es magnet_speed, que es como nuestro dt para la posición.
        # Asumamos que cada frame es un 'dt' constante en el tiempo.
        dt_sim = 1 # cada frame es una unidad de tiempo
        delta_flux = flux_history[-1] - flux_history[-2]
        emf_induced = -delta_flux / dt_sim # Ley de Faraday
        # Para que la FEM sea más pronunciada cuando el imán está justo encima y la tasa de cambio es máxima
        # Consideramos la tasa de cambio del campo con respecto a la posición, multiplicada por la velocidad del imán.
        # d(Phi_B)/dt = (d(Phi_B)/dx) * (dx/dt)
        # d(Phi_B)/dx de la función Lorentziana es más compleja, pero su forma es similar a una campana con picos en los lados.
        # Vamos a usar la derivada numérica para simplicidad.

    # --- Ley de Ohm: I = FEM / R ---
    current_induced = emf_induced / coil_resistance

    # --- Ley de Lenz: El campo magnético inducido se opone al cambio de flujo ---
    # Si emf_induced > 0: el flujo está aumentando (se está volviendo más positivo o menos negativo).
    #   Para oponerse a un flujo entrante (positivo) que aumenta, se debe generar un campo saliente.
    #   Esto significa que el campo magnético inducido (B_inducido) apunta en la dirección opuesta al campo original.
    #   Si el imán se acerca desde la izquierda (N hacia la bobina), el flujo entrante aumenta.
    #   La corriente inducida debe generar un campo magnético saliente para oponerse.
    #   Por la regla de la mano derecha, si el campo inducido es saliente (hacia +y), la corriente es anti-horaria.
    # Si emf_induced < 0: el flujo está disminuyendo (se está volviendo menos positivo o más negativo).
    #   Para oponerse a un flujo entrante (positivo) que disminuye, se debe generar un campo entrante.
    #   Si el imán se aleja hacia la derecha (N se aleja de la bobina), el flujo entrante disminuye.
    #   La corriente inducida debe generar un campo magnético entrante para oponerse a la disminución.
    #   Por la regla de la mano derecha, si el campo inducido es entrante (hacia -y), la corriente es horaria.

    # Actualizar la visualización de la corriente y el campo inducido
    current_strength = abs(current_induced)
    if current_strength > 0.01: # Solo mostrar si hay una corriente significativa
        current_arrow.set_alpha(1.0)
        # Dirección de la flecha de corriente:
        # Asumimos que "entrante" es en la dirección -Y (hacia abajo)
        # y "saliente" es en la dirección +Y (hacia arriba)
        # Esto es una simplificación de la representación 2D para una espira rectangular.
        # Si la FEM es positiva (flujo positivo aumentando, o flujo negativo disminuyendo)
        # la corriente debe generar un B inducido que se oponga a ese cambio.

        # Un enfoque más claro:
        # El flujo cambia de acuerdo a la posición del imán y su movimiento.
        # Cuando el imán (N) se acerca desde la izquierda:
        #   El flujo entrante (positivo) aumenta.
        #   La FEM es negativa (según la Ley de Faraday con el signo).
        #   La corriente será negativa (si resistencia > 0).
        #   Una corriente negativa (anti-horaria) generaría un B inducido saliente,
        #   oponiéndose al aumento del flujo entrante.
        # Cuando el imán (N) se aleja hacia la derecha:
        #   El flujo entrante (positivo) disminuye.
        #   La FEM es positiva.
        #   La corriente será positiva.
        #   Una corriente positiva (horaria) generaría un B inducido entrante,
        #   oponiéndose a la disminución del flujo entrante.

        # Vamos a visualizar la dirección de la corriente y el campo inducido.
        if emf_induced < 0: # Corriente anti-horaria (para oponerse a un aumento de flujo entrante)
            # Para una espira rectangular, anti-horaria significa:
            # Lado izquierdo: arriba (+y)
            # Lado superior: derecha (+x)
            # Lado derecho: abajo (-y)
            # Lado inferior: izquierda (-x)
            current_arrow.set_data(x=[coil_center_x + coil_width/2 * 0.7, coil_center_x + coil_width/2 * 0.7],
                                   y=[coil_center_y + coil_height/2 * 0.7, coil_center_y + coil_height/2 * 0.7 - 0.001], # Pequeña perturbación para la flecha
                                   dx=0, dy=-0.1 * np.sign(current_induced)) # Flecha hacia abajo (anti-horario)
            induced_B_arrow_out.set_alpha(1.0) # B inducido saliente (hacia +y)
            induced_B_arrow_in.set_alpha(0.0)
            induced_B_text.set_text("B inducido: SALIENDO")
            induced_B_text.set_alpha(1.0)

        elif emf_induced > 0: # Corriente horaria (para oponerse a una disminución de flujo entrante)
            # Horaria:
            # Lado izquierdo: abajo (-y)
            # Lado superior: izquierda (-x)
            # Lado derecho: arriba (+y)
            # Lado inferior: derecha (+x)
            current_arrow.set_data(x=[coil_center_x + coil_width/2 * 0.7, coil_center_x + coil_width/2 * 0.7],
                                   y=[coil_center_y - coil_height/2 * 0.7, coil_center_y - coil_height/2 * 0.7 + 0.001], # Pequeña perturbación
                                   dx=0, dy=0.1 * np.sign(current_induced)) # Flecha hacia arriba (horario)
            induced_B_arrow_in.set_alpha(1.0) # B inducido entrante (hacia -y)
            induced_B_arrow_out.set_alpha(0.0)
            induced_B_text.set_text("B inducido: ENTRANDO")
            induced_B_text.set_alpha(1.0)
        else:
            current_arrow.set_alpha(0.0)
            induced_B_arrow_in.set_alpha(0.0)
            induced_B_arrow_out.set_alpha(0.0)
            induced_B_text.set_alpha(0.0)

    else:
        current_arrow.set_alpha(0.0)
        induced_B_arrow_in.set_alpha(0.0)
        induced_B_arrow_out.set_alpha(0.0)
        induced_B_text.set_alpha(0.0)

    current_text.set_text(f"Corriente Inducida: {current_induced:.4f} A")

    emf_history.append(emf_induced)
    current_history.append(current_induced)

    # Actualizar la gráfica de flujo, FEM y corriente
    # (Para ello, necesitaríamos un segundo conjunto de ejes o una gráfica separada.
    # Por ahora, nos enfocamos en la visualización principal. Podemos añadir esto después.)

    return [magnet_patch, north_pole_text, south_pole_text, current_arrow, current_text,
            induced_B_arrow_in, induced_B_arrow_out, induced_B_text] + field_lines

# --- Animación ---
ani = animation.FuncAnimation(fig, animate, frames=200, interval=50, blit=True, init_func=init)

# --- Explicación científica (se imprimiría en la consola o se mostraría como texto) ---
print("\n--- Explicación Científica de la Simulación ---")
print("Principio: Inducción Electromagnética (Ley de Faraday y Ley de Lenz)")
print("\n**Ley de Faraday de la Inducción Electromagnética:**")
print("Establece que una fuerza electromotriz (FEM) se induce en una espira conductora")
print("cuando hay un cambio en el flujo magnético (Phi_B) que atraviesa la espira.")
print(r"La fórmula es: $FEM = -N \frac{d\Phi_B}{dt}$")
print("Donde N es el número de vueltas de la bobina (simplificado aquí como 'num_turns'),")
print("y d(Phi_B)/dt es la tasa de cambio del flujo magnético con respecto al tiempo.")
print("Unidades: Flujo magnético en Weber (Wb), tiempo en segundos (s), FEM en Voltios (V).")
print("\n**Ley de Lenz:**")
print("Indica la dirección de la corriente inducida. La corriente inducida fluirá en")
print("una dirección tal que el campo magnético que produce se oponga al cambio en el")
print("flujo magnético que lo originó.")
print("El signo negativo en la Ley de Faraday representa la Ley de Lenz.")
print("\n**Simulación:**")
print("1. **Imán en movimiento:** Representa la fuente de un campo magnético.")
print("2. **Bobina (espira):** El conductor donde se induce la corriente.")
print("3. **Campo Magnético (rojo):** Líneas ilustrativas que emanan del polo Norte del imán.")
print("4. **Cálculo del Flujo (Simplificado):** En la simulación, el flujo magnético a través de la espira")
print("   se aproxima como una función de la distancia entre el imán y la espira. Es máximo cuando el imán")
print("   está centrado sobre la espira y disminuye a medida que se aleja.")
print("5. **Cálculo de la FEM:** Se calcula la tasa de cambio del flujo magnético entre frames (derivada numérica).")
print("6. **Cálculo de la Corriente:** Usando la Ley de Ohm ($I = FEM / R$), se calcula la corriente inducida.")
print("   La resistencia de la bobina (`coil_resistance`) afecta la magnitud de la corriente.")
print("7. **Visualización de Corriente (verde):** La flecha verde indica la dirección de la corriente.")
print("   - Si el flujo entrante (positivo) **aumenta** (imán acercándose), la FEM es negativa, la corriente")
print("     genera un campo magnético inducido **saliendo** de la espira para oponerse al aumento.")
print("   - Si el flujo entrante (positivo) **disminuye** (imán alejándose), la FEM es positiva, la corriente")
print("     genera un campo magnético inducido **entrando** en la espira para oponerse a la disminución.")
print("   - La flecha de la corriente se ajusta para ser horaria o anti-horaria, produciendo el campo inducido (morado) correcto.")
print("   (La dirección de la corriente es simplificada para 2D, se muestra una flecha representativa de la dirección general)")
print("8. **Campo Magnético Inducido (morado):** La flecha morada muestra la dirección del campo magnético producido por la corriente inducida.")
print("   Siempre se opone al *cambio* de flujo, no al flujo en sí.")
print("\n**Limitaciones y Simplificaciones:**")
print("Esta simulación es una ilustración conceptual. No calcula las líneas de campo magnético")
print("ni el flujo de manera rigurosa para un imán real en 3D. El campo y el flujo son modelos")
print("matemáticos simplificados para demostrar los principios de Faraday y Lenz.")
print("La interacción electromagnética y las fuerzas entre el imán y la bobina no están simuladas.")

plt.show()

# --- Gráficos adicionales para análisis (opcional, se pueden añadir después de plt.show() o en una ventana separada) ---
# Si quisieras ver las gráficas de flujo, FEM y corriente vs tiempo después de la simulación
# plt.figure(figsize=(12, 8))
#
# plt.subplot(3, 1, 1)
# plt.plot(time_steps, flux_history, label='Flujo Magnético (Phi_B)')
# plt.title('Flujo Magnético, FEM Inducida y Corriente vs. Tiempo')
# plt.ylabel('Flujo (Wb)')
# plt.grid(True)
# plt.legend()
#
# plt.subplot(3, 1, 2)
# plt.plot(time_steps, emf_history, color='orange', label='FEM Inducida')
# plt.ylabel('FEM (V)')
# plt.grid(True)
# plt.legend()
#
# plt.subplot(3, 1, 3)
# plt.plot(time_steps, current_history, color='green', label='Corriente Inducida')
# plt.xlabel('Tiempo (frames)')
# plt.ylabel('Corriente (A)')
# plt.grid(True)
# plt.legend()
#
# plt.tight_layout()
# plt.show()