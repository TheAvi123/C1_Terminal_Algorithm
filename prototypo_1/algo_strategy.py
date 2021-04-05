import gamelib
import random
import math
import warnings
from sys import maxsize
import json

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring Prototypo_1...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        global NO_ATTACK, WAITING_TO_ATTACK, BASIC_SCOUT_ATTACK, SPLIT_SCOUT_ATTACK, DEMOLISHER_ATTACK
        NO_ATTACK = 0
        WAITING_TO_ATTACK = 1
        BASIC_SCOUT_ATTACK = 2
        SPLIT_SCOUT_ATTACK = 3
        DEMOLISHER_ATTACK = 4
        # This is a good place to do initial setup
        self.attack_status = 0
        self.attack_delay = 0
        self.min_attack_size = 6
        self.max_attack_wait = 32
        self.scored_on_locations = []
        self.build_exceptions = []
        self.threat_map = []
        self.set_build_queues()

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of Prototypo_1'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.turn_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All Methods below this point are Prototypo methods
    """

    """ Logic Switching for different strategies throughout the game """
    def turn_strategy(self, game_state):
        # Check for delayed attack strategy
        self.attack_delay -= 1
        if self.attack_delay < 0:
            self.attack_status = NO_ATTACK
            self.build_exceptions = []
        else: 
            self.attack_status = WAITING_TO_ATTACK
        
        # Build Intial Defense Configuration on Turn 0
        if game_state.turn_number == 0:
            self.build_initial_defenses(game_state)
            self.remove_base_buildings(game_state)
            return
        
        # Build Core Defenses
        self.build_defenses(game_state, self.core_queue)

        # Offensive Moves
        self.determine_attack_strategy(game_state)

        # Defensive Moves
        self.build_additional_defenses(game_state)
        self.remove_base_buildings(game_state)


    """ Builds initial defense configuration"""
    def build_initial_defenses(self, game_state):
        # Place turrets
        turret_locations = [[3, 12], [24, 12], [4, 11], [23, 11], [5, 10], [22, 10], [8, 7], [19, 7], [12, 6], [15, 6]]
        num_spawned = game_state.attempt_spawn(TURRET, turret_locations)
        if num_spawned < len(turret_locations):
            gamelib.debug_write('ERROR: Failed to spawn initial turrets: ' + str(num_spawned))

        # Place walls
        wall_locations = [[0, 13], [1, 13], [2, 13], [3, 13], [24, 13], [25, 13], [26, 13], [27, 13], [5, 12], [22, 12]]
        num_spawned = game_state.attempt_spawn(WALL, wall_locations)
        if num_spawned < len(wall_locations):
            gamelib.debug_write('ERROR: Failed to spawn initial walls: '  + str(num_spawned))


    """ Mark all unupgraded structures for removal """
    def remove_base_buildings(self, game_state):
        base_structures = self.get_structure_positions(game_state, False)
        num_removed = 0
        for structure in base_structures:
            num_removed += game_state.attempt_remove(structure)
        if num_removed < len(base_structures):
            gamelib.debug_write('ERROR: Failed to mark all base structures for removal')


    """ Returns list of positions containing base (or upgraded) structures """
    def get_structure_positions(self, game_state, upgraded = False):
        positions = []
        for x in range(0, 28):
            for y in range(0, 28):
                location = [x, y]
                if game_state.game_map.in_arena_bounds(location):
                    unit = game_state.contains_stationary_unit(location)
                    if unit is not False and unit.player_index == 0 and unit.upgraded is upgraded:
                        positions.append(location)
        return positions


    """ Removed build exceptions from a given list of locations """
    def enforce_build_exceptions(self, locations):
        new_locations = []
        for loc in locations:
            if loc not in self.build_exceptions:
                new_locations.append(loc)
        return new_locations


    """ Build defenses """
    def build_defenses(self, game_state, build_queue):
        for item in build_queue:
            filtered_locations = self.enforce_build_exceptions(item.iloc)
            if item.iupgrade:
                gamelib.debug_write(filtered_locations)
                game_state.attempt_upgrade(filtered_locations)
            else:
                game_state.attempt_spawn(item.itype, filtered_locations)
            # Stop if no SP left
            if game_state.get_resource(SP, 0) == 0:
                break


    """ Build additional defenses and upgrades structures in a prioritized order """
    def build_additional_defenses(self, game_state): 
        # Setup Queue
        build_queue = []
        queue_additions = [self.funnel_queue, self.corner_queue, self.center_queue, self.wall_queue, self.support_queue]
        for queue in queue_additions:
            build_queue += queue
        # Build/Upgrade Units
        self.build_defenses(game_state, build_queue)


    """ TODO: Reconfigure this """
    """ Manually set build and upgrade queue order"""
    def set_build_queues(self):
        self.core_queue = [
            QueueItem(WALL, False, [[0, 13], [27, 13], 
                                    [1, 13], [26, 13], 
                                    [2, 13], [25, 13], 
                                    [3, 13], [24, 13], 
                                    [4, 12], [23, 12]]),
            QueueItem(TURRET, False, [[2, 12], [25, 12], 
                                      [3, 12], [24, 12],  
                                      [5, 10], [22, 10], 
                                      [7, 8], [20, 8], 
                                      [9, 6], [18, 6], 
                                      [15, 6], [12, 6]]),
            QueueItem(TURRET, True , [[2, 12], [25, 12], 
                                      [3, 12], [24, 12],  
                                      [5, 10], [22, 10], 
                                      [7, 8], [20, 8], 
                                      [9, 6], [18, 6], 
                                      [15, 6], [12, 6]]),
            QueueItem(WALL, True , [[0, 13], [27, 13], 
                                    [1, 13], [26, 13]]),
            QueueItem(WALL, False, [[5, 11], [22, 11], 
                                    [7, 9], [20, 9]]),
            QueueItem(WALL, True , [[5, 11], [22, 11], 
                                    [7, 9], [20, 9]])
            
        ]
        self.center_queue = [
            QueueItem(WALL, False, [[10, 7], [17, 7], 
                                    [11, 7], [16, 7], 
                                    [13, 7], [14, 7]]),
            QueueItem(WALL, True , [[9, 8], [18, 8], 
                                    [15, 8], [12, 8],
                                    [10, 7], [17, 7], 
                                    [11, 7], [16, 7], 
                                    [13, 7], [14, 7]])
        ]
        self.funnel_queue = [
            QueueItem(WALL, False, [[6, 10], [21, 10], 
                                    [8, 8], [19, 8]]),
            QueueItem(TURRET, False, [[4, 11], [23, 11], 
                                      [6, 9], [21, 9], 
                                      [8, 7], [19, 7]]),
            QueueItem(TURRET, True , [[4, 11], [23, 11], 
                                      [8, 7], [19, 7]]),
            QueueItem(WALL, True, [[4, 12], [23, 12],
                                   [8, 8], [19, 8]])
        ]
        self.wall_queue = [
            QueueItem(WALL, False, [[5, 12], [22, 12], 
                                   [6, 11], [21, 11], 
                                   [7, 10], [20, 10], 
                                   [8, 9], [19, 9]]),
            QueueItem(WALL, True, [[5, 12], [22, 12], 
                                   [6, 11], [21, 11], 
                                   [8, 9], [19, 9]])
        ]
        self.corner_queue = [
            QueueItem(WALL, False, [[4, 13], [23, 13]]),  
            QueueItem(WALL, True , [[4, 13], [23, 13]]), 
            QueueItem(TURRET, False, [[1, 12], [26, 12]]),  
            QueueItem(TURRET, True , [[1, 12], [26, 12]]), 
            QueueItem(WALL, True , [[2, 13], [25, 13], 
                                    [3, 13], [24, 13]])
        ]
        self.support_queue = [   
            QueueItem(SUPPORT, False, [[10, 5], [11, 5], [12, 5], [13, 5], [14, 5], [15, 5], 
                                       [16, 5], [17, 5], [13, 4], [14, 4], [10, 3], [11, 3], 
                                       [13, 3], [14, 3], [16, 3], [17, 3], [11, 2], [16, 2], 
                                       [12, 1], [13, 1], [14, 1], [15, 1], [13, 0], [14, 0]]), 
        ]


    """ TODO: Add more strategies """
    """ Determine if there is enough MP to attack and choose viable attack strategy """
    def determine_attack_strategy(self, game_state):
        playerMP = int(game_state.get_resource(MP, 0))
        threshold = max(self.min_attack_size, min(self.max_attack_wait, 0.7 * game_state.turn_number))
        if playerMP >= threshold:
            self.generate_threatmap(game_state)
            safest_deployment = self.find_safest_deploy_location(game_state)
            path_is_blocked = self.check_path_blocked(game_state, safest_deployment[0])
            # TODO: check for empty board
            if safest_deployment[1] < playerMP / 2 and not path_is_blocked:
                # relatively safe path exists for a single stack scout attack
                self.attack_delay = 0
                self.attack_status = BASIC_SCOUT_ATTACK
                self.basic_scout_attack(game_state, safest_deployment[0], playerMP)
                self.build_exceptions = game_state.find_path_to_edge(safest_deployment[0])
            elif path_is_blocked:
                self.attack_delay = 0
                self.attack_status = SPLIT_SCOUT_ATTACK
                self.split_scout_attack(game_state, playerMP)
            else:
                self.attack_delay = 0
                self.attack_status = DEMOLISHER_ATTACK
                self.demolisher_attack(game_state, safest_deployment[0], playerMP)
        else:
            self.attack_status = NO_ATTACK
            self.build_exceptions = [] 


    """ Generate 2D array representing threat level at every location on the map """
    def generate_threatmap(self, game_state):
        self.threat_map = []
        for x in range(28):
            column = []
            for y in range(28):
                location = [x, y]
                if game_state.game_map.in_arena_bounds(location) is False:
                    column.append(None)
                    continue
                turrets_in_range = game_state.get_attackers(location, 0)
                threat_level = 0
                for turret in turrets_in_range:
                    threat_level += turret.damage_i
                column.append(threat_level)
            self.threat_map.append(column)


    """ Generate 2D array representing threat level at every location on the map """
    """ Return list of 2 items: location of safest point, and thread on path """
    def find_safest_deploy_location(self, game_state, locations = None):
        deploy_locations = []
        if locations is None or len(locations) == 0:
            deploy_locations = self.get_viable_deploy_locations(game_state)
        else:
            deploy_locations = locations
        safest_point = None
        safest_point_threat = math.inf
        for deploy_loc in deploy_locations:
            path = game_state.find_path_to_edge(deploy_loc)
            if path is None or len(path) == 0:
                gamelib.debug_write('Error: Path was None or empty list')
            else: 
                path_threat = 0
                for path_loc in path:
                    path_threat += self.threat_map[path_loc[0]][path_loc[1]]
                if path_threat < safest_point_threat:
                    safest_point = deploy_loc
                    safest_point_threat = path_threat
        return [safest_point, safest_point_threat]


    """ Finds all deployment locations that are not blocked """
    def get_viable_deploy_locations(self, game_state):
        friendly_locations = game_state.game_map.get_edges()[2] + game_state.game_map.get_edges()[3]
        viable_locations = []
        for location in friendly_locations:
            if game_state.contains_stationary_unit(location) is False:
                viable_locations.append(location)
        return viable_locations


    """ TODO: Return true if enemy has blocked all paths to their edge """
    def check_path_blocked(self, game_state, deploy_point):
        enemy_edges = game_state.game_map.get_edges()[0] + game_state.game_map.get_edges()[1]
        predicted_path = game_state.find_path_to_edge(deploy_point)
        if predicted_path[-1] in enemy_edges:
            return False
        else:
            return True


    """ Basic Single Stack Scout Attack """
    def basic_scout_attack(self, game_state, deploy_point, attack_size):
        spawn_count = game_state.attempt_spawn(SCOUT, deploy_point, attack_size)
        if (spawn_count < attack_size):
            gamelib.debug_write('ERROR: Num spawned is {} but {} MP available'.format(spawn_count, game_state.get_resource(MP, 0)))


    """ TODO: Basic charge attack which waits to accumulate a certain number of MP and uses scouts 
        Returns 1 if attacking, 0 otherwise"""
    def split_scout_attack(self, game_state, attack_size):
        potential_locations = [[7, 6], [20, 6]]
        deploy_location = self.find_safest_deploy_location(game_state, potential_locations)[0]
        if deploy_location is None:
            gamelib.debug_write('Error: SSA returned no deploy location... manually setting to [7, 6]')
            deploy_location = [7, 6]
        if deploy_location == [7, 6]:
            deploy_location_2 = [6, 7]
            self.build_exceptions = [[21, 9], [21, 10], [20, 10]]
        elif deploy_location == [20, 6]:
            deploy_location_2 = [21, 7]
            self.build_exceptions = [[6, 9], [6, 10], [7, 10]]
        else: 
            gamelib.debug_write('ERROR: SSA returned unexpected deploy location: ' + str(deploy_location))
            return
        stack_size = int(attack_size / 2)
        spawn_count = game_state.attempt_spawn(SCOUT, deploy_location, stack_size)
        spawn_count = game_state.attempt_spawn(SCOUT, deploy_location_2, stack_size)
        if (spawn_count < stack_size):
            gamelib.debug_write('ERROR: Num spawned is {} but {} MP available'.format(spawn_count, attack_size))


    """ Basic demolisher attack to clear enemy base"""
    def demolisher_attack(self, game_state, deploy_point, attack_size):
        spawn_count = game_state.attempt_spawn(SCOUT, deploy_point, attack_size)
        if (spawn_count < attack_size):
            gamelib.debug_write('ERROR: Num spawned is {} but {} MP available'.format(spawn_count, game_state.get_resource(MP, 0)))
        return

""" Custom Class for representing upgrades in a queue"""
class QueueItem:
    iloc = None
    itype = None
    iupgrade = False

    def __init__(self, unit_type, needs_upgrade, locations):
        self.iloc = locations
        self.itype = unit_type
        self.iupgrade = needs_upgrade

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
