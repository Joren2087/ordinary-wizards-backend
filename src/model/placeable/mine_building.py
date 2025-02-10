import datetime

from sqlalchemy import BigInteger, ForeignKey, Column, Enum as SqlEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.model.enums import MineBuildingType, BlueprintType
from src.model.placeable.building import Building


class MineBuilding(Building):
    """
    A building that can mine crystals (or maybe other resources) over time
    The mined resources can be collected by the player. The amount mined increases over time depending on the
    running tasks. It is also capped based on the level of the building
    """
    placeable_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('building.placeable_id'), primary_key=True)

    mine_type: Mapped[MineBuildingType] = Column(SqlEnum(MineBuildingType), nullable=False, default='crystal')
    last_collected: Mapped[DateTime] = Column(DateTime, nullable=False, default=0)


    def __init__(self, island_id:int = 0, x:int = 0, z: int = 0, level: int = 0, mine_type: str = 'crystal', rotation: int = 0, last_collected: DateTime = None) -> None:
        """
        Create a new mine building object with the given parameters
        :param island_id: The id of the island that this building belongs to
        :param x: The x position of the building on the grid
        :param z: The z position of the building on the grid
        :param level: The level of the building
        :param mine_type: The type of the mine (default is 'crystal')
        :param last_collected: The last time the mine contents were collected
        :param rotation: The rotation of the building (0=North, 1=East, 2=South, 3=West)
        """
        super().__init__(island_id, xpos=x, zpos=z, level=level, blueprint_id=BlueprintType.MINE.value, rotation=rotation)
        if not MineBuildingType.has_value(mine_type):
            raise ValueError('Invalid mine_type')

        self.mine_type = MineBuildingType[mine_type.upper()]
        self.last_collected = last_collected if last_collected is not None else datetime.datetime(1970, 1, 1, 0, 0)


    def update(self, data: dict):
        """
        Update the mine building object with the given data
        :param data: The new data. In this class, only the mine_type can be updated
        (it does call super().update(), so check the docs over there as well)
        :return:
        """
        super().update(data)
        if 'mine_type' in data:
            if not MineBuildingType.has_value(data.get('mine_type', self.mine_type)):
                raise ValueError('Invalid mine_type')

            # Ignore pycharm warning, it's wrong
            self.mine_type = MineBuildingType[data.get('mine_type').upper()]

        self.last_collected = data.get('last_collected', self.last_collected)


    __mapper_args__ = {
        'polymorphic_identity': 'mine_building'
    }
