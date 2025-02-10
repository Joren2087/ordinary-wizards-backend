from typing import List

from sqlalchemy import Column, SmallInteger, Integer, DateTime, BigInteger, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, relationship, mapped_column

from src.model.task import Task


class BuildingUpgradeTask(Task):
    """
    A BuildingUpgradeTask is a task that represents the construction or an upgrade of a building
    """
    __tablename__ = 'building_upgrade_task'


    id: Mapped[int] = mapped_column(BigInteger, ForeignKey('task.id', ondelete='cascade', onupdate='cascade'), primary_key=True)

    to_level: Mapped[int] = Column(SmallInteger, CheckConstraint('to_level >= 0'), nullable=False)
    used_crystals: Mapped[int] = Column(Integer, CheckConstraint('used_crystals >= 0'), nullable=False)

    building_minions: Mapped[List["BuilderMinion"]] = relationship(back_populates="builds_on", uselist=True)


    def __init__(self, endtime: DateTime, working_building: "Building", to_level: int, used_crystals: int, island_id: int = None):
        """
        Initialize the building upgrade task object
        :param endtime: The time when the task should end
        :param working_building: The building that should be upgraded
        :param to_level: The level that the building should be upgraded to
        :param used_crystals: The amount of crystals used for the upgrade, will be rewarded back to the player if the task is cancelled
        """
        super().__init__(endtime, island_id or working_building.island_id, working_building=working_building)
        if to_level < 0:
            raise ValueError("Level must be greater than or equal to 0")
        if used_crystals < 0:
            raise ValueError("Used crystals must be greater than or equal to 0")

        self.to_level = to_level
        self.used_crystals = used_crystals

    def update(self, data: dict):
        """
        Update the building upgrade task with new data
        Note: no attributes of BuildingUpgradeTask are allowed to be updated, this is just a super call.
        Update working minions though the building_minion endpoint
        :param data: The new data
        :return:
        """
        super().update(data)


    __mapper_args__ = {
        'polymorphic_identity': 'building_upgrade_task'
    }