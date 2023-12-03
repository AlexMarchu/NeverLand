import pygame
import os
import random

pygame.init()
# set rate
clock = pygame.time.Clock()
FPS = 60

# define game variables
GRAVITY = 0.75
TILE_SIZE = 40

# define font
RD = pygame.font.Font('assets/fonts/PressStart2P-Regular.ttf', 20)

# loading images
ammo_image = pygame.image.load('assets/images/icons/ammo_image.png')
ammo_image = pygame.transform.scale(ammo_image, (TILE_SIZE, TILE_SIZE))
health_image = pygame.image.load('assets/images/icons/health_image.png')
health_image = pygame.transform.scale(health_image, (TILE_SIZE, TILE_SIZE))
grenade_image = pygame.image.load('assets/images/icons/grenade_image.png')
grenade_image = pygame.transform.scale(grenade_image, (TILE_SIZE, TILE_SIZE))

item_boxes = {
    'Health': health_image,
    'Ammo': ammo_image,
    'Grenade': grenade_image
}

# create sprite groups
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()


class Soldier(pygame.sprite.Sprite):
    def __init__(self, character_type, x, y, scale, speed, ammo, grenades):
        super().__init__()
        self.character_type = character_type

        self.alive = True
        self.speed = speed
        self.shoot_cooldown = 0
        self.ammo = ammo
        self.start_ammo = ammo
        self.grenades_ammo = grenades
        self.health = 100
        self.max_health = self.health
        self.direction = 1
        self.flip = False
        self.jump = False
        self.in_air = False
        self.velocity_y = 0
        self.moving_left = False
        self.moving_right = False
        self.shoot = False
        self.grenade_thrown = False
        self.grenade = False
        self.animation_list = list()
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.action = 0

        # create ai variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20, )
        self.idling = False
        self.idling_counter = 0

        # loading animations
        animation_list = ['idle', 'running', 'jump', 'death']
        for animation in animation_list:
            tmp = list()
            frames_count = len(os.listdir(f'assets/images/{self.character_type}/{animation}'))
            for i in range(1, frames_count + 1):
                img = pygame.image.load(f'assets/images/{self.character_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                tmp.append(img)
            self.animation_list.append(tmp)
            tmp = list()

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = x, y

    def update(self):
        self.update_animation()
        self.check_alive()
        # update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_right, moving_left):
        dx = 0
        dy = 0

        # moving left or right
        if moving_left:
            dx = -self.speed
            self.direction = -1
            self.flip = True

        if moving_right:
            dx = self.speed
            self.direction = 1
            self.flip = False

        # jumping
        if self.jump and not self.in_air:
            self.velocity_y = -11
            self.jump = False
            self.in_air = True

        # apply gravity
        self.velocity_y += GRAVITY
        dy += self.velocity_y

        # check collision with floor
        if self.rect.bottom + dy > 300:
            dy = 300 - self.rect.bottom
            self.in_air = False

        self.rect.x += dx
        self.rect.y += dy

    def shoot_(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            bullet = Bullet(self.rect.centerx + (0.7 * self.rect.size[0] * self.direction),
                            self.rect.centery, self.direction)
            bullet_group.add(bullet)
            self.ammo -= 1

    def ai(self):
        if self.alive and game.player.alive:
            if not self.idling and random.randint(1, 200) == 1:
                self.update_action(0)  # 0 -- idle
                self.idling = True
                self.idling_counter = 50

            # check if the AI near the player
            if self.vision.colliderect(game.player.rect):
                # stop running
                self.update_action(0)  # 0 -- idle
                # start shoot
                self.shoot_()
            else:
                if not self.idling:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_right, ai_moving_left)
                    self.update_action(1)  # 1 -- run
                    self.move_counter += 1

                    # update AI vision rectangle as the enemy moves
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                    # pygame.draw.rect(game.screen, 'red', self.vision)

                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False
                        self.update_action(1)  # 1 -- run

    def grenade_(self):
        grenade = Grenade(self.rect.centerx + (0.5 * self.rect.size[0] * self.direction),
                          self.rect.top, self.direction)
        grenade_group.add(grenade)
        self.grenades_ammo -= 1
        self.grenade_thrown = True

    def update_animation(self):
        ANIMATION_COOLDOWN = 110
        self.image = self.animation_list[self.action][self.frame_index]

        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()

        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        if self.action != new_action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    def draw(self):
        if not self.alive:
            game.screen.blit(self.image, self.rect)
        else:
            game.screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.direction = direction
        self.speed = 10
        self.image = game.bullet_image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        # move bullet
        self.rect.x += (self.speed * self.direction)

        # check if bullet has gone off-screen
        if self.rect.right < 0 or self.rect.left > game.width:
            self.kill()

        # check collision with characters
        if pygame.sprite.spritecollide(game.player, bullet_group, False):
            if game.player.alive:
                game.player.health -= 15
                self.kill()
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    self.kill()


class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.explosion_timer = 100
        self.velocity_y = -11
        self.direction = direction
        self.speed = 7
        self.image = game.grenade_image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.velocity_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.velocity_y

        # check collision with the floor
        if self.rect.bottom + dy > 300:
            dy = 300 - self.rect.bottom
            self.speed = 0

        # check if grenade has gone off-screen
        if self.rect.right > game.width or self.rect.left < 0:
            # self.kill()
            self.direction *= -1
            dx = self.direction * self.speed

        # update grenade position
        self.rect.x += dx
        self.rect.y += dy

        # countdown timer
        self.explosion_timer -= 1

        if self.explosion_timer <= 0:
            self.kill()
            explosion = Explosion(self.rect.x, self.rect.y, 0.65)
            explosion_group.add(explosion)
            # damage to anyone who is nearby
            if abs(self.rect.x - game.player.rect.x) < TILE_SIZE and \
                abs(self.rect.y - game.player.rect.y) < TILE_SIZE:
                game.player.health -= 100
            elif abs(self.rect.x - game.player.rect.x) < TILE_SIZE * 2 and \
                abs(self.rect.y - game.player.rect.y) < TILE_SIZE * 2:
                game.player.health -= 50
            elif abs(self.rect.x - game.player.rect.x) < TILE_SIZE * 3 and \
                abs(self.rect.y - game.player.rect.y) < TILE_SIZE * 3:
                game.player.health -= 25

            for enemy in enemy_group:
                if abs(self.rect.x - enemy.rect.x) < TILE_SIZE and \
                        abs(self.rect.y - enemy.rect.y) < TILE_SIZE:
                    enemy.health -= 100
                elif abs(self.rect.x - enemy.rect.x) < TILE_SIZE * 2 and \
                        abs(self.rect.y - enemy.rect.y) < TILE_SIZE * 2:
                    enemy.health -= 50
                elif abs(self.rect.x - enemy.rect.x) < TILE_SIZE * 3 and \
                        abs(self.rect.y - enemy.rect.y) < TILE_SIZE * 3:
                    enemy.health -= 25


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        super().__init__()
        self.images = list()

        for i in range(1, 10):
            img = pygame.image.load(f'assets/images/explosions/{i}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)

        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        EXPLOSION_SPEED = 4

        # update explosion animation
        self.counter += 1
        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            # if the animation is complete then delete the explosion
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]


class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        super().__init__()
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        # check if the player has picked up the box
        if pygame.sprite.collide_rect(self, game.player):
            # check what kind of box it was
            if self.item_type == 'Health':
                game.player.health = min(game.player.max_health, game.player.health + 25)
            elif self.item_type == 'Ammo':
                game.player.ammo += 10
            elif self.item_type == 'Grenade':
                game.player.grenades_ammo += 3
            # delete the item box
            self.kill()


class HealthBar:
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        self.health = health

        pygame.draw.rect(game.screen, 'black', (self.x - 3, self.y - 3, 156, 26))
        pygame.draw.rect(game.screen, 'red', (self.x, self.y, 150, 20))
        pygame.draw.rect(game.screen, 'green', (self.x, self.y, 150 * self.health / self.max_health, 20))


class Game:
    def __init__(self):

        pygame.display.set_caption('Our Game')

        self.width = 800
        self.height = self.width // 100 * 80

        self.screen = pygame.display.set_mode((self.width, self.height))

        # temp - creating boxes
        self.health_box = ItemBox('Health', 100, 300 - TILE_SIZE)
        item_box_group.add(self.health_box)
        self.ammo_box = ItemBox('Ammo', 400, 300 - TILE_SIZE)
        item_box_group.add(self.ammo_box)
        self.grenade_box = ItemBox('Grenade', 500, 300 - TILE_SIZE)
        item_box_group.add(self.grenade_box)

        # creating soldiers
        self.player = Soldier('player', 300, 200, 3, 4, 20, 5)
        self.enemy = Soldier('enemy', 450, 250, 3, 2, 20, 0)
        self.enemy_2 = Soldier('enemy', 550, 250, 3, 2, 20, 0)
        enemy_group.add(self.enemy)
        enemy_group.add(self.enemy_2)

        self.health_bar = HealthBar(10, 10, self.player.health, self.player.max_health)

        self.bullet_image = pygame.image.load('assets/images/icons/bullet.png').convert_alpha()
        self.grenade_image = pygame.image.load('assets/images/icons/grenade.png').convert_alpha()

        self.running = True

    def draw_bg(self):
        self.screen.fill((180, 191, 255))
        pygame.draw.line(self.screen, 'red', (0, 300), (self.width, 300))

    def draw_text(self, text, font, colour, x, y):
        data = font.render(text, True, colour)
        self.screen.blit(data, (x, y))

    def run(self):

        while self.running:

            clock.tick(FPS)
            self.draw_bg()

            # show info
            self.draw_text(f'ПАТРОНЫ: {self.player.ammo}', RD, 'white', 10, 40)
            self.draw_text(f'ГРАНАТЫ: {self.player.grenades_ammo}', RD, 'white', 10, 70)

            self.health_bar.draw(self.player.health)

            if self.player.alive:
                if self.player.shoot:
                    self.player.shoot_()
                elif self.player.grenade and not self.player.grenade_thrown and self.player.grenades_ammo > 0:
                    self.player.grenade_()
                if self.player.in_air:
                    self.player.update_action(2)  # 2 -- run
                elif self.player.moving_left or self.player.moving_right:
                    self.player.update_action(1)  # 1 -- run
                else:
                    self.player.update_action(0)  # 0 -- idle

            self.player.update()
            self.player.draw()

            # update and draw groups
            bullet_group.update()
            bullet_group.draw(self.screen)

            grenade_group.update()
            grenade_group.draw(self.screen)

            explosion_group.update()
            explosion_group.draw(self.screen)

            item_box_group.update()
            item_box_group.draw(self.screen)

            for enemy in enemy_group:
                enemy.update()
                enemy.ai()
                enemy.draw()

            self.player.move(self.player.moving_right, self.player.moving_left)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.player.moving_left = True
                    if event.key == pygame.K_d:
                        self.player.moving_right = True
                    if event.key == pygame.K_SPACE:
                        self.player.shoot = True
                    if event.key == pygame.K_q:
                        self.player.grenade = True
                    if event.key == pygame.K_w and self.player.alive and not self.player.in_air:
                        self.player.jump = True
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        pygame.quit()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.player.moving_left = False
                    if event.key == pygame.K_d:
                        self.player.moving_right = False
                    if event.key == pygame.K_SPACE:
                        self.player.shoot = False
                    if event.key == pygame.K_q:
                        self.player.grenade = False
                        self.player.grenade_thrown = False

            pygame.display.update()


game = Game()
game.run()
