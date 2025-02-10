from sqlalchemy import ForeignKey, BigInteger, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.model.upgrade_task import BuildingUpgradeTask
from src.model.entity import Entity


class BuilderMinion(Entity):
    """
    A builder minion is a type of entity that can be placed on an island and can build buildings.
    """
    entity_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('entity.entity_id'), primary_key=True)

    builds_on_id: Mapped[int] = mapped_column(ForeignKey("building_upgrade_task.id"), nullable=True)
    builds_on: Mapped[BuildingUpgradeTask] = relationship("BuildingUpgradeTask", back_populates="building_minions", cascade="all", passive_deletes=True)

    def __init__(self, island_id: int = 0, x: int = 0, y: int = 0, z: int = 0, level: int = 0, builds_on: BuildingUpgradeTask = None):
        """
        Create a new builder minion object with the given parameters
        :param island_id: The id of the island that this minion belongs to
        :param x: The x position of the minion
        :param y: The y position of the minion
        :param z: The z position of the minion
        :param level: The level of the minion
        :param builds_on: The task that the minion is currently working on (optional)
        """
        super().__init__(island_id, x, y, z, level)
        self.builds_on = builds_on

    def update(self, data: dict):
        """
        Updates the builder minions' fields by a dictionary
        :param data: The data to update with. Only fields that have to be changed have to be present.
        """
        super().update(data)
        self.builds_on = data.get('builds_on', self.builds_on)


    __mapper_args__ = {
        'polymorphic_identity': 'builder_minion'
    }


