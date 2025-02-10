from src.model.enums import BlueprintType
from src.model.placeable.building import Building


class WallBuilding(Building):
    """
    the wall building is a building that can be placed on the grid to divert enemy minions during multiplayer
    """

    def __init__(self, island_id: int = 0, x: int = 0, z: int = 0, level: int = 0, rotation: int = 0):
        """
        Create a new wall building object with the given parameters
        :param island_id: The id of the island that this building belongs to
        :param x: The x position of the building on the grid
        :param z: The z position of the building on the grid
        :param level: The level of the building
        :param rotation: The rotation of the building (0=North, 1=East, 2=South, 3=West)
        """
        super().__init__(island_id, xpos=x, zpos=z, level=level, blueprint_id=BlueprintType.WALL.value, rotation=rotation)

    def update(self, data: dict):
        """
        Update the wall building object with the given data
        See the docs of the parent class for more info
        :param data: The new data
        :return:
        """
        super().update(data)

    __mapper_args__ = {
        'polymorphic_identity': 'wall_building'
    }
