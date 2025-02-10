from flask import current_app
from sqlalchemy import BigInteger, String, Column, Integer, SmallInteger, ForeignKey, CheckConstraint, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship, declared_attr

from src.model.upgrade_task import BuildingUpgradeTask
from src.model.task import Task


class Placeable(current_app.db.Model):
    """
    A placeable is an abstract class for all placeable (building& props)
    """
    __tablename__ = 'placeable'

    placeable_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    island_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('island.owner_id'), nullable=False)

    @declared_attr
    def island(self):
        return relationship("Island", back_populates="placeables")

    type: Mapped[str] = Column(String(32))

    xpos: Mapped[int] = Column(SmallInteger(), CheckConstraint('xpos >= -7 AND xpos <= 7'), nullable=False, default=0)
    zpos: Mapped[int] = Column(SmallInteger(), CheckConstraint('zpos >= -7 AND zpos <= 7'), nullable=False, default=0)

    rotation: Mapped[int] = Column(SmallInteger(), CheckConstraint('rotation >= 0 AND rotation <= 3'), nullable=False, default=0)

    blueprint_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey('blueprint.id'), nullable=False, default=0)
    blueprint: Mapped["Blueprint"] = relationship('Blueprint')

    task_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('task.id'), nullable=True)
    task: Mapped[Task] = relationship("Task", back_populates="working_building", passive_deletes=True)

    def __init__(self, island_id: int = 0, xpos: int = 0, zpos: int = 0, blueprint_id: int = 0, rotation: int = 0):
        """
        Initializes a placeable object
        :param island_id: The id of the island that this placeable belongs to
        :param xpos: The x position of the building, in the grid. So it is bound by [-7,7]
        :param zpos: The z position of the building, in the grid. So it is bound by [-7,7]
        :param blueprint_id: The id of the blueprint that builds this placeable
        :param rotation: The rotation of the building (0=North, 1=East, 2=South, 3=West)
        """
        if xpos < -7 or xpos > 7 or zpos < -7 or zpos > 7:
            raise ValueError("xpos and/or zpos is out of bounds [-7,7]")
        if rotation < 0 or rotation > 3:
            raise ValueError("rotation is out of bounds [0,3]")

        self.island_id = island_id
        self.xpos = xpos
        self.zpos = zpos
        self.blueprint_id = blueprint_id
        self.rotation = rotation


    def create_task(self, endtime: DateTime):
        """
        Create a new 'regular' task for this building
        :param endtime: The time when the task should end
        :return: The new task
        """
        task = Task(endtime, self.island_id, self)
        self.task = task
        return task

    def create_upgrade_task(self, endtime: DateTime, used_crystals: int):
        """
        Create a new upgrade task for this building
        :param endtime: The time when the task should end
        :param used_crystals: The amount of crystals used for the upgrade
        :return: The new task
        """
        task = BuildingUpgradeTask(endtime, self, self.level + 1, used_crystals)
        self.task = task
        return task


    def update(self, data: dict):
        """
        Updates the placeable object new data
        Updating the id, island_id, task_id and type are not allowed
        :param data: The new data
        :return:
        """
        if data.get('x', self.xpos) < -7 or data.get('x', self.xpos) > 7:
            raise ValueError("xpos is out of bounds [-7,7]")
        if data.get('z', self.zpos) < -7 or data.get('z', self.zpos) > 7:
            raise ValueError("zpos is out of bounds [-7,7]")
        if data.get('rotation', self.rotation) < 0 or data.get('rotation', self.rotation) > 3:
            raise ValueError("rotation is out of bounds [0,3]")

        self.xpos = data.get('x', self.xpos)
        self.zpos = data.get('z', self.zpos)
        self.rotation = data.get('rotation', self.rotation)


    __mapper_args__ = {
        'polymorphic_on': 'type'
    }
