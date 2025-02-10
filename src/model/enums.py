from enum import Enum


class TowerBuildingType(Enum):
    """
    An enum for the different types of towers
    """
    MAGIC = 'magic'

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


class MineBuildingType(Enum):
    """
    An enum for the different types of mines
    """
    CRYSTAL = 'crystal'

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


class GemType(Enum):
    """
    An enum for the different types of gems
    """
    JUMMY = 'jummy'
    RUBY = 'ruby'
    SAPPHIRE = 'sapphire'
    DIAMOND = 'diamond'
    EMERALD = 'emerald'
    AMETHYST = 'amethyst'
    AMBER = 'amber'


    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


class BlueprintType(Enum):
    """
    An enum for the different types of blueprints associated with their id in the db
    """
    ALTAR = 1
    MINE = 2
    TOWER = 3
    FUSE_TABLE = 4
    WARRIOR_HUT = 5
    WALL = 8

    # Props
    BUSH = 6
    TREE = 7
    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    def __eq__(self, other):
        if isinstance(other, BlueprintType):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        return False


