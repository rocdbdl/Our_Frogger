# astar_spatiotemporal.py

import pygame

# Taille de chaque case de la grille en pixels
TILE_SIZE = 25

def is_walkable_at_time(pos_xy, time, world_sprites):
    """
    Vérifie si une case (col, row) est sûre à un instant 'time' donné.
    Retourne True si la case est sûre, False sinon.
    """
    col, row = pos_xy
    cars, logs, turtles, turtle_counter_start = world_sprites

    grid_width = 350 // TILE_SIZE
    grid_height = 400 // TILE_SIZE

    # On vérifie les limites de la grille
    if not (0 <= col < grid_width and 0 <= row < grid_height):
        return False

    # On vérifie si la case est occupée par une voiture
    for car in cars:
        if car.rect.top // TILE_SIZE == row:
            # On calcule la position future de la voiture
            future_left = car.rect.left + car.speed * time
            future_right = car.rect.right + car.speed * time
            # On vérifie si la colonne de la case est dans l'intervalle de la voiture
            if future_left <= (col + 1) * TILE_SIZE and future_right >= col * TILE_SIZE:
                return False # Collision avec une voiture 

    # On vérifie si la case est dans la rivière (lignes 3 à 7)
    if 3 <= row <= 7:
        is_safe_surface = False
        # On vérifie si une bûche sera là
        for log in logs:
            if log.rect.top // TILE_SIZE == row:
                future_left = log.rect.left + log.speed * time
                future_right = log.rect.right + log.speed * time
                if future_left <= (col + 1) * TILE_SIZE and future_right >= col * TILE_SIZE:
                    is_safe_surface = True
                    break
        
        # Si pas sur une bûche, vérifie pour une tortue
        if not is_safe_surface:
            for turtle in turtles:
                if turtle.rect.top // TILE_SIZE == row:
                    # Prédire si la tortue plonge
                    if turtle.canDive == 2:
                        # Le cycle de plongée est de 50 frames.
                        # Le nombre de cycles de plongée complets au temps 'time'
                        num_dive_cycles = (turtle_counter_start + time) // 50
                        is_diving = (num_dive_cycles % 2 != 0)
                    else:
                        is_diving = False

                    if not is_diving:
                        future_left = turtle.rect.left + turtle.speed * time
                        future_right = turtle.rect.right + turtle.speed * time
                        if future_left <= (col + 1) * TILE_SIZE and future_right >= col * TILE_SIZE:
                            is_safe_surface = True
                            break
        
        return is_safe_surface # True si sur une surface sûre, False si dans l'eau

    # Si ce n'est ni une voiture ni la rivière, c'est une route sûre
    return True


class Node:
    """ Un nœud dans la recherche spatio-temporelle. """
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position  # Tuple (col, row, time)

        self.g = 0  # Coût du chemin (équivalent au temps)
        self.h = 0  # Heuristique (estimation du temps restant)
        self.f = 0  # Coût total (g + h)

    def __eq__(self, other):
        return self.position == other.position


def spatio_temporal_astar(start_pos, end_pos, world_sprites, max_time=100):
    """
    Trouve un chemin optimal dans l'espace-temps (col, row, time).
    start_pos et end_pos sont en (col, row).
    """
    start_node = Node(None, (start_pos[0], start_pos[1], 0))
    end_pos_xy = end_pos 

    open_list = []
    closed_list = set() # un set pour des recherches rapides

    open_list.append(start_node)

    while open_list:
        # Trouve le meilleur nœud ie plus petit f dans open_list
        open_list.sort(key=lambda x: x.f)
        current_node = open_list.pop(0)

        # Si on a déjà visité cet état (pos, time), on passe
        if current_node.position in closed_list:
            continue
        closed_list.add(current_node.position)

        # Condition de victoire : on a atteint les coordonnées du but
        if current_node.position[0:2] == end_pos_xy:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1] # Retourne le plan complet (col, row, time)

        # Génère les 5 mouvements possibles
        children = []

        for move in [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)]: 
            pos = current_node.position
            new_pos = (pos[0] + move[0], pos[1] + move[1], pos[2] + 1)

            # Ne pas chercher un plan trop loin dans le futur
            if new_pos[2] > max_time:
                continue
            
            # Vérifie si la nouvelle position est sûre à ce temps
            if not is_walkable_at_time(new_pos[0:2], new_pos[2], world_sprites):
                continue
            
            children.append(Node(current_node, new_pos))
        
        for child in children:
            child.g = child.position[2] 
            child.h = abs(child.position[0] - end_pos_xy[0]) + abs(child.position[1] - end_pos_xy[1])
            child.f = child.g + child.h
            open_list.append(child)

    return None # Aucun chemin trouvé dans l'horizon de temps