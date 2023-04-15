import pygame
from qiskit import QuantumCircuit, execute, Aer
import random
import math

# Set up the game window
pygame.init()

scale = 2
screen = pygame.display.set_mode((640 * scale, 480 * scale))
pygame.display.set_caption("Quantum Game")

laser_sounds = [
    pygame.mixer.Sound('sounds/punch1.wav'),
    pygame.mixer.Sound('sounds/punch2.wav'),
    pygame.mixer.Sound('sounds/throwknife.wav')
]

hit_sounds = [
    pygame.mixer.Sound('sounds/Explosion1.wav'),
    pygame.mixer.Sound('sounds/Explosion3.wav'),
    pygame.mixer.Sound('sounds/Explosion5.wav')
]

# Set up the player's qubit
qc = QuantumCircuit(1)
qc.h(0)

theta = 0
player_score = 0
flash_alpha = 0
enemy_speed = 1 * scale
enemy_horizontal_speed = 0.5

destroyed_enemies = []
lasers = []

# Set up the player's sphere
player_pos = (320 * scale, 240 * scale)
player_radius = 60 * scale

button_width = 120
button_height = 50
button_margin = 20
screen_height = screen.get_height()
increase_button = pygame.Rect(button_margin, screen_height - button_height - button_margin, button_width, button_height)
decrease_button = pygame.Rect(button_width * 2 + button_margin * 3, screen_height - button_height - button_margin, button_width, button_height)
x_button = pygame.Rect(button_width + button_margin * 2, screen_height - button_height - button_margin, button_width, button_height)

def update_player_color():
    # Run the circuit and get the statevector
    backend = Aer.get_backend('statevector_simulator')
    job = execute(qc, backend)
    result = job.result()
    statevector = result.get_statevector()

    # Calculate the probability of measuring 0 and 1
    prob_0 = abs(statevector[0])**2
    prob_1 = abs(statevector[1])**2

    # Set the player's color based on the qubit state
    player_color = (prob_0 * 255, 0, prob_1 * 255)
    return player_color

player_color = update_player_color()

# Set up the enemies' qubits and spheres
num_enemies = 5
enemy_qcs = [QuantumCircuit(1) for _ in range(num_enemies)]
for eqc in enemy_qcs:
    eqc.h(0)
    eqc.ry(random.uniform(0, 2 * math.pi), 0)

enemy_radius = 30 * scale

destroyed_enemies_alpha = [255] * num_enemies

def update_enemy_colors():
    enemy_colors = []
    for eqc in enemy_qcs:
        # Run the circuit and get the statevector
        backend = Aer.get_backend('statevector_simulator')
        job = execute(eqc, backend)
        result = job.result()
        statevector = result.get_statevector()

        # Calculate the probability of measuring 0 and 1
        prob_0 = abs(statevector[0])**2
        prob_1 = abs(statevector[1])**2

        # Set the enemy's color based on the qubit state
        enemy_color = (prob_0 * 255, 0, prob_1 * 255)
        enemy_colors.append(enemy_color)
    return enemy_colors

enemy_colors = update_enemy_colors()
enemy_positions = [(i * (640 // num_enemies) + (320 // num_enemies), enemy_radius) for i in range(num_enemies)]

def generate_enemy():
    eqc = QuantumCircuit(1)
    eqc.h(0)
    eqc.ry(random.uniform(0, 2 * math.pi), 0)

    # Run the circuit and get the statevector
    backend = Aer.get_backend('statevector_simulator')
    job = execute(eqc, backend)
    result = job.result()
    statevector = result.get_statevector()

    # Calculate the probability of measuring 0 and 1
    prob_0 = abs(statevector[0])**2
    prob_1 = abs(statevector[1])**2

    # Set the enemy's color based on the qubit state
    enemy_color = (prob_0 * 255, 0, prob_1 * 255)

    return eqc, enemy_color

create_enemy_count = 0

prob_0_history = []
prob_1_history = []
max_history_length = 1
phi = 0
pygame.mixer.Sound('sounds/polizia4.wav').play()

# Game loop
mouse_held_down = False
done = False
while not done:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if increase_button.collidepoint(event.pos):
                mouse_held_down = 'increase'
            elif decrease_button.collidepoint(event.pos):
                mouse_held_down = 'decrease'
            elif x_button.collidepoint(event.pos):
                mouse_held_down = 'x'
        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_held_down = False

    # Execute action if mouse button is held down
    if mouse_held_down == 'increase':
        theta -= 0.1
        qc.ry(-0.1, 0)
        player_color = update_player_color()
    elif mouse_held_down == 'decrease':
        theta += 0.1
        qc.ry(0.1, 0)
        player_color = update_player_color()
    elif mouse_held_down == 'x':
        phi += 0.1
        qc.rx(0.1, 0)
        player_color = update_player_color()

    # Handle keyboard input
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        theta -= 0.1
        qc.ry(-0.1, 0)
        player_color = update_player_color()
    if keys[pygame.K_RIGHT]:
        theta += 0.1
        qc.ry(0.1, 0)
        player_color = update_player_color()
    if keys[pygame.K_UP]:
        phi -= 0.1
        qc.rx(-0.1, 0)
        player_color = update_player_color()
    if keys[pygame.K_DOWN]:
        phi += 0.1
        qc.rx(0.1, 0)
        player_color = update_player_color()

    # Calculate player qubit probabilities
    backend = Aer.get_backend('statevector_simulator')
    job = execute(qc, backend)
    result = job.result()
    statevector = result.get_statevector()
    prob_0 = abs(statevector[0])**2
    prob_1 = abs(statevector[1])**2

    prob_0_history.append(prob_0)
    prob_1_history.append(prob_1)
    if len(prob_0_history) > max_history_length:
        prob_0_history.pop(0)
        prob_1_history.pop(0)

    # Check for collisions with enemies
    tolerance_range = 5
    for i in range(num_enemies):
        if abs(player_color[0] - enemy_colors[i][0]) < tolerance_range and abs(player_color[2] - enemy_colors[i][2]) < tolerance_range:
            if i not in destroyed_enemies:
                destroyed_enemies.append(i)
                # Add laser animation
                laser = {
                    'start_pos': player_pos,
                    'end_pos': enemy_positions[i],
                    'color': player_color,
                    'alpha': 255
                }
                lasers.append(laser)
                # Play sound effect
                random.choice(laser_sounds).play()

    # Update enemy colors and positions
    enemy_qcs = [qc for qc in enemy_qcs if qc is not None]
    num_enemies = len(enemy_qcs)
    if num_enemies > 0:
        enemy_colors = update_enemy_colors()
        #enemy_positions = [(i * (640 // num_enemies) + (320 // num_enemies), enemy_radius) for i in range(num_enemies)]

    # Add new enemies if 3 or more have been destroyed
    while create_enemy_count >= 3:
        eqc, enemy_color = generate_enemy()
        enemy_qcs.append(eqc)
        enemy_colors.append(enemy_color)
        destroyed_enemies_alpha.append(255)
        num_enemies += 1

        # Update enemy positions
        new_enemy_x = (640 // num_enemies) + (320 // num_enemies)
        new_enemy_y = enemy_radius
        enemy_positions.append((new_enemy_x, new_enemy_y))
        create_enemy_count -= 1

    # Redraw the screen
    screen.fill((0, 0, 0))
    pygame.draw.circle(screen, player_color, player_pos, player_radius)

    # Animate flash
    if flash_alpha > 0:
        flash_surface = pygame.Surface((640 * scale, 480 * scale))
        flash_surface.fill((255, 255, 255))
        flash_surface.set_alpha(flash_alpha)
        screen.blit(flash_surface, (0, 0))
        flash_alpha -= 25

    # Draw an indicator on the player's sphere to show the rotation of the qubit
    player_indicator_pos = (int(player_pos[0] + math.sin(theta) * player_radius * math.cos(phi)), int(player_pos[1] - math.cos(theta) * player_radius * math.cos(phi)))
    pygame.draw.line(screen, (255, 255, 255), player_pos, player_indicator_pos)
    pygame.draw.circle(screen, (255, 0, 0), player_indicator_pos, 5)

    crosshair_color = (0, 0, 0)
    crosshair_x = player_pos[0]
    crosshair_y = player_pos[1]
    pygame.draw.line(screen, crosshair_color, (crosshair_x - player_radius, crosshair_y), (crosshair_x + player_radius, crosshair_y))
    pygame.draw.line(screen, crosshair_color, (crosshair_x, crosshair_y - player_radius), (crosshair_x, crosshair_y + player_radius))

    for i in range(num_enemies):
        if i in destroyed_enemies:
            # Draw animation effect for destroyed enemy
            if destroyed_enemies_alpha[i] > 0:
                enemy_surface = pygame.Surface((enemy_radius * 2, enemy_radius * 2))
                enemy_surface.set_colorkey((0, 0, 0))
                enemy_surface.set_alpha(destroyed_enemies_alpha[i])
                pygame.draw.circle(enemy_surface, enemy_colors[i], (enemy_radius, enemy_radius), enemy_radius)
                screen.blit(enemy_surface, (enemy_positions[i][0] - enemy_radius, enemy_positions[i][1] - enemy_radius))
                destroyed_enemies_alpha[i] -= 25
            else:
                destroyed_enemies.remove(i)

        else:
            # Move enemies towards player.
            ex, ey = enemy_positions[i]
            ey += enemy_speed

            # Move enemy horizontally towards player
            if ex < player_pos[0]:
                ex += enemy_horizontal_speed
            elif ex > player_pos[0]:
                ex -= enemy_horizontal_speed
            enemy_positions[i] = (ex, ey)

            # Check for collision with player
            if ey + enemy_radius >= player_pos[1] - player_radius:
                player_score -= 1
                # Start flash animation
                flash_alpha = 255
                # Reset enemy position
                ex = i * (640 // num_enemies) + (320 // num_enemies)
                ey = enemy_radius
                enemy_positions[i] = (ex, ey)
                # Reset enemy position
                ex = i * (640 // num_enemies) + (320 // num_enemies)
                ey = enemy_radius
                enemy_positions[i] = (ex, ey)
                random.choice(hit_sounds).play()

            pygame.draw.circle(screen, enemy_colors[i], enemy_positions[i], enemy_radius)

    # Remove destroyed enemies from display
    for i in sorted(destroyed_enemies[:], reverse=True):
        if i < len(destroyed_enemies_alpha) and destroyed_enemies_alpha[i] <= 0:
            del enemy_qcs[i]
            del enemy_colors[i]
            del enemy_positions[i]
            del destroyed_enemies_alpha[i]
            destroyed_enemies.remove(i)
            player_score += 1
            create_enemy_count += 1
            if player_score % 10 == 0:
                enemy_speed += 1
                enemy_horizontal_speed += 0.2
        elif i >= len(destroyed_enemies_alpha):
            destroyed_enemies.remove(i)

    num_enemies = len(enemy_qcs)

    # Animate lasers
    for laser in lasers[:]:
        # Draw laser
        laser_surface = pygame.Surface((640, 480))
        laser_surface.set_colorkey((0, 0, 0))
        laser_surface.set_alpha(laser['alpha'])
        pygame.draw.line(laser_surface, laser['color'], laser['start_pos'], laser['end_pos'], 5)
        screen.blit(laser_surface, (0, 0))

        # Update laser alpha
        laser['alpha'] -= 25
        if laser['alpha'] <= 0:
            lasers.remove(laser)

    # Render player score
    font = pygame.font.Font(None, 36)
    text = font.render(f"Score: {player_score}", True, (255, 255, 255))
    text_rect = text.get_rect(center=(320 * scale, 20))
    screen.blit(text, text_rect)

    # Draw the buttons
    pygame.draw.rect(screen, (0, 75, 0), increase_button)
    increase_text = font.render("Rotate Y-", True, (255, 255, 255))
    screen.blit(increase_text,
                (increase_button.centerx - increase_text.get_width() // 2,
                increase_button.centery - increase_text.get_height() // 2))
    pygame.draw.rect(screen, (0, 75, 0), decrease_button)
    decrease_text = font.render("Rotate Y+", True, (255, 255, 255))
    screen.blit(decrease_text,
                (decrease_button.centerx - decrease_text.get_width() // 2,
                decrease_button.centery - decrease_text.get_height() // 2))

    # Draw the new button
    pygame.draw.rect(screen, (0, 75, 0), x_button)
    x_text = font.render("X", True, (255, 255, 255))
    screen.blit(x_text,
                (x_button.centerx - x_text.get_width() // 2,
                x_button.centery - x_text.get_height() // 2))

    # Draw bar chart.
    bar_width = 100 * scale
    bar_margin = 5 * scale
    bar_max_height = 125 * scale
    bar_x = 640 * scale - bar_width - bar_margin
    font = pygame.font.Font(None, 24)
    for i in range(len(prob_0_history)):
        bar_0_height = int(prob_0_history[i] * bar_max_height)
        bar_1_height = int(prob_1_history[i] * bar_max_height)
        bar_y = 480  * scale - bar_margin - bar_max_height
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y + bar_max_height - bar_0_height, bar_width // 2, bar_0_height))
        pygame.draw.rect(screen, (0, 0, 255), (bar_x + bar_width // 2, bar_y + bar_max_height - bar_1_height, bar_width // 2, bar_1_height))

        # Draw text labels for the bars
        text_0 = font.render("|0>", True, (255, 255, 255))
        text_1 = font.render("|1>", True, (255, 255, 255))
        screen.blit(text_0, (bar_x + (bar_width // 4) - (text_0.get_width() // 2), bar_y + bar_max_height + bar_margin - 25))
        screen.blit(text_1, (bar_x + (3 * bar_width // 4) - (text_1.get_width() // 2), bar_y + bar_max_height + bar_margin - 25))

        bar_x -= bar_width + bar_margin

    pygame.display.flip()

pygame.quit()