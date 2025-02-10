from src.model.enums import BlueprintType
from src.model.placeable.building import Building


class WarriorHutBuilding(Building):
    """
    The warrior hut allows a player to spawn warriors from. The warriors can be used to attack other islands
    and/or warriors during a multiplayer game.
    It has no function in single player mode
    """

    def __init__(self, island_id: int = 0, x: int = 0, z: int = 0, level: int = 0, rotation: int = 0):
        """
        Create a new warrior hut building object with the given parameters
        :param island_id: The id of the island that this building belongs to
        :param x: The x position of the building on the grid
        :param z: The z position of the building on the grid
        :param level: The level of the building
        :param rotation: The rotation of the building (0=North, 1=East, 2=South, 3=West)
        """
        super().__init__(island_id, xpos=x, zpos=z, level=level, blueprint_id=BlueprintType.WARRIOR_HUT.value, rotation=rotation)

    def update(self, data: dict):
        """
        Update the warrior hut building object with the given data
        See the docs of the parent class for more info
        :param data: The new data
        :return:
        """
        super().update(data)

    __mapper_args__ = {
        'polymorphic_identity': 'warrior_hut_building'
    }
