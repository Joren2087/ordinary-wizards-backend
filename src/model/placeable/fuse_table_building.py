from src.model.enums import BlueprintType
from src.model.placeable.building import Building


class FuseTableBuilding(Building):
    """
    A fuse table allows a player to convert crystals into (random) gems
    This process requires some idle time
    """

    def __init__(self, island_id:int = 0, x: int = 0, z: int = 0, level: int = 0, rotation: int = 0):
        """
        Create a new fuse table building object with the given parameters
        :param island_id: The id of the island that this building belongs to
        :param x: THe x position of the building on the grid
        :param z: The z position of the building on the grid
        :param level: The level of the building
        :param rotation: The rotation of the building (0=North, 1=East, 2=South, 3=West)
        """
        super().__init__(island_id, xpos=x, zpos=z, level=level, blueprint_id=BlueprintType.FUSE_TABLE.value, rotation=rotation)

    def update(self, data: dict):
        """
        Update the fuse table building object with the given data
        See the docs of the parent class for more info
        :param data: THe new data
        :return:
        """
        super().update(data)

    __mapper_args__ = {
        'polymorphic_identity': 'fuse_table_building'
    }
