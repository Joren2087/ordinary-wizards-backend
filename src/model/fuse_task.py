from sqlalchemy import ForeignKey, BigInteger, CheckConstraint, Integer, Column, DateTime
from sqlalchemy.orm import mapped_column, Mapped

from src.model.task import Task


class FuseTask(Task):
    """
    A FuseTask is a task that represents the fusion of two gems inside a Fuse Table Building
    To retrieve the building this task is associated with, use the working_building attribute
    """
    __tablename__ = 'fuse_task'

    id: Mapped[int] = mapped_column(BigInteger, ForeignKey('task.id', ondelete='cascade', onupdate='cascade'), primary_key=True)

    crystal_amount: Mapped[int] = Column(Integer, CheckConstraint('crystal_amount >= 0'), nullable=False)


    def __init__(self, endtime: DateTime, crystal_amount: int, island_id: int = None, working_building: "FuseTableBuilding" = None):
        """
        Initialize the fuse task object
        :param endtime: The time when the task should end
        :param crystal_amount: The amount of crystals used for the fusion
        :param fuse_table_building: The building that the fusion is taking place in
        """
        super().__init__(endtime, island_id, working_building=working_building)
        if crystal_amount < 0:
            raise ValueError("Crystal amount must be greater than or equal to 0")

        self.crystal_amount = crystal_amount

    def update(self, data: dict):
        """
        Update the fuse task with new data
        Note: no attributes of FuseTask are allowed to be updated, this is just a super call.
        :param data: The new data
        :return:
        """
        super().update(data)


    __mapper_args__ = {
        'polymorphic_identity': 'fuse_task'
    }