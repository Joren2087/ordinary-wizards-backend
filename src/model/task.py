import datetime

from flask import current_app
from sqlalchemy import BigInteger, DateTime, Column, func, String, Boolean, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, declared_attr, relationship


class Task(current_app.db.Model):
    """
    A Task is an object to keep track of running 'single task'. Periodic tasks are handeled differently, see SCHEDULING.md for more information.
    This class has a polymorphic relationship (not total!) with other tasks, such as BuildingUpgradeTask

    A task on its own can mean anything.
    A building that's in construction or in upgrade are represented by a BuildingUpgradeTask
    """


    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    starttime: Mapped[DateTime] = Column(DateTime(timezone=True), nullable=False)
    endtime: Mapped[DateTime] = Column(DateTime(timezone=True), nullable=False)

    type: Mapped[str] = Column(String(32), nullable=False) # Keep track of polymorphic identities

    # The island that the task is associated with
    island_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('island.owner_id'), nullable=False)
    @declared_attr
    def island(self):
        return relationship("Island", back_populates="tasks")

    # The building that the task is associated with, may be None
    working_building: Mapped['Placeable'] = relationship('Placeable', back_populates='task', uselist=False, cascade="save-update, merge")


    def __init__(self, endtime: DateTime, island_id: int = None, working_building: 'Building' = None):
        """
        Initialize the task object
        :param endtime: The time when the task should end
        """
        self.starttime = datetime.datetime.now(tz=endtime.tzinfo)
        self.endtime = endtime
        self.island_id = island_id
        self.working_building = working_building


    def update(self, data: dict):
        """
        Update the task with the new endtime
        :param data:
        :return:
        """
        self.endtime = data.get('endtime', self.endtime)
        self.working_building = data.get('working_building', self.working_building)


    def is_over(self) -> bool:
        """
        Check if the task is done
        :return: True if the task is done, False otherwise
        """
        return self.endtime < datetime.datetime.now(tz=self.endtime.tzinfo)


    __mapper_args__ = {
        'polymorphic_identity': 'task',
        'polymorphic_on': type
    }