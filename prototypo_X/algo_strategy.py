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
        self.max_attack_wait = 16
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
        #self.build_defenses(game_state, self.core_queue)

        # Offensive Moves
        self.determine_attack_strategy(game_state)

        # Defensive Moves
        self.build_additional_defenses(game_state)
        self.remove_base_buildings(game_state)

    """ CSA : Find the least defended (by turrets) section of the opponent's board"""
    """ CSA : Find Least Defended Cross Section """
    """ Find Weakly Defended Locations """
    def CSA(self, game_state):
        # If one the corner triangles 
        # This will be used in an attack strategy, and help us decide what kind of attack

        # these coordinates are all from our point of view
        left_corner_points = [[3, 17], [4, 17], [2, 16], [3, 16], [4, 16], [5, 16], [1, 15], [2, 15], [3, 15], [4, 15], [5, 15], [6, 15], 
        [0, 14], [1, 14], [2, 14], [3, 14], [4, 14], [5, 14], [6, 14], [7, 14]]

        right_corner_points = [[23, 17], [24, 17], [22, 16], [23, 16], [24, 16], [25, 16], [21, 15], [22, 15], [23, 15], [24, 15], [25, 15], 
        [26, 15], [20, 14], [21, 14], [22, 14], [23, 14], [24, 14], [25, 14], [26, 14], [27, 14]]

        middle_points_our_left = [[6, 20], [7, 20], [5, 19], [6, 19], [7, 19], [8, 19], [4, 18], [5, 18], [6, 18], [7, 18], [8, 18], [9, 18], 
        [5, 17], [6, 17], [7, 17], [8, 17], [9, 17], [10, 17], [6, 16], [7, 16], [8, 16], [9, 16], [10, 16], [11, 16], [7, 15], [8, 15], [9, 15], 
        [10, 15], [11, 15], [12, 15], [8, 14], [9, 14], [10, 14], [11, 14], [12, 14], [13, 14]]

        middle_points_our_right = [[20, 20], [21, 20], [19, 19], [20, 19], [21, 19], [22, 19], [18, 18], [19, 18], [20, 18], [21, 18], [22, 18], 
        [23, 18], [17, 17], [18, 17], [19, 17], [20, 17], [21, 17], [22, 17], [16, 16], [17, 16], [18, 16], [19, 16], [20, 16], [21, 16], [15, 15], 
        [16, 15], [17, 15], [18, 15], [19, 15], [20, 15], [14, 14], [15, 14], [16, 14], [17, 14], [18, 14], [19, 14]]

        middle_square = [[13, 27], [14, 27], [12, 26], [13, 26], [14, 26], [15, 26], [11, 25], [12, 25], [13, 25], [14, 25], [15, 25], [16, 25], 
        [10, 24], [11, 24], [12, 24], [13, 24], [14, 24], [15, 24], [16, 24], [17, 24], [9, 23], [10, 23], [11, 23], [12, 23], [13, 23], [14, 23],
        [15, 23], [16, 23], [17, 23], [18, 23], [8, 22], [9, 22], [10, 22], [11, 22], [12, 22], [13, 22], [14, 22], [15, 22], [16, 22], [17, 22], 
        [18, 22], [19, 22], [7, 21], [8, 21], [9, 21], [10, 21], [11, 21], [12, 21], [13, 21], [14, 21], [15, 21], [16, 21], [17, 21], [18, 21], 
        [19, 21], [20, 21], [8, 20], [9, 20], [10, 20], [11, 20], [12, 20], [13, 20], [14, 20], [15, 20], [16, 20], [17, 20], [18, 20], [19, 20], 
        [9, 19], [10, 19], [11, 19], [12, 19], [13, 19], [14, 19], [15, 19], [16, 19], [17, 19], [18, 19], [10, 18], [11, 18], [12, 18], [13, 18], 
        [14, 18], [15, 18], [16, 18], [17, 18], [11, 17], [12, 17], [13, 17], [14, 17], [15, 17], [16, 17], [12, 16], [13, 16], [14, 16], [15, 16], 
        [13, 15], [14, 15]]

        turret_danger_densities = {'left' : 0, 'midleft' : 0, 'right' : 0, 'midright' : 0, 'middle' : 0}

        for point in left_corner_points:
            turret_danger_densities['left'] += self.threat_map[point[0]][point[1]]

        for point in right_corner_points:
            turret_danger_densities['right'] += self.threat_map[point[0]][point[1]]

        for point in middle_points_our_left:
            turret_danger_densities['midleft'] += self.threat_map[point[0]][point[1]]

        for point in middle_points_our_right:
            turret_danger_densities['midright'] += self.threat_map[point[0]][point[1]]

        for point in middle_square:
            turret_danger_densities['middle'] += self.threat_map[point[0]][point[1]]

        min_key = min(turret_danger_densities.items(), key=(lambda key: turret_danger_densities[key[0]]))
        
        return turret_danger_densities# {'min_td' : min_key[0], 'turrets_danger' : turret_danger_densities[min_key[0]]}


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
                game_state.attempt_upgrade(filtered_locations)
            else:
                game_state.attempt_spawn(item.itype, filtered_locations)
            # Stop if no SP left
            if game_state.get_resource(SP, 0) == 0:
                break


    """ Build additional defenses and upgrades structures in a prioritized order """
    def build_additional_defenses(self, game_state): 
        # Setup Queue
        build_queue = self.core_queue
        queue_additions = [self.support_queue]
        for queue in queue_additions:
            build_queue += queue
        # Build/Upgrade Units
        self.build_defenses(game_state, build_queue)


    """ TODO: Reconfigure this """
    """ Manually set build and upgrade queue order"""
    def set_build_queues(self):
        self.core_queue = [
            QueueItem(TURRET, False, [[2, 13], [3, 12], [25, 12], [4, 11], [21, 10], [18, 7]]),
            QueueItem(WALL, False, [[0, 13], [1, 13], [25, 13], [26, 13], [27, 13], [5, 10], [6, 9], [7, 8], [8, 7], 
            [9, 6], [17, 6], [10, 5], [16, 5], [11, 4], [15, 4], [12, 3], [14, 3], [13, 2]]),    
            QueueItem(WALL, False, [[3, 13], [4, 12], [24, 13], [21, 11]]),
            QueueItem(None, True, [[3, 12], [3, 13], [4, 11], [4, 12], [25, 12], [24, 13], [21, 10], [21, 11]]),    
            QueueItem(WALL, False, [[23, 13], [21, 12], [20, 10]]),  
            QueueItem(TURRET, False, [[24, 12], [22, 11], [24, 11], [20, 9], [19, 8]]),
            QueueItem(None, True, [[24, 12], [23, 13], [27, 13], [26, 13], [22, 11], [21, 12]]),
            QueueItem(TURRET, False, [[1, 12], [2, 12], [26, 12], [25, 11]]),
            QueueItem(WALL, False, [[5, 11], [19, 9], [18, 8], [17, 7], [21, 7], [20, 6], [24, 10], [23, 9], [22, 8]]),  
            QueueItem(None, True, [[2, 13], [25, 13], [25, 12], [26, 12], [5, 11], [24, 11], [25, 11], [5, 10], [20, 10], 
            [24, 10], [19, 9], [20, 9], [23, 9], [18, 8], [19, 8], [22, 8], [17, 7], [18, 7], [21, 7]])
        ]
        self.support_queue = [   
            QueueItem(WALL, False, [[6, 11], [7, 11], [8, 11]]), 
            QueueItem(SUPPORT, False, [[6, 10], [7, 10], [8, 10], [7, 9], [8, 9], [9, 9], [8, 8], [9, 8], [10, 8], [9, 7], [10, 7], 
            [11, 7], [10, 6], [11, 6], [12, 6], [11, 5], [12, 5], [13, 5], [12, 4], [13, 4], [14, 4], [13, 3]]), 
        ]


    """ TODO: Add more strategies """
    """ Determine if there is enough MP to attack and choose viable attack strategy """
    def determine_attack_strategy(self, game_state):
        playerMP = int(game_state.get_resource(MP, 0))
        enemyMP = int(game_state.get_resource(MP, 1))
        threshold = max(self.min_attack_size, min(self.max_attack_wait, 0.8 * game_state.turn_number))
        interceptor_check = 0
        if self.all_core_defenses_built(game_state) is True:
            interceptor_check = int(game_state.turn_number * 0.7)
        if playerMP >= int(threshold):
            self.generate_threatmap(game_state)
            safest_deployment = self.find_safest_deploy_location(game_state)
            path_is_blocked = False
            if safest_deployment[0] is None:
                path_is_blocked = True
            else:
                gamelib.debug_write('ATTACKING ::: Safest Point = ' + str(safest_deployment[0]))
                gamelib.debug_write('ATTACKING ::: Safest Path = ' + str(game_state.find_path_to_edge(safest_deployment[0])))
            gamelib.debug_write('ATTACKING ::: Path Blocked = ' + str(path_is_blocked))
            # Attack logic switching
            if safest_deployment[1] < playerMP / 2 and not path_is_blocked:
                gamelib.debug_write('ATTACKING ::: BASIC_SCOUT_ATTACK')
                # relatively safe path exists for a single stack scout attack
                self.attack_delay = 0
                self.attack_status = BASIC_SCOUT_ATTACK
                self.basic_scout_attack(game_state, safest_deployment[0], playerMP)
                self.build_exceptions = game_state.find_path_to_edge(safest_deployment[0])
                if [14, 1] not in self.build_exceptions:
                    game_state.attempt_spawn(WALL, [14, 1])
            # elif path_is_blocked:
            #     gamelib.debug_write('ATTACKING ::: SPLIT_SCOUT_ATTACK')
            #     self.attack_delay = 0
            #     self.attack_status = SPLIT_SCOUT_ATTACK
            #     self.split_scout_attack(game_state, playerMP, target_region)
            elif playerMP > 12:
                corner_structure = game_state.contains_stationary_unit([0, 14])
                use_demolishers = False
                count = 0
                gamelib.debug_write('ATTACKING ::: Corner Structure = ' + str(corner_structure))
                if corner_structure is None or corner_structure is False or corner_structure == SUPPORT or (corner_structure == TURRET and corner_structure.upgraded is False):
                    gamelib.debug_write('ATTACKING ::: SNEAK_ATTACK UNDEFENDED')
                    count = int(playerMP / 3) + 1
                elif (corner_structure == WALL and corner_structure.upgraded is False) or corner_structure == TURRET:
                    gamelib.debug_write('ATTACKING ::: SNEAK_ATTACK BASIC WALL/UPGRADED TURRET')
                    count = int(playerMP * 3 / 4) + 1
                elif corner_structure.upgraded:
                    gamelib.debug_write('ATTACKING ::: SNEAK_ATTACK USING DEMOLISHERS')
                    count = int((playerMP * 3 / 4) / 3)
                    use_demolishers = True
                self.build_exceptions = [[0, 13], [1, 13], [1, 12], [2, 12]]
                self.attack_delay = 0
                self.attack_status = SPLIT_SCOUT_ATTACK
                spawn_loc1 = [15, 1]   
                spawn_loc2 = [16, 2]
                game_state.attempt_spawn(WALL, [16, 3])
                if use_demolishers:
                    game_state.attempt_spawn(WALL, [6, 9])
                    game_state.attempt_spawn(DEMOLISHER, [4, 9], count)
                    game_state.attempt_spawn(SCOUT, spawn_loc1, playerMP - count * 3)
                else:
                    game_state.attempt_spawn(SCOUT, spawn_loc1, count)
                    game_state.attempt_spawn(SCOUT, spawn_loc2, playerMP - count)
                # not blocked or underdefense 
            else:
                gamelib.debug_write('ATTACKING ::: NO_ATTACK')
                gamelib.debug_write('ATTACKING ::: Enemy MP = ' + str(enemyMP))
                gamelib.debug_write('ATTACKING ::: Threshold = ' + str(max(9, min(30, game_state.turn_number * 0.75))))
                self.attack_status = NO_ATTACK
                self.build_exceptions = [] 
            if enemyMP >= max(9, min(30, interceptor_check)) and self.attack_status == NO_ATTACK and game_state.turn_number % 2 == 0:
                # spawn intercepters
                gamelib.debug_write('ATTACKING ::: INTERCEPTING')
                locations = [[10, 3], [17, 3]]
                count = max(1, int(enemyMP / 12))
                game_state.attempt_spawn(WALL, [13, 1])
                self.build_exceptions = [[6, 9]]
                game_state.attempt_spawn(INTERCEPTOR, locations, count)
        elif enemyMP >= max(9, min(30, interceptor_check)) and self.attack_status == NO_ATTACK and game_state.turn_number % 2 == 0:
            # spawn intercepters
            locations = [[10, 3], [17, 3]]
            count = max(1, int(enemyMP / 12))
            game_state.attempt_spawn(WALL, [13, 1])
            self.build_exceptions = [[6, 9]]
            game_state.attempt_spawn(INTERCEPTOR, locations, count)
        else: 
            gamelib.debug_write('ATTACKING ::: NO_ATTACK')
            gamelib.debug_write('ATTACKING ::: Enemy MP = ' + str(enemyMP))
            gamelib.debug_write('ATTACKING ::: Threshold = ' + str(max(9, min(30, game_state.turn_number * 0.75))))
            self.attack_status = NO_ATTACK
            self.build_exceptions = [] 


    def all_core_defenses_built(self, game_state):
        for item in self.core_queue:
            for loc in item.iloc:
                if game_state.contains_stationary_unit(loc) is False:
                    return False
        return True



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
        safest_path = []
        safest_point_threat = math.inf
        for deploy_loc in deploy_locations:
            path = game_state.find_path_to_edge(deploy_loc)
            if path is None or len(path) == 0:
                gamelib.debug_write('Error: Path was None or empty list')
            elif self.check_path_blocked(game_state, deploy_loc) is True:
                continue
            else: 
                path_threat = 0
                for path_loc in path:
                    path_threat += self.threat_map[path_loc[0]][path_loc[1]]
                if path_threat < safest_point_threat or (path_threat == safest_point_threat and len(path) < len(safest_path)):
                    safest_point = deploy_loc
                    safest_path = path
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


    """ Return true if enemy has blocked all paths to their edge """
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
        
        least_defended_region = self.CSA(game_state)['min_td']

        scout_deploy_locs = []
        demolisher_deploy_locs = []

        playerMP = int(game_state.get_resource(MP, 0))

        if least_defended_region == 'left':
            scout_deploy_locs = [14, 0]
            demolisher_deploy_locs = [0, 13]
            demolisher_count = int((playerMP / 2 - (playerMP / 2) % 3) / 3)
            scout_count = playerMP - demolisher_count * 3
            # Avi will work on getting the right walls removed
            game_state.attempt_spawn(DEMOLISHER, demolisher_deploy_locs, demolisher_count)
            game_state.attempt_spawn(SCOUT, scout_deploy_locs, scout_count)
        elif least_defended_region == 'right':
            scout_deploy_locs = [13, 0]
            demolisher_deploy_locs = [27, 13]
            demolisher_count = int((playerMP / 2 - (playerMP / 2) % 3) / 3)
            scout_count = playerMP - demolisher_count * 3
            game_state.attempt_spawn(DEMOLISHER, demolisher_deploy_locs, demolisher_count)
            game_state.attempt_spawn(SCOUT, scout_deploy_locs, scout_count)
        elif least_defended_region == 'midleft':
            demolisher_deploy_locs = [22, 8]
            wall_locations = [[21, 10], [20, 10], [19, 10], [18, 10], [17, 10]]
            demolisher_count = int(playerMP / 3)
            game_state.attempt_spawn(WALL, wall_locations)
            game_state.attempt_spawn(DEMOLISHER, demolisher_deploy_locs, demolisher_count)
        elif least_defended_region == 'midright':
            # 5 walls from 6 to 10, all with y-coord of 10
            wall_locations = [[6, 10], [7, 10], [8, 10], [9, 10], [10, 10]]
            demolisher_deploy_locs = [5, 8]
            demolisher_count = int(playerMP / 3)
            game_state.attempt_spawn(WALL, wall_locations)
            game_state.attempt_spawn(DEMOLISHER, demolisher_deploy_locs, demolisher_count)

        # spawn_count = game_state.attempt_spawn(SCOUT, deploy_point, attack_size)
        # if (spawn_count < attack_size):
        #     gamelib.debug_write('ERROR: Num spawned is {} but {} MP available'.format(spawn_count, game_state.get_resource(MP, 0)))
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
