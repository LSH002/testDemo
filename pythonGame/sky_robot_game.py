import pygame
import random
import sys
import math

# 初始化Pygame
pygame.init()
pygame.mixer.init()  # 初始化音频混合器

# 屏幕设置
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("天空机器人")

# 颜色
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# 游戏状态
MENU = 0
PLAYING = 1
GAME_OVER = 2

# 尝试加载音效
try:
    jump_sound = pygame.mixer.Sound("sounds/jump.wav")
    collect_sound = pygame.mixer.Sound("sounds/collect.wav")
    explosion_sound = pygame.mixer.Sound("sounds/explosion.wav")
    power_up_sound = pygame.mixer.Sound("sounds/power_up.wav")
    game_over_sound = pygame.mixer.Sound("sounds/game_over.wav")
    has_sound = True
except:
    has_sound = False

# 机器人类
class Robot:
    def __init__(self):
        self.width = 50
        self.height = 50
        self.x = 100
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.gravity = 0.5
        self.lift = -10
        self.color = BLUE
        self.shield_active = False
        self.shield_timer = 0
        self.boost_active = False
        self.boost_timer = 0
        self.lives = 3
        self.invulnerable = False
        self.invulnerable_timer = 0
    
    def show(self):
        # 绘制机器人主体
        if self.invulnerable and pygame.time.get_ticks() % 200 < 100:
            # 无敌状态闪烁
            pass
        else:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
            # 绘制机器人眼睛
            pygame.draw.circle(screen, WHITE, (self.x + 35, self.y + 15), 8)
            pygame.draw.circle(screen, BLACK, (self.x + 35, self.y + 15), 4)
            # 绘制机器人天线
            pygame.draw.line(screen, BLACK, (self.x + 25, self.y), (self.x + 25, self.y - 15), 3)
            pygame.draw.circle(screen, RED, (self.x + 25, self.y - 15), 5)
            
            # 如果有护盾，绘制护盾效果
            if self.shield_active:
                pygame.draw.circle(screen, BLUE, (self.x + self.width//2, self.y + self.height//2), 
                                 self.width//2 + 10, 3)
            
            # 如果有加速，绘制加速效果
            if self.boost_active:
                for i in range(3):
                    offset = i * 5
                    pygame.draw.line(screen, ORANGE, 
                                    (self.x - 10 - offset, self.y + self.height//4),
                                    (self.x - 20 - offset, self.y + self.height//2), 3)
                    pygame.draw.line(screen, ORANGE, 
                                    (self.x - 10 - offset, self.y + 3*self.height//4),
                                    (self.x - 20 - offset, self.y + self.height//2), 3)
    
    def update(self):
        self.velocity += self.gravity
        self.y += self.velocity
        
        # 护盾计时器
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False
        
        # 加速计时器
        if self.boost_active:
            self.boost_timer -= 1
            if self.boost_timer <= 0:
                self.boost_active = False
        
        # 无敌计时器
        if self.invulnerable:
            self.invulnerable_timer -= 1
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
        
        # 防止机器人飞出屏幕
        if self.y > SCREEN_HEIGHT - self.height:
            self.y = SCREEN_HEIGHT - self.height
            self.velocity = 0
        if self.y < 0:
            self.y = 0
            self.velocity = 0
    
    def jump(self):
        self.velocity = self.lift
        if has_sound:
            jump_sound.play()

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def activate_shield(self):
        self.shield_active = True
        self.shield_timer = 300  # 持续5秒(60帧/秒)
        if has_sound:
            power_up_sound.play()
    
    def activate_boost(self):
        self.boost_active = True
        self.boost_timer = 180  # 持续3秒
        if has_sound:
            power_up_sound.play()
    
    def hit(self):
        if self.shield_active:
            self.shield_active = False
            return False
        elif self.invulnerable:
            return False
        else:
            self.lives -= 1
            self.invulnerable = True
            self.invulnerable_timer = 120  # 2秒无敌时间
            if has_sound:
                explosion_sound.play()
            return self.lives <= 0

# 障碍物基类
class Obstacle:
    def __init__(self, speed):
        self.width = 50
        self.x = SCREEN_WIDTH
        self.speed = speed
        self.passed = False
    
    def update(self, boost_speed=0):
        self.x -= (self.speed + boost_speed)
    
    def offscreen(self):
        return self.x < -self.width
    
    def pass_robot(self, robot):
        if not self.passed and self.x + self.width < robot.x:
            self.passed = True
            return True
        return False

# 常规障碍物类
class PipeObstacle(Obstacle):
    def __init__(self, speed):
        super().__init__(speed)
        self.gap = 180
        self.top_height = random.randint(50, SCREEN_HEIGHT - self.gap - 50)
        self.bottom_y = self.top_height + self.gap
        self.color = GREEN
    
    def show(self):
        # 绘制上方障碍物
        pygame.draw.rect(screen, self.color, (self.x, 0, self.width, self.top_height))
        # 绘制下方障碍物
        pygame.draw.rect(screen, self.color, (self.x, self.bottom_y, self.width, SCREEN_HEIGHT - self.bottom_y))
    
    def hit(self, robot):
        if robot.shield_active:
            return False
            
        robot_rect = robot.get_rect()
        top_rect = pygame.Rect(self.x, 0, self.width, self.top_height)
        bottom_rect = pygame.Rect(self.x, self.bottom_y, self.width, SCREEN_HEIGHT - self.bottom_y)
        
        return robot_rect.colliderect(top_rect) or robot_rect.colliderect(bottom_rect)

# 移动障碍物类
class MovingObstacle(Obstacle):
    def __init__(self, speed):
        super().__init__(speed)
        self.height = 100
        self.y = random.randint(50, SCREEN_HEIGHT - self.height - 50)
        self.color = PURPLE
        self.direction = random.choice([-1, 1])
        self.move_speed = 2
    
    def show(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
    
    def update(self, boost_speed=0):
        super().update(boost_speed)
        self.y += self.direction * self.move_speed
        
        # 碰到边缘就改变方向
        if self.y <= 0 or self.y + self.height >= SCREEN_HEIGHT:
            self.direction *= -1
    
    def hit(self, robot):
        if robot.shield_active:
            return False
            
        robot_rect = robot.get_rect()
        obstacle_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        return robot_rect.colliderect(obstacle_rect)

# 旋转障碍物类
class SpinningObstacle(Obstacle):
    def __init__(self, speed):
        super().__init__(speed)
        self.radius = 80
        self.center_y = random.randint(self.radius + 50, SCREEN_HEIGHT - self.radius - 50)
        self.angle = 0
        self.color = ORANGE
        self.rotation_speed = 0.05
        self.blade_length = 70
        self.num_blades = 3
        
    def show(self):
        # 绘制中心
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.center_y)), 20)
        
        # 绘制旋转的叶片
        for i in range(self.num_blades):
            angle = self.angle + (2 * math.pi / self.num_blades) * i
            end_x = self.x + math.cos(angle) * self.blade_length
            end_y = self.center_y + math.sin(angle) * self.blade_length
            pygame.draw.line(screen, self.color, (int(self.x), int(self.center_y)), 
                             (int(end_x), int(end_y)), 8)
    
    def update(self, boost_speed=0):
        super().update(boost_speed)
        self.angle += self.rotation_speed
        
    def hit(self, robot):
        if robot.shield_active:
            return False
            
        robot_rect = robot.get_rect()
        # 检测与中心的碰撞
        center_rect = pygame.Rect(self.x - 20, self.center_y - 20, 40, 40)
        if robot_rect.colliderect(center_rect):
            return True
            
        # 检测与叶片的碰撞
        robot_center = (robot.x + robot.width/2, robot.y + robot.height/2)
        for i in range(self.num_blades):
            angle = self.angle + (2 * math.pi / self.num_blades) * i
            end_x = self.x + math.cos(angle) * self.blade_length
            end_y = self.center_y + math.sin(angle) * self.blade_length
            
            # 简化的线段碰撞检测
            distance = point_to_line_distance(robot_center, (self.x, self.center_y), (end_x, end_y))
            if distance < (robot.width + robot.height) / 4:
                return True
                
        return False

# 点到线段的距离计算
def point_to_line_distance(point, line_start, line_end):
    x, y = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    # 线段长度的平方
    l2 = (x2 - x1)**2 + (y2 - y1)**2
    
    # 如果线段实际是一个点，则返回点到该点的距离
    if l2 == 0:
        return math.sqrt((x - x1)**2 + (y - y1)**2)
    
    # 考虑点到线的投影是否在线段内
    t = max(0, min(1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / l2))
    
    # 计算投影点
    projection_x = x1 + t * (x2 - x1)
    projection_y = y1 + t * (y2 - y1)
    
    # 返回点到投影点的距离
    return math.sqrt((x - projection_x)**2 + (y - projection_y)**2)

# 物品基类
class Item:
    def __init__(self):
        self.width = 25
        self.height = 25
        self.x = SCREEN_WIDTH
        self.y = random.randint(50, SCREEN_HEIGHT - 50)
        self.speed = 3
        self.collected = False
    
    def update(self, boost_speed=0):
        self.x -= (self.speed + boost_speed)
    
    def offscreen(self):
        return self.x < -self.width
    
    def collect(self, robot):
        if self.collected:
            return False
        
        robot_rect = robot.get_rect()
        item_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        if robot_rect.colliderect(item_rect):
            self.collected = True
            if has_sound:
                collect_sound.play()
            return True
        return False

# 普通奖励
class Reward(Item):
    def __init__(self):
        super().__init__()
        self.color = RED
    
    def show(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.line(screen, WHITE, (self.x + 5, self.y + self.height//2), 
                        (self.x + self.width - 5, self.y + self.height//2), 2)
        pygame.draw.line(screen, WHITE, (self.x + self.width//2, self.y + 5), 
                        (self.x + self.width//2, self.y + self.height - 5), 2)

# 护盾物品
class Shield(Item):
    def __init__(self):
        super().__init__()
        self.color = BLUE
    
    def show(self):
        pygame.draw.circle(screen, self.color, (int(self.x + self.width//2), int(self.y + self.height//2)), 
                          self.width//2)
        pygame.draw.circle(screen, WHITE, (int(self.x + self.width//2), int(self.y + self.height//2)), 
                          self.width//2, 2)

# 加速物品
class Boost(Item):
    def __init__(self):
        super().__init__()
        self.color = YELLOW
    
    def show(self):
        # 绘制一个加速图标
        pygame.draw.polygon(screen, self.color, [
            (self.x, self.y + self.height//2),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height)
        ])

# 生命物品
class Life(Item):
    def __init__(self):
        super().__init__()
        self.color = RED
    
    def show(self):
        # 绘制一个心形
        pygame.draw.circle(screen, self.color, (int(self.x + self.width//3), int(self.y + self.height//3)), 
                          self.width//3)
        pygame.draw.circle(screen, self.color, (int(self.x + 2*self.width//3), int(self.y + self.height//3)), 
                          self.width//3)
        pygame.draw.polygon(screen, self.color, [
            (self.x, self.y + self.height//3),
            (self.x + self.width, self.y + self.height//3),
            (self.x + self.width//2, self.y + self.height)
        ])

# 粒子效果
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 6)
        self.speed_x = random.uniform(-2, 2)
        self.speed_y = random.uniform(-2, 2)
        self.life = random.randint(20, 40)
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 1
        self.size = max(0, self.size - 0.1)
    
    def show(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))
    
    def is_dead(self):
        return self.life <= 0

# 绘制云朵
def draw_clouds(frame_count):
    for i in range(0, SCREEN_WIDTH, 200):
        offset = (frame_count // 2) % 200
        cloud_x = (i - offset) % (SCREEN_WIDTH + 200) - 100
        pygame.draw.ellipse(screen, WHITE, (cloud_x, 50, 100, 50))
        pygame.draw.ellipse(screen, WHITE, (cloud_x + 25, 25, 70, 60))
        pygame.draw.ellipse(screen, WHITE, (cloud_x + 50, 40, 80, 50))

# 绘制背景星星
def draw_stars(frame_count):
    for i in range(30):
        x = (i * 30 + frame_count // 4) % SCREEN_WIDTH
        y = (i * 25) % SCREEN_HEIGHT
        size = 1 + math.sin(frame_count * 0.05 + i) * 1
        brightness = 128 + int(math.sin(frame_count * 0.02 + i * 0.5) * 127)
        color = (brightness, brightness, brightness)
        pygame.draw.circle(screen, color, (int(x), int(y)), int(size))

# 主游戏函数
def game():
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)
    
    # 游戏状态
    game_state = MENU
    
    # 菜单选项
    menu_options = ["开始游戏", "退出"]
    menu_selection = 0
    
    # 游戏变量
    robot = None
    obstacles = []
    items = []
    particles = []
    frame_count = 0
    score = 0
    high_score = 0
    level = 1
    level_threshold = 10
    obstacle_speed = 3
    spawn_rate = 120  # 帧数
    
    running = True
    while running:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if game_state == MENU:
                    if event.key == pygame.K_UP:
                        menu_selection = (menu_selection - 1) % len(menu_options)
                    elif event.key == pygame.K_DOWN:
                        menu_selection = (menu_selection + 1) % len(menu_options)
                    elif event.key == pygame.K_RETURN:
                        if menu_selection == 0:  # 开始游戏
                            game_state = PLAYING
                            # 初始化游戏
                            robot = Robot()
                            obstacles = [PipeObstacle(obstacle_speed)]
                            items = []
                            particles = []
                            frame_count = 0
                            score = 0
                            level = 1
                            obstacle_speed = 3
                            spawn_rate = 120
                        elif menu_selection == 1:  # 退出
                            pygame.quit()
                            sys.exit()
                            
                elif game_state == PLAYING:
                    if event.key == pygame.K_SPACE:
                        robot.jump()
                    elif event.key == pygame.K_ESCAPE:
                        game_state = MENU
                        
                elif game_state == GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        game_state = MENU
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
        
        # 绘制背景
        screen.fill(SKY_BLUE)
        
        # 根据游戏状态处理
        if game_state == MENU:
            # 绘制标题
            draw_clouds(frame_count)
            title_font = pygame.font.SysFont(None, 72)
            title_text = title_font.render("天空机器人", True, BLUE)
            screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))
            
            # 绘制高分
            if high_score > 0:
                high_score_text = font.render("最高分数: " + str(high_score), True, BLACK)
                screen.blit(high_score_text, (SCREEN_WIDTH//2 - high_score_text.get_width()//2, 200))
            
            # 绘制菜单选项
            for i, option in enumerate(menu_options):
                color = RED if i == menu_selection else BLACK
                option_text = font.render(option, True, color)
                screen.blit(option_text, (SCREEN_WIDTH//2 - option_text.get_width()//2, 300 + i * 50))
                
            # 绘制帮助信息
            help_text1 = small_font.render("使用 空格键 让机器人飞行", True, BLACK)
            help_text2 = small_font.render("躲避障碍物并收集物品", True, BLACK)
            help_text3 = small_font.render("红色物品: +5分  蓝色物品: 护盾  黄色物品: 加速  心形: 额外生命", True, BLACK)
            screen.blit(help_text1, (SCREEN_WIDTH//2 - help_text1.get_width()//2, 450))
            screen.blit(help_text2, (SCREEN_WIDTH//2 - help_text2.get_width()//2, 480))
            screen.blit(help_text3, (SCREEN_WIDTH//2 - help_text3.get_width()//2, 510))
                
        elif game_state == PLAYING:
            # 更新游戏状态
            frame_count += 1
            
            # 难度随分数提高
            current_level = 1 + score // level_threshold
            if current_level > level:
                level = current_level
                obstacle_speed += 0.5
                if spawn_rate > 60:
                    spawn_rate -= 10
            
            # 生成障碍物
            if frame_count % spawn_rate == 0:
                # 随机选择障碍物类型
                obstacle_type = random.choices([PipeObstacle, MovingObstacle, SpinningObstacle], 
                                             weights=[0.5, 0.3, 0.2], k=1)[0]
                obstacles.append(obstacle_type(obstacle_speed))
            
            # 生成物品
            if frame_count % 180 == 0:
                # 随机选择物品类型
                item_type = random.choices([Reward, Shield, Boost, Life], 
                                         weights=[0.6, 0.2, 0.15, 0.05], k=1)[0]
                items.append(item_type())
            
            # 更新机器人
            robot.update()
            
            # 计算加速值
            boost_speed = 2 if robot.boost_active else 0
            
            # 更新障碍物
            for obstacle in obstacles[:]:
                obstacle.update(boost_speed)
                
                # 检查碰撞
                if obstacle.hit(robot):
                    game_over = robot.hit()
                    
                    # 生成粒子效果
                    for _ in range(20):
                        particles.append(Particle(robot.x + robot.width//2, robot.y + robot.height//2, RED))
                    
                    if game_over:
                        if has_sound:
                            game_over_sound.play()
                        game_state = GAME_OVER
                        high_score = max(high_score, score)
                
                # 检查是否通过障碍物
                if obstacle.pass_robot(robot):
                    score += 1
                    # 生成粒子效果
                    for _ in range(5):
                        particles.append(Particle(obstacle.x, SCREEN_HEIGHT//2, GREEN))
                
                # 移除屏幕外的障碍物
                if obstacle.offscreen():
                    obstacles.remove(obstacle)
            
            # 更新物品
            for item in items[:]:
                item.update(boost_speed)
                
                # 检查是否收集物品
                if item.collect(robot):
                    # 根据物品类型执行对应效果
                    if isinstance(item, Reward):
                        score += 5
                    elif isinstance(item, Shield):
                        robot.activate_shield()
                    elif isinstance(item, Boost):
                        robot.activate_boost()
                    elif isinstance(item, Life):
                        robot.lives += 1
                    
                    # 生成粒子效果
                    for _ in range(15):
                        particles.append(Particle(item.x, item.y, item.color))
                    
                    items.remove(item)
                
                # 移除屏幕外的物品
                elif item.offscreen():
                    items.remove(item)
            
            # 更新粒子
            for particle in particles[:]:
                particle.update()
                if particle.is_dead():
                    particles.remove(particle)
            
            # 绘制背景
            draw_clouds(frame_count)
            
            # 绘制机器人
            robot.show()
            
            # 绘制障碍物
            for obstacle in obstacles:
                obstacle.show()
                
            # 绘制物品
            for item in items:
                item.show()
            
            # 绘制粒子
            for particle in particles:
                particle.show()
            
            # 绘制分数
            score_text = font.render("得分: " + str(score), True, BLACK)
            screen.blit(score_text, (10, 10))
            
            # 绘制生命值
            for i in range(robot.lives):
                pygame.draw.circle(screen, RED, (SCREEN_WIDTH - 30 - i * 30, 30), 10)
                
            # 绘制等级
            level_text = font.render("等级: " + str(level), True, BLACK)
            screen.blit(level_text, (10, 50))
            
            # 绘制道具状态
            if robot.shield_active:
                shield_text = small_font.render("护盾: " + str(robot.shield_timer // 60 + 1) + "s", True, BLUE)
                screen.blit(shield_text, (SCREEN_WIDTH - 100, 60))
            
            if robot.boost_active:
                boost_text = small_font.render("加速: " + str(robot.boost_timer // 60 + 1) + "s", True, YELLOW)
                screen.blit(boost_text, (SCREEN_WIDTH - 100, 90))
                
        elif game_state == GAME_OVER:
            # 游戏结束画面
            screen.fill(BLACK)
            draw_stars(frame_count)
            
            game_over_text = font.render("游戏结束!", True, WHITE)
            score_text = font.render("得分: " + str(score), True, WHITE)
            high_score_text = font.render("最高分数: " + str(high_score), True, WHITE)
            restart_text = font.render("按空格键返回菜单", True, WHITE)
            exit_text = font.render("按ESC键退出游戏", True, WHITE)
            
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 100))
            screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
            screen.blit(high_score_text, (SCREEN_WIDTH//2 - high_score_text.get_width()//2, SCREEN_HEIGHT//2))
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 50))
            screen.blit(exit_text, (SCREEN_WIDTH//2 - exit_text.get_width()//2, SCREEN_HEIGHT//2 + 100))
        
        # 更新显示
        pygame.display.flip()
        frame_count += 1
        clock.tick(60)

# 运行游戏
if __name__ == "__main__":
    game() 