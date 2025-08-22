import pygame
import time
import random
import astar


# === CONSTANTES & CONFIG ===
pygame.init()
screen_width = 350
screen_height = 400
white = (255, 255, 255)

finish = False
fps = 3  #on l'a choisi bas pour bien voir les déplacements de la grenouille

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Frogger-AI-bot avec A*')
clock = pygame.time.Clock()

backgroundImage = pygame.image.load('images/background.gif')

# === GROUPES DE SPRITES ===
#sprite = objet graphique qui se déplace à l'écran
all_sprites = pygame.sprite.Group()
cars = pygame.sprite.Group()  #  groupe dédié pour les voitures
logs = pygame.sprite.Group()   # groupe dédié pour les bûches
turtles = pygame.sprite.Group()
frogs = pygame.sprite.Group() # Contiendra notre unique grenouille

# === CHARGEMENT DES IMAGES ===
frog_img = pygame.image.load('images/frog10.gif')
frog_dead_img = pygame.image.load('images/frog11.png')

yellowCar = pygame.image.load('images/yellowCar.gif')
dozer = pygame.image.load('images/dozer.gif')
purpleCar = pygame.image.load('images/purpleCar.gif')
greenCar = pygame.image.load('images/greenCar.gif')
truck = pygame.image.load('images/truck.gif')

logShort = pygame.image.load('images/logShort.gif')
logMedium = pygame.image.load('images/logMedium.gif')
logLong = pygame.image.load('images/logLong.gif')

twoTurtles = pygame.image.load('images/turtletwo.gif')
twoTurtlesDive = pygame.image.load('images/turtletwodown.gif')
threeTurtles = pygame.image.load('images/turtlethree.gif')
threeTurtlesDive = pygame.image.load('images/turtlethreedown.gif')

turtleCounter = 0


class Turtle(pygame.sprite.Sprite):
    def __init__(self, canDive, size, startX, startY, speed):
        pygame.sprite.Sprite.__init__(self)
        self.canDive = canDive
        self.size = size
        self.image = twoTurtles if size == 2 else threeTurtles
        self.rect = self.image.get_rect(topleft=(startX, startY))
        self.speed = speed
        self.state = 0  # 0 - not diving, 1 - diving

    def update(self):
        self.rect.x += self.speed
        if self.speed < 0 and self.rect.right < 0:
            self.rect.left = screen_width
        self.collision()

    def collision(self):
        for f in frogs:
            if f.rect.colliderect(self) and not f.dead:
                if self.state == 1:
                    f.die()
                else:
                    f.rect.x += self.speed


class Log(pygame.sprite.Sprite):
    def __init__(self, startX, startY, size, speed):
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        if self.size == 'short': self.image = logShort
        elif self.size == 'medium': self.image = logMedium
        else: self.image = logLong
        self.rect = self.image.get_rect(topleft=(startX, startY))
        self.speed = speed

    def update(self):
        self.rect.x += self.speed
        if self.speed > 0 and self.rect.left > screen_width:
            self.rect.right = 0
        self.collision()

    def collision(self):
        for f in frogs:
            if f.rect.colliderect(self) and not f.dead:
                f.rect.x += self.speed


class Car(pygame.sprite.Sprite):
    def __init__(self, startX, startY, img, speed, direction):
        pygame.sprite.Sprite.__init__(self)
        if img == 'yellow': self.image = yellowCar
        elif img == 'green': self.image = greenCar
        elif img == 'truck': self.image = truck
        elif img == 'dozer': self.image = dozer
        elif img == 'purple': self.image = purpleCar
        self.rect = self.image.get_rect(topleft=(startX, startY))
        self.speed = speed * direction

    def update(self):
        self.rect.x += self.speed
        if self.speed > 0 and self.rect.left > screen_width:
            self.rect.right = 0
        elif self.speed < 0 and self.rect.right < 0:
            self.rect.left = screen_width
        self.collision()

    def collision(self):
        collided_frogs = pygame.sprite.spritecollide(self, frogs, False)
        for f in collided_frogs:
            if not f.dead:
                f.die()



class Frog(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = frog_img
        self.rect = self.image.get_rect()
        self.reset()
        
        # Attributs pour A*
        self.path = []      # Le chemin à suivre, généré par A*
        self.path_step = 0  # L'étape actuelle dans le chemin

    # Réinitialise la position et l'état de la grenouille
    def reset(self):
        self.rect.centerx = screen_width / 2
        self.rect.y = 350
        self.dead = False
        self.image = frog_img
        self.path = []
        self.path_step = 0
        print("Grenouille réinitialisée.")


    # Met à jour la grenouille
    def update(self):
        if self.dead:
            return

        if self.path and self.path_step < len(self.path):
            next_pos = self.path[self.path_step]
            # Les positions dans le chemin seront des coordonnées de grille
            # Nous les convertissons en pixels. La taille d'une case est 25x25
            self.rect.x = next_pos[0] * 25
            self.rect.y = next_pos[1] * 25
            self.path_step += 1
        
        # Vérification des conditions de mort ou de victoire
        self.check_status()

    # Vérifie si la grenouille est dans l'eau, hors de l'écran ou a gagné
    def check_status(self):
        # Hors de l'écran
        if self.rect.right < 0 or self.rect.left > screen_width:
            self.die()
            
        # Dans la rivière 
        if self.rect.y <= 175 and self.rect.y > 50:
            on_safe_surface = False
            # Vérifie si elle est sur une bûche ou une tortue
            for surface in pygame.sprite.spritecollide(self, logs, False):
                on_safe_surface = True
            for surface in pygame.sprite.spritecollide(self, turtles, False):
                if surface.state == 0: # Si la tortue ne plonge pas
                    on_safe_surface = True
            
            if not on_safe_surface:
                self.die()

        # Zone d'arrivée
        elif self.rect.y <= 50:
            print("Victoire ! La grenouille a atteint l'arrivée ! ")
            self.reset() # On la réinitialise pour une nouvelle traversée

    def die(self):
        if not self.dead:
            print(" La grenouille est morte.")
            self.image = frog_dead_img
            self.dead = True

    def move_to(self, grid_pos):
        self.rect.x = grid_pos[0] * astar.TILE_SIZE
        self.rect.y = grid_pos[1] * astar.TILE_SIZE


# === FONCTIONS UTILITAIRES ===
def text_objects(text, font):
    textSurface = font.render(text, True, white)
    return textSurface, textSurface.get_rect()

def message_display(text, position):
    largeText = pygame.font.Font('freesansbold.ttf', 16)
    TextSurf, TextRect = text_objects(text, largeText)
    TextRect.center = ((screen_width / 2), 10 + position)
    screen.blit(TextSurf, TextRect)

# Configure ou réinitialise les obstacles sur l'écran
def set_level():

    for sprite in all_sprites:
        sprite.kill()
    

    for i in range(8):
        is_diving = i % 3 == 0
        if i < 4:
            t = Turtle(2 if is_diving else 1, 3, 100 * i, 175, 75, 25, -2)
        else:
            t = Turtle(2 if is_diving else 1, 2, 87.5 * (i-4), 100, 50, 25, -2.5)
        turtles.add(t)
        all_sprites.add(t)


    for i in range(9):
        if i < 3: l = Log(150 * i, 150, 'short', 62.5, 25, 3)
        elif i < 6: l = Log(200 * (i-3), 125, 'long', 150, 25, 4)
        else: l = Log(150 * (i-6), 75, 'medium', 87.5, 25, 2)
        logs.add(l)
        all_sprites.add(l)


    for i in range(12):
        if i < 3: c = Car(75 * i, 325, 'yellow', 6, -1, 25, 25)
        elif i < 6: c = Car(75 * (i-3), 300, 'dozer', 2, 1, 25, 25)
        elif i < 9: c = Car(75 * (i-6), 275, 'purple', 4, -1, 25, 25)
        elif i < 10: c = Car(75 * (i-9), 250, 'green', 10, 1, 25, 25)
        else: c = Car(150 * (i-10), 225, 'truck', 3, -1, 50, 25)
        cars.add(c)
        all_sprites.add(c)


# === INITIALISATION DU JEU ===
player_frog = Frog()
frogs.add(player_frog)
set_level()

frog_dead_timer = 0
RESTART_DELAY = 5000 # milisecondes de délai après la mort


# === BOUCLE DE JEU PRINCIPALE ===
while not finish:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            finish = True

    # Logique de réinitialisation après la mort
    if player_frog.dead:
        if frog_dead_timer == 0:
            frog_dead_timer = pygame.time.get_ticks() # Démarrer le chrono
        elif pygame.time.get_ticks() - frog_dead_timer > RESTART_DELAY:
            player_frog.reset()
            frog_dead_timer = 0



    # --- Logique de l'IA  ---
    if not player_frog.dead:
        # On créé la grille à jour
        grid = astar.conservative_grid(screen_width, screen_height, cars, logs, turtles, turtleCounter)

        # On définit le départ et l'arrivée
        start_pos_grid = (player_frog.rect.x // astar.TILE_SIZE, player_frog.rect.y // astar.TILE_SIZE)

        # On définit les plusieurs points d'arrivée possibles 
        end_positions = [(x, 2) for x in range(1, 13, 2)] 

        # On choisit la destination la plus proche comme cible pour A*
        end_pos_grid = min(end_positions, key=lambda pos: abs(pos[0] - start_pos_grid[0]))

        # On applique A* pour trouver le chemin
        path = astar.astar(grid, start_pos_grid, end_pos_grid)


        if path and len(path) > 1:
            next_step = path[1] # la toute première case vers laquelle la grenouille doit se déplacer pour suivre le chemin
            player_frog.move_to(next_step)
        else:
            # Si aucun chemin n'est trouvé, la grenouille ne bouge pas
            pass


    # Mise à jour des sprites 
    all_sprites.update() 
    player_frog.check_status() # On vérifie le statut après le mouvement du monde


    # --- Affichage ---
    screen.blit(backgroundImage, (0, 0))
    all_sprites.draw(screen)
    frogs.draw(screen)


    if player_frog.dead:
        message_display('MORT', 0)
    else:
        message_display('VIVANT', 0)
    
    pygame.display.update()
    clock.tick(fps)

    # --- Gestion des tortues qui plongent ---
    turtleCounter += 1
    if turtleCounter >= 50:
        turtleCounter = 0
        for t in turtles:
            if t.canDive == 2:
                t.state = 1 - t.state 
                if t.size == 2:
                    t.image = twoTurtlesDive if t.state == 1 else twoTurtles
                else:
                    t.image = threeTurtlesDive if t.state == 1 else threeTurtles

pygame.quit()
quit()