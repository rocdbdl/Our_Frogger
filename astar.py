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
    Retourne une grille où 0 = praticable, 1 = obstacle.
    """
    # Calcule les dimensions de la grille en fonction de la taille des cases
    grid_width = screen_width // TILE_SIZE
    grid_height = screen_height // TILE_SIZE
    
    # Initialise une grille vide où tout est praticable (valeur 0)
    grid = [[0 for _ in range(grid_width)] for _ in range(grid_height)]

    # --- On marque les zones d'eau comme des obstacles ---
    # Lignes 3 à 7 correspondent à la rivière (de y=75 à y=175)
    for row in range(3, 8):
        for col in range(grid_width):
            grid[row][col] = 1 # 1 = Obstacle

    # --- On marque les surfaces sûres sur l'eau (bûches, tortues) ---
    # Les cases occupées par ces objets redeviennent praticables (valeur 0)
    safe_surfaces = pygame.sprite.Group(logs, turtles)
    for sprite in safe_surfaces:
        # Pour les tortues, ne les considérer sûres que si elles ne plongent pas
        if isinstance(sprite, pygame.sprite.Sprite) and hasattr(sprite, 'state') and sprite.state == 1:
            continue # Si la tortue plonge (state=1), elle n'est pas sûre, on passe

        # Convertit les coordonnées en pixels du sprite en coordonnées de grille
        start_col = sprite.rect.left // TILE_SIZE
        end_col = sprite.rect.right // TILE_SIZE
        row = sprite.rect.top // TILE_SIZE
        
        # Marque toutes les cases sous le sprite comme praticables
        for col in range(start_col, end_col + 1):
            if 0 <= col < grid_width:
                grid[row][col] = 0

    # --- On marque les voitures comme des obstacles ---
    for car in cars:
        start_col = car.rect.left // TILE_SIZE
        end_col = car.rect.right // TILE_SIZE
        row = car.rect.top // TILE_SIZE

        for col in range(start_col, end_col + 1):
            if 0 <= row < grid_height and 0 <= col < grid_width:
                grid[row][col] = 1

    return grid



# version plus intelligente de create_grid
# Cette version prédit la position des objets à la prochaine frame t+1
# Elle est utile pour éviter que la grenouille ne meure à cause d'un obstacle qui
# n'est pas encore là dans la frame actuelle t.
def create_predictive_grid(screen_width, screen_height, cars, logs, turtles, turtle_counter):
    """
    Crée une grille 2D représentant l'état du jeu à la PROCHAINE frame (t+1).
    0 = praticable, 1 = obstacle.
    """
    grid_width = screen_width // TILE_SIZE
    grid_height = screen_height // TILE_SIZE
    grid = [[0 for _ in range(grid_width)] for _ in range(grid_height)]

    # On marque les zones d'eau comme des obstacles
    for row in range(3, 8):
        for col in range(grid_width):
            grid[row][col] = 1

    # On prédit la position des surfaces sûres
    safe_surfaces = pygame.sprite.Group(logs, turtles)
    for sprite in safe_surfaces:
        # On prédit si la tortue va plonger
        will_dive = False
        if isinstance(sprite, pygame.sprite.Sprite) and hasattr(sprite, 'canDive') and sprite.canDive == 2:
            # Si le compteur arrive à 50 à la prochaine frame, l'état va s'inverser
            if (turtle_counter + 1) % 50 == 0:
                will_dive = (sprite.state == 0) # Si elle ne plonge pas, elle va plonger
            else:
                will_dive = (sprite.state == 1) # Si elle plonge, elle continue de plonger
        
        if will_dive:
            continue  # Cette tortue ne sera pas sûre, on ne la marque pas

        # Calcul de la position future
        future_rect_left = sprite.rect.left + sprite.speed
        future_rect_right = sprite.rect.right + sprite.speed
        
        start_col = int(future_rect_left // TILE_SIZE)
        end_col = int(future_rect_right // TILE_SIZE)
        row = sprite.rect.top // TILE_SIZE
        
        for col in range(start_col, end_col + 1):
            if 0 <= col < grid_width:
                grid[row][col] = 0


    # On prédit la position des voitures
    for car in cars:
        # Calcul de la position future
        future_rect_left = car.rect.left + car.speed
        future_rect_right = car.rect.right + car.speed

        start_col = int(future_rect_left // TILE_SIZE)
        end_col = int(future_rect_right // TILE_SIZE)
        row = car.rect.top // TILE_SIZE

        for col in range(start_col, end_col + 1):
            if 0 <= row < grid_height and 0 <= col < grid_width:
                grid[row][col] = 1

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