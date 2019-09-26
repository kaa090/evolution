import numpy as np
import copy

NORD, NORDOST, OST, SUDOST, SUD, SUDWEST, WEST, NORDWEST = 0, 1, 2, 3, 4, 5, 6, 7
DIRECTIONS = 8

WORLD_X = 10
WORLD_Y = 10
CREATURES = 1
SURVIVORS = 2
CHILDS = 0
FOODS = 10
POISONS = 10

# WORLD_X = 40
# WORLD_Y = 20
# CREATURES = 64
# SURVIVORS = 8
# CHILDS = 8
# FOODS = 60
# POISONS = 60

EMPTIES = WORLD_X * WORLD_Y - CREATURES - FOODS - POISONS

EPOCH = 100
MUTATION = 2

HEALTH = 100
FOOD_HEALTH = 10
COST_OF_TURN = 1

DNA_SIZE = 64
EMPTY_CODE = 0
CREATURE_CODE = 1
FOOD_CODE = 2
POISON_CODE = 3


class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __add__(self, p):
        return Point(self.x + p.x, self.y + p.y)

    def __sub__(self, p):
        return Point(self.x - p.x, self.y - p.y)

    def __str__(self):
        return '({}, {})'.format(self.x, self.y)


class World:
    def __init__(self):
        self.year = 0
        self.map = np.ndarray(shape=(WORLD_Y, WORLD_X))
        self.creatures = []
        self.generate_map()

    def __str__(self):
        my_str = str(self.map)
        for creature in self.creatures:
            my_str += '\n' + str(creature)
        return my_str

    def generate_map(self):
        creatures = np.full(CREATURES, CREATURE_CODE)
        food = np.full(FOODS, FOOD_CODE)
        poison = np.full(POISONS, POISON_CODE)
        empty = np.full(EMPTIES, EMPTY_CODE)
        self.map = np.concatenate((creatures, food, poison, empty))
        np.random.shuffle(self.map)
        self.map = self.map.reshape(WORLD_Y, WORLD_X)

    def populate_creatures(self, creatures):
        self.creatures = creatures

        if len(self.creatures) == 0:
            for i in range(CREATURES):
                self.creatures.append(Creature(str(i), Point(0, 0)))

        k = 0
        for i, j in np.ndindex(self.map.shape):
            if self.map[i][j] == CREATURE_CODE:
                self.creatures[k].point.x = j
                self.creatures[k].point.y = i
                k += 1

    def run_creatures(self):
        for self.year in range(EPOCH):
            print("year =", self.year)
            for i, creature in enumerate(self.creatures):
                creature.run(self)
                print(creature)
                if creature.health <= 0:
                    self.creatures.pop(i)

            if len(self.creatures) == SURVIVORS:
                self.next_generation()

    def next_generation(self):
        print("#######################################")
        childs = []
        for creature in self.creatures:
            childs.extend(creature.make_childs())
        self.creatures.extend(childs)


class Creature:
    def __init__(self, name, point, dna=[]):
        self.name = name
        self.age = 0
        self.health = HEALTH
        self.point = point
        self.eye = np.random.choice([NORD, NORDOST, OST, SUDOST, SUD, SUDWEST, WEST, NORDWEST], 1)
        if len(dna) != 0:
            self.DNA = dna
        else:
            self.DNA = np.random.randint(0, DNA_SIZE, DNA_SIZE)
        self.CS_IP = 0
        self.history = ""

    def __str__(self):
        return '{}:\tage = {}, health = {}, coords = {}, eye = {}, CS_IP = {}' \
            .format(self.name, self.age, self.health, self.point, self.eye, self.CS_IP)

    def get_point_from_command(self, command):
        direction = command % DIRECTIONS
        new_point = copy.copy(self.point)

        if direction == NORDWEST or direction == NORD or direction == NORDOST:
            new_point.y += 1
        elif direction == SUDWEST or direction == SUD or direction == SUDOST:
            new_point.y -= 1

        if direction == NORDWEST or direction == WEST or direction == SUDWEST:
            new_point.x -= 1
        elif direction == NORDOST or direction == OST or direction == SUDOST:
            new_point.x += 1

        new_point.x %= WORLD_X
        new_point.y %= WORLD_Y

        return new_point

    def increment_cs_ip(self, point_type):
        if point_type == EMPTY_CODE:
            self.CS_IP += 1
        elif point_type == CREATURE_CODE:
            self.CS_IP += 2
        elif point_type == FOOD_CODE:
            self.CS_IP += 3
        elif point_type == POISON_CODE:
            self.CS_IP += 4

    def move(self, point, world):
        self.history += '\tmove to {}'.format(point)

        if world.map[point.y][point.x] == EMPTY_CODE:
            world.map[self.point.y][self.point.x] = EMPTY_CODE
            world.map[point.y][point.x] = CREATURE_CODE
            self.point = point
        elif world.map[point.y][point.x] == FOOD_CODE:
            world.map[self.point.y][self.point.x] = EMPTY_CODE
            world.map[point.y][point.x] = CREATURE_CODE
            self.point = point
            self.health += FOOD_HEALTH
        elif world.map[point.y][point.x] == POISON_CODE:
            world.map[self.point.y][self.point.x] = EMPTY_CODE
            world.map[point.y][point.x] = EMPTY_CODE
            self.health = 0

    def eat_or_defuse(self, point, world):
        self.history += '\teat_or_defuse from {}'.format(point)

        if world.map[point.y][point.x] == FOOD_CODE:
            world.map[point.y][point.x] = EMPTY_CODE
            self.health += FOOD_HEALTH
        elif world.map[point.y][point.x] == POISON_CODE:
            world.map[point.y][point.x] = FOOD_CODE

    def look(self, point):
        self.history += '\tlook to {}'.format(point)

    def turn(self, direction):
        self.history += '\tturn by {}'.format(direction)

        self.eye += direction
        self.eye %= DIRECTIONS

    def make_childs(self):
        print('{}:\tmake_childs'.format(self.name))

        childs = []
        for i in range(CHILDS):
            childs.append(Creature(str(self.name) + '.' + str(i), Point(0, 0), self.DNA))

        return childs

    def run(self, world):
        for _ in range(10):
            if self.DNA[self.CS_IP] < 4 * DIRECTIONS:
                point = self.get_point_from_command(self.DNA[self.CS_IP])
                command = self.DNA[self.CS_IP]
                self.increment_cs_ip(world.map[point.y][point.x])

                if command < DIRECTIONS:
                    self.move(point, world)
                    break
                elif DIRECTIONS <= command < 2 * DIRECTIONS:
                    self.eat_or_defuse(point, world)
                    break
                elif 2 * DIRECTIONS <= command < 3 * DIRECTIONS:
                    self.look(point)
                elif 3 * DIRECTIONS <= command < 4 * DIRECTIONS:
                    self.turn(command % DIRECTIONS)
            else:
                self.CS_IP += self.DNA[self.CS_IP]
                self.CS_IP %= DNA_SIZE

        self.age += 1
        self.health -= COST_OF_TURN


myWorld = World()
myWorld.populate_creatures(myWorld.creatures)
print(myWorld)
myWorld.run_creatures()
print("end")
print(myWorld)
