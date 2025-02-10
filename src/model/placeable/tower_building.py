from sqlalchemy import BigInteger, ForeignKey, Column, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.model.enums import TowerBuildingType, BlueprintType
from src.model.placeable.building import Building


class TowerBuilding(Building):
    """
    A Tower that can attack enemy warriors and/or buildings (aka the island)
    It has no function in single player mode
    """

    placeable_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('building.placeable_id'), primary_key=True)

    tower_type: Mapped[TowerBuildingType] = Column(SqlEnum(TowerBuildingType), nullable=False, default='magic')

    def __init__(self, island_id: int = 0, tower_type: TowerBuildingType = TowerBuildingType.MAGIC, x: int = 0, z: int = 0, level: int = 0, rotation: int = 0):
        """
        Create a new tower building object with the given parameters
        :param island_id: The id of the island that this building belongs to
        :param tower_type: The type of the tower (default is 'magic')
        :param x: The x position of the building on the grid
        :param z: The z position of the building on the grid
        :param level: The level of the building
        :param rotation: The rotation of the building (0=North, 1=East, 2=South, 3=West)
        """
        super().__init__(island_id, xpos=x, zpos=z, level=level, blueprint_id=BlueprintType.TOWER.value, rotation=rotation)
        if not TowerBuildingType.has_value(tower_type):
            raise ValueError('Invalid tower_type')

        self.tower_type = TowerBuildingType[tower_type.upper()]

    def update(self, data: dict):
        """
        Update the tower building object with the given data
        Only the tower_type can be updated in this class.
        However, it does call super().update(), so check the docs over there as well
        :param data: The new data
        :return:
        """
        super().update(data)
        if not TowerBuildingType.has_value(data.get('tower_type', self.tower_type)):
            raise ValueError('Invalid tower_type')

        # Ignore pycharm warning, it's wrong
        self.tower_type = TowerBuildingType[data.get('tower_type', self.tower_type).upper()]

    __mapper_args__ = {
        'polymorphic_identity': 'tower_building'
    }
