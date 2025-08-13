import pygame

# Taille de chaque case de la grille en pixels
TILE_SIZE = 25

class Node:
    """
    Un nœud dans la grille de recherche. Chaque nœud représente une case.
    """
    def __init__(self, parent=None, position=None):
        self.parent = parent    # Le nœud parent dans le chemin
        self.position = position  # Tuple (ligne, colonne)

        # Coûts pour l'algorithme A*
        self.g = 0  # Coût du chemin depuis le départ jusqu'à ce nœud
        self.h = 0  # Coût heuristique estimé jusqu'à la fin
        self.f = 0  # Coût total (g + h)

    def __eq__(self, other):
        # Un nœud est égal à un autre s'ils ont la même position
        return self.position == other.position


def create_grid(screen_width, screen_height, cars, logs, turtles):
    """
    Crée une grille 2D représentant l'état actuel du jeu.
    0 = praticable, 1 = obstacle.
    """
    grid_width = screen_width // TILE_SIZE
    grid_height = screen_height // TILE_SIZE
    grid = [[0 for _ in range(grid_width)] for _ in range(grid_height)]

    # Marque la rivière comme obstacles (lignes 3 à 7)
    for row in range(3, 8):
        if 0 <= row < grid_height:
            for col in range(grid_width):
                grid[row][col] = 1

    # Surfaces sûres (bûches & tortues non plongeantes)
    safe_surfaces = pygame.sprite.Group(logs, turtles)
    for sprite in safe_surfaces:
        # Tortues plongeantes non sûres
        if hasattr(sprite, 'state') and sprite.state == 1:
            continue

        row = sprite.rect.top // TILE_SIZE
        if not (0 <= row < grid_height):
            continue

        start_col = sprite.rect.left // TILE_SIZE
        end_col = (sprite.rect.right - 1) // TILE_SIZE  # borne droite exclusive -> -1

        # Clamp dans la grille
        start_col = max(0, start_col)
        end_col = min(grid_width - 1, end_col)

        for col in range(start_col, end_col + 1):
            grid[row][col] = 0

    # Voitures = obstacles
    for car in cars:
        row = car.rect.top // TILE_SIZE
        if not (0 <= row < grid_height):
            continue

        start_col = car.rect.left // TILE_SIZE
        end_col = (car.rect.right - 1) // TILE_SIZE

        start_col = max(0, start_col)
        end_col = min(grid_width - 1, end_col)

        for col in range(start_col, end_col + 1):
            grid[row][col] = 1

    return grid




# version plus intelligente de create_grid
# Cette version prédit la position des objets à la prochaine frame t+1
# Elle est utile pour éviter que la grenouille ne meure à cause d'un obstacle qui
# n'est pas encore là dans la frame actuelle t.
def create_predictive_grid(screen_width, screen_height, cars, logs, turtles, turtle_counter):
    """
    Grille 2D représentant l'état du jeu à la PROCHAINE frame (t+1).
    0 = praticable, 1 = obstacle.
    """
    grid_width = screen_width // TILE_SIZE
    grid_height = screen_height // TILE_SIZE
    grid = [[0 for _ in range(grid_width)] for _ in range(grid_height)]

    # Marque la rivière comme obstacles (lignes 3 à 7)
    for row in range(3, 8):
        if 0 <= row < grid_height:
            for col in range(grid_width):
                grid[row][col] = 1

    # Surfaces sûres prédites (bûches & tortues non plongeantes à t+1)
    safe_surfaces = pygame.sprite.Group(logs, turtles)
    for sprite in safe_surfaces:
        # Prédire le plongeon des tortues
        will_dive = False
        if hasattr(sprite, 'canDive') and sprite.canDive == 2:
            if (turtle_counter + 1) % 50 == 0:
                will_dive = (sprite.state == 0)  # va commencer à plonger
            else:
                will_dive = (sprite.state == 1)  # reste en plongée

        if will_dive:
            continue

        # Position future à t+1
        future_left = sprite.rect.left + sprite.speed
        future_right = sprite.rect.right + sprite.speed
        row = sprite.rect.top // TILE_SIZE
        if not (0 <= row < grid_height):
            continue

        start_col = int(future_left // TILE_SIZE)
        end_col = int((future_right - 1) // TILE_SIZE)  # borne droite exclusive -> -1

        # Clamp
        start_col = max(0, start_col)
        end_col = min(grid_width - 1, end_col)

        for col in range(start_col, end_col + 1):
            grid[row][col] = 0

    # Voitures prédites à t+1 = obstacles
    for car in cars:
        future_left = car.rect.left + car.speed
        future_right = car.rect.right + car.speed
        row = car.rect.top // TILE_SIZE
        if not (0 <= row < grid_height):
            continue

        start_col = int(future_left // TILE_SIZE)
        end_col = int((future_right - 1) // TILE_SIZE)

        start_col = max(0, start_col)
        end_col = min(grid_width - 1, end_col)

        for col in range(start_col, end_col + 1):
            grid[row][col] = 1

    return grid

def conservative_grid(screen_width, screen_height, cars, logs, turtles, turtle_counter):
    g_now  = create_grid(screen_width, screen_height, cars, logs, turtles)
    g_next = create_predictive_grid(screen_width, screen_height, cars, logs, turtles, turtle_counter)
    h, w = len(g_now), len(g_now[0])
    grid = [[0]*w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            # 1 = obstacle. On est conservateur: obstacle s'il y a obstacle maintenant OU à la prochaine frame.
            grid[r][c] = 1 if (g_now[r][c] == 1 or g_next[r][c] == 1) else 0
    return grid


def astar(grid, start, end):
    """
    Retourne une liste de tuples (ligne, colonne) représentant le chemin du début à la fin.
    Utilise l'algorithme A*
    """
    start_node = Node(None, start)
    end_node = Node(None, end)

    open_list = []  # Liste des nœuds à visiter
    closed_list = [] # Liste des nœuds déjà visités

    open_list.append(start_node)

    while open_list:
        # --- Trouve le nœud avec le coût F le plus bas dans la open_list ---
        current_node = open_list[0]
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        # --- Déplace le nœud actuel de open_list à closed_list ---
        open_list.pop(current_index)
        closed_list.append(current_node)

        # --- Vérifie si on a atteint la fin ---
        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1]  # Retourne le chemin inversé (du début à la fin)

        # --- Génère les voisins (enfants) ---
        children = []
        # Mouvements possibles : Haut, Bas, Gauche, Droite
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            # S'assure que le voisin est dans les limites de la grille
            if not (0 <= node_position[0] < len(grid[0]) and 0 <= node_position[1] < len(grid)):
                continue

            # S'assure que le voisin est une case praticable
            if grid[node_position[1]][node_position[0]] != 0:
                continue

            new_node = Node(current_node, node_position)
            children.append(new_node)

        # --- Traite les voisins ---
        for child in children:
            # Si le voisin est déjà dans la closed_list, on l'ignore
            if child in closed_list:
                continue

            # Calcule les coûts g, h, et f
            child.g = current_node.g + 1
            # Heuristique: Distance de Manhattan
            child.h = abs(child.position[0] - end_node.position[0]) + abs(child.position[1] - end_node.position[1])
            child.f = child.g + child.h

            # Si le voisin est déjà dans open_list avec un meilleur coût g, on l'ignore
            if any(open_node for open_node in open_list if child == open_node and child.g >= open_node.g):
                continue
            
            # Ajouter le voisin à la open_list
            open_list.append(child)
            
    return None # Retourne None si aucun chemin n'est trouvé