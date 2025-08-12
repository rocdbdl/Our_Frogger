import pygame

# Taille de chaque case de la grille en pixels
TILE_SIZE = 25

class Node:
    """
    Un nœud dans la grille de recherche. Chaque nœud représente une case.
    """
    def __init__(self, parent=None, position=None):
        self.parent = parent
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

    # --- Étape 1: Marquer les zones d'eau comme des obstacles ---
    # Lignes 3 à 7 correspondent à la rivière (de y=75 à y=175)
    for row in range(3, 8):
        for col in range(grid_width):
            grid[row][col] = 1 # 1 = Obstacle

    # --- Étape 2: Marquer les surfaces sûres sur l'eau (bûches, tortues) ---
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

    # --- Étape 3: Marquer les voitures comme des obstacles ---
    for car in cars:
        start_col = car.rect.left // TILE_SIZE
        end_col = car.rect.right // TILE_SIZE
        row = car.rect.top // TILE_SIZE

        for col in range(start_col, end_col + 1):
            if 0 <= row < grid_height and 0 <= col < grid_width:
                grid[row][col] = 1

    return grid

def astar(grid, start, end):
    """
    Retourne une liste de tuples (ligne, colonne) représentant le chemin du début à la fin.
    Utilise l'algorithme A*.
    """
    start_node = Node(None, start)
    end_node = Node(None, end)

    open_list = []  # Liste des nœuds à visiter
    closed_list = [] # Liste des nœuds déjà visités

    open_list.append(start_node)

    while open_list:
        # --- Trouver le nœud avec le coût F le plus bas dans la open_list ---
        current_node = open_list[0]
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        # --- Déplacer le nœud actuel de open_list à closed_list ---
        open_list.pop(current_index)
        closed_list.append(current_node)

        # --- Vérifier si on a atteint la fin ---
        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1]  # Retourner le chemin inversé (du début à la fin)

        # --- Générer les voisins (enfants) ---
        children = []
        # Mouvements possibles : Haut, Bas, Gauche, Droite
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            # S'assurer que le voisin est dans les limites de la grille
            if not (0 <= node_position[0] < len(grid[0]) and 0 <= node_position[1] < len(grid)):
                continue

            # S'assurer que le voisin est une case praticable
            if grid[node_position[1]][node_position[0]] != 0:
                continue

            new_node = Node(current_node, node_position)
            children.append(new_node)

        # --- Traiter les voisins ---
        for child in children:
            # Si le voisin est déjà dans la closed_list, on l'ignore
            if child in closed_list:
                continue

            # Calculer les coûts g, h, et f
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