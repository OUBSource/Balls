import pygame
import math
import random
import sys

# Инициализация Pygame
pygame.init()

# Настройки экрана
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Пиксельная 3D Аркада 90-х - От первого лица")

# Цвета
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_RED = (128, 0, 0)
DARK_GREEN = (0, 128, 0)
DARK_BLUE = (0, 0, 128)

# 3D математика
class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    
    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def length(self):
        return math.sqrt(self.x*self.x + self.y*self.y + self.z*self.z)
    
    def normalize(self):
        length = self.length()
        if length > 0:
            return Vector3(self.x/length, self.y/length, self.z/length)
        return Vector3(0, 0, 0)
    
    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

class Cube3D:
    def __init__(self, position, size, color):
        self.position = position
        self.size = size
        self.color = color
        self.dark_color = (color[0]//2, color[1]//2, color[2]//2)
    
    def get_vertices(self):
        s = self.size / 2
        return [
            Vector3(-s, -s, -s), Vector3(s, -s, -s),
            Vector3(s, s, -s), Vector3(-s, s, -s),
            Vector3(-s, -s, s), Vector3(s, -s, s),
            Vector3(s, s, s), Vector3(-s, s, s)
        ]
    
    def project(self, camera_pos, camera_forward, camera_right, camera_up):
        vertices = self.get_vertices()
        projected = []
        
        for vertex in vertices:
            # Переводим в систему координат камеры
            world_vertex = vertex + self.position
            cam_relative = world_vertex - camera_pos
            
            # Проецируем на плоскость камеры
            z = cam_relative.dot(camera_forward)
            if z <= 0.1:  # За камерой
                projected.append(None)
                continue
                
            x = cam_relative.dot(camera_right)
            y = cam_relative.dot(camera_up)
            
            # Перспективная проекция
            scale = 400 / z
            screen_x = WIDTH // 2 + x * scale
            screen_y = HEIGHT // 2 - y * scale
            
            projected.append((screen_x, screen_y, scale))
        
        return projected
    
    def draw(self, screen, camera_pos, camera_forward, camera_right, camera_up):
        projected = self.project(camera_pos, camera_forward, camera_right, camera_up)
        
        # Рисуем грани куба
        faces = [
            [0, 1, 2, 3],  # задняя
            [4, 5, 6, 7],  # передняя
            [0, 1, 5, 4],  # нижняя
            [2, 3, 7, 6],  # верхняя
            [0, 3, 7, 4],  # левая
            [1, 2, 6, 5]   # правая
        ]
        
        face_colors = [
            self.dark_color,  # задняя
            self.color,       # передняя
            self.dark_color,  # нижняя
            self.dark_color,  # верхняя
            self.dark_color,  # левая
            self.dark_color   # правая
        ]
        
        # Сортируем грани по глубине
        face_depths = []
        for i, face in enumerate(faces):
            z_sum = 0
            count = 0
            for vertex_idx in face:
                if projected[vertex_idx]:
                    world_vertex = self.get_vertices()[vertex_idx] + self.position
                    z_sum += (world_vertex - camera_pos).dot(camera_forward)
                    count += 1
            if count > 0:
                face_depths.append((i, z_sum / count))
        
        face_depths.sort(key=lambda x: -x[1])
        
        for face_idx, _ in face_depths:
            face = faces[face_idx]
            color = face_colors[face_idx]
            
            points = []
            valid = True
            for vertex_idx in face:
                if projected[vertex_idx]:
                    points.append((projected[vertex_idx][0], projected[vertex_idx][1]))
                else:
                    valid = False
                    break
            
            if valid and len(points) >= 3:
                pygame.draw.polygon(screen, color, points)
                for i in range(len(points)):
                    start = points[i]
                    end = points[(i + 1) % len(points)]
                    pygame.draw.line(screen, BLACK, start, end, 2)

# Игрок от первого лица
class Player:
    def __init__(self):
        self.position = Vector3(0, 0, 0)
        self.health = 20
        self.score = 0
        self.level = 1
        self.yaw = 0  # Поворот по горизонтали
        self.pitch = 0  # Наклон по вертикали
    
    def get_camera_vectors(self):
        # Векторы направления камеры
        forward = Vector3(
            math.sin(self.yaw) * math.cos(self.pitch),
            math.sin(self.pitch),
            -math.cos(self.yaw) * math.cos(self.pitch)
        ).normalize()
        
        right = Vector3(
            math.cos(self.yaw),
            0,
            math.sin(self.yaw)
        ).normalize()
        
        up = Vector3(
            -math.sin(self.yaw) * math.sin(self.pitch),
            math.cos(self.pitch),
            math.cos(self.yaw) * math.sin(self.pitch)
        ).normalize()
        
        return forward, right, up
    
    def move(self, keys, dt):
        speed = 5 * dt
        forward, right, up = self.get_camera_vectors()
        
        if keys[pygame.K_w]:
            self.position = self.position + forward * speed
        if keys[pygame.K_s]:
            self.position = self.position + forward * -speed
        if keys[pygame.K_a]:
            self.position = self.position + right * -speed
        if keys[pygame.K_d]:
            self.position = self.position + right * speed
        if keys[pygame.K_q]:
            self.position.y += speed
        if keys[pygame.K_e]:
            self.position.y -= speed
        
        # Ограничение движения по Y (чтобы не улететь)
        self.position.y = max(-10, min(10, self.position.y))
    
    def rotate(self, mouse_rel):
        sensitivity = 0.002
        self.yaw += mouse_rel[0] * sensitivity
        self.pitch += mouse_rel[1] * sensitivity
        self.pitch = max(-math.pi/2, min(math.pi/2, self.pitch))

# Враг
class Enemy:
    def __init__(self, position, level):
        self.position = position
        self.level = level
        self.size = 8 + level * 1
        self.health = 3 + (level - 1) * 3
        self.max_health = self.health
        self.speed = 1 + level * 0.3
        self.shoot_timer = random.randint(100, 300) - level * 20
        self.shoot_delay = max(50, 300 - level * 25)
        self.color = (min(255, 50 + level * 40), max(0, 200 - level * 30), 50)
        self.cube = Cube3D(self.position, self.size, self.color)
        self.wobble = random.random() * math.pi * 2
    
    def draw(self, screen, camera_pos, forward, right, up):
        self.cube.position = self.position
        self.cube.color = self.color
        self.cube.size = self.size
        self.cube.draw(screen, camera_pos, forward, right, up)
    
    def update(self, player_pos, dt):
        self.wobble += dt
        # Плавное движение
        self.position.y += math.sin(self.wobble * 2) * 0.3
        
        # Движение к игроку, но сохраняя дистанцию
        to_player = player_pos - self.position
        distance = to_player.length()
        
        if distance > 30 and distance < 100:
            move_dir = to_player.normalize()
            self.position = self.position + move_dir * self.speed * dt
        
        self.shoot_timer -= 1
    
    def should_shoot(self):
        return self.shoot_timer <= 0
    
    def reset_shoot_timer(self):
        self.shoot_timer = self.shoot_delay

# 3D шар
class Ball3D:
    def __init__(self, position, velocity, color, radius=4):
        self.position = position
        self.velocity = velocity
        self.color = color
        self.radius = radius
        self.light_color = (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50))
    
    def update(self, dt):
        self.position = self.position + self.velocity * dt
    
    def draw(self, screen, camera_pos, forward, right, up):
        # Переводим в систему координат камеры
        cam_relative = self.position - camera_pos
        z = cam_relative.dot(forward)
        
        if z <= 0.1:  # За камерой
            return
        
        x = cam_relative.dot(right)
        y = cam_relative.dot(up)
        
        # Перспективная проекция
        scale = 400 / z
        screen_x = WIDTH // 2 + x * scale
        screen_y = HEIGHT // 2 - y * scale
        
        draw_radius = max(2, int(self.radius * scale))
        
        # Рисуем пиксельную сферу
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), draw_radius)
        pygame.draw.circle(screen, self.light_color, (int(screen_x), int(screen_y)), max(1, draw_radius - 2))
        pygame.draw.circle(screen, BLACK, (int(screen_x), int(screen_y)), draw_radius, 1)
    
    def is_off_screen(self, camera_pos):
        relative_pos = self.position - camera_pos
        return relative_pos.length() > 500

# Шар игрока
class PlayerBall(Ball3D):
    def __init__(self, position, direction):
        velocity = direction.normalize() * 15
        super().__init__(position, velocity, RED, 3)

# Шар врага
class EnemyBall(Ball3D):
    def __init__(self, position, target_pos):
        direction = (target_pos - position).normalize()
        velocity = direction * 8
        super().__init__(position, velocity, GREEN, 3)

# Отскочивший шар
class BouncedBall(Ball3D):
    def __init__(self, position, target_pos):
        direction = (target_pos - position).normalize()
        velocity = direction * 12
        super().__init__(position, velocity, (100, 255, 100), 4)

# Прицел
class Crosshair:
    def __init__(self):
        self.size = 20
    
    def draw(self, screen):
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        # Простой пиксельный прицел
        pygame.draw.line(screen, RED, (center_x - self.size, center_y), (center_x + self.size, center_y), 2)
        pygame.draw.line(screen, RED, (center_x, center_y - self.size), (center_x, center_y + self.size), 2)
        pygame.draw.circle(screen, RED, (center_x, center_y), 3, 1)

# Основная игра от первого лица
class Game:
    def __init__(self):
        self.player = Player()
        self.enemies = []
        self.player_balls = []
        self.enemy_balls = []
        self.bounced_balls = []
        self.crosshair = Crosshair()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.game_over = False
        self.wave = 1
        self.clock = pygame.time.Clock()
        self.spawn_enemies()
        
        # Блокировка мыши в центре экрана
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
    
    def spawn_enemies(self):
        self.enemies = []
        enemy_count = 3 + self.wave
        
        for i in range(enemy_count):
            angle = (i / enemy_count) * math.pi * 2
            radius = 20 + random.randint(10, 30)
            x = math.cos(angle) * radius
            z = math.sin(angle) * radius + 30
            y = random.randint(-5, 5)
            
            self.enemies.append(Enemy(Vector3(x, y, z), self.player.level))
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE and self.game_over:
                    self.__init__()
                if event.key == pygame.K_f:
                    # Выстрел
                    forward, _, _ = self.player.get_camera_vectors()
                    self.player_balls.append(PlayerBall(self.player.position, forward))
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Выстрел при клике
                forward, _, _ = self.player.get_camera_vectors()
                self.player_balls.append(PlayerBall(self.player.position, forward))
                
                # Проверка отбития вражеских шаров (по прицелу)
                for ball in self.enemy_balls[:]:
                    # Проецируем шар на экран
                    forward, right, up = self.player.get_camera_vectors()
                    cam_relative = ball.position - self.player.position
                    z = cam_relative.dot(forward)
                    
                    if z <= 0.1:
                        continue
                    
                    x = cam_relative.dot(right)
                    y = cam_relative.dot(up)
                    
                    scale = 400 / z
                    screen_x = WIDTH // 2 + x * scale
                    screen_y = HEIGHT // 2 - y * scale
                    
                    distance = math.sqrt((screen_x - WIDTH//2)**2 + (screen_y - HEIGHT//2)**2)
                    ball_radius = max(2, int(ball.radius * scale))
                    
                    if distance < ball_radius + 10:  # Область прицела
                        self.enemy_balls.remove(ball)
                        if self.enemies:
                            closest_enemy = min(self.enemies, 
                                              key=lambda e: (e.position - ball.position).length())
                            self.bounced_balls.append(BouncedBall(ball.position, closest_enemy.position))
        
        # Обработка вращения камеры
        mouse_rel = pygame.mouse.get_rel()
        self.player.rotate(mouse_rel)
        
        return True
    
    def update(self):
        if self.game_over:
            return
        
        dt = self.clock.tick(60) / 1000.0  # Delta time в секундах
        
        # Движение игрока
        keys = pygame.key.get_pressed()
        self.player.move(keys, dt)
        
        # Обновление врагов
        for enemy in self.enemies:
            enemy.update(self.player.position, dt)
            
            if enemy.should_shoot():
                # Враг стреляет в игрока
                self.enemy_balls.append(EnemyBall(enemy.position, self.player.position))
                enemy.reset_shoot_timer()
        
        # Обновление шаров игрока
        for ball in self.player_balls[:]:
            ball.update(dt)
            if ball.is_off_screen(self.player.position):
                self.player_balls.remove(ball)
                continue
            
            # Проверка столкновений с врагами
            for enemy in self.enemies[:]:
                distance = (ball.position - enemy.position).length()
                if distance < ball.radius + enemy.size/2:
                    enemy.health -= 1
                    if ball in self.player_balls:
                        self.player_balls.remove(ball)
                    
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                        self.player.score += 10 * self.player.level
                    
                    break
        
        # Обновление вражеских шаров
        for ball in self.enemy_balls[:]:
            ball.update(dt)
            if ball.is_off_screen(self.player.position):
                self.enemy_balls.remove(ball)
                continue
            
            # Проверка столкновений с игроком
            distance = (ball.position - self.player.position).length()
            if distance < ball.radius + 2:  # Маленький радиус столкновения с игроком
                self.player.health -= 1
                self.enemy_balls.remove(ball)
                
                if self.player.health <= 0:
                    self.game_over = True
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
        
        # Обновление отскочивших шаров
        for ball in self.bounced_balls[:]:
            ball.update(dt)
            if ball.is_off_screen(self.player.position):
                self.bounced_balls.remove(ball)
                continue
            
            # Проверка столкновений с врагами
            for enemy in self.enemies[:]:
                distance = (ball.position - enemy.position).length()
                if distance < ball.radius + enemy.size/2:
                    enemy.health -= 2
                    if ball in self.bounced_balls:
                        self.bounced_balls.remove(ball)
                    
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                        self.player.score += 15 * self.player.level
                    
                    break
        
        # Проверка завершения волны
        if not self.enemies:
            self.wave += 1
            self.player.level += 1
            self.spawn_enemies()
    
    def draw_3d_environment(self, screen):
        # Рисуем простой пол
        forward, right, up = self.player.get_camera_vectors()
        
        # Рисуем сетку пола
        grid_size = 10
        for i in range(-20, 21):
            for j in range(-20, 21):
                point = Vector3(i * grid_size, -5, j * grid_size)
                cam_relative = point - self.player.position
                z = cam_relative.dot(forward)
                
                if z <= 0.1:
                    continue
                
                x = cam_relative.dot(right)
                y = cam_relative.dot(up)
                
                scale = 400 / z
                screen_x = WIDTH // 2 + x * scale
                screen_y = HEIGHT // 2 - y * scale
                
                if 0 <= screen_x < WIDTH and 0 <= screen_y < HEIGHT:
                    brightness = max(0, min(255, int(255 * (1 - z/200))))
                    color = (brightness//3, brightness//3, brightness//2)
                    pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), 1)
    
    def draw(self):
        screen.fill(BLACK)
        
        # Получаем векторы камеры
        forward, right, up = self.player.get_camera_vectors()
        
        # Рисуем 3D окружение
        self.draw_3d_environment(screen)
        
        # Рисуем все 3D объекты
        for ball in self.player_balls:
            ball.draw(screen, self.player.position, forward, right, up)
        
        for ball in self.enemy_balls:
            ball.draw(screen, self.player.position, forward, right, up)
        
        for ball in self.bounced_balls:
            ball.draw(screen, self.player.position, forward, right, up)
        
        for enemy in self.enemies:
            enemy.draw(screen, self.player.position, forward, right, up)
        
        # Рисуем прицел
        self.crosshair.draw(screen)
        
        # Интерфейс
        health_text = self.small_font.render(f"Здоровье: {self.player.health}/20", True, WHITE)
        score_text = self.small_font.render(f"Счет: {self.player.score}", True, WHITE)
        level_text = self.small_font.render(f"Уровень: {self.player.level}", True, WHITE)
        wave_text = self.small_font.render(f"Волна: {self.wave}", True, WHITE)
        enemies_text = self.small_font.render(f"Врагов: {len(self.enemies)}", True, WHITE)
        
        screen.blit(health_text, (10, 10))
        screen.blit(score_text, (10, 35))
        screen.blit(level_text, (10, 60))
        screen.blit(wave_text, (10, 85))
        screen.blit(enemies_text, (10, 110))
        
        # Подсказки
        help_text = self.small_font.render("WASD: движение, Q/E: вверх/вниз, ЛКМ: стрелять/отбивать, ESC: выход", True, GRAY)
        screen.blit(help_text, (WIDTH // 2 - help_text.get_width() // 2, HEIGHT - 30))
        
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            game_over_text = self.font.render("ИГРА ОКОНЧЕНА!", True, RED)
            restart_text = self.font.render("Нажмите ПРОБЕЛ для перезапуска", True, WHITE)
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))
        
        pygame.display.flip()

# Основной игровой цикл
def main():
    game = Game()
    
    running = True
    while running:
        running = game.handle_events()
        game.update()
        game.draw()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()