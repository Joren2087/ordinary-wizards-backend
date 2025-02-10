from flask import current_app
from sqlalchemy import SmallInteger, String, Column, Integer
from sqlalchemy.orm import mapped_column, Mapped

from src.model.enums import BlueprintType


class Blueprint(current_app.db.Model):
    """
    A blueprint object is a representation of a building that can be built in the game
    """

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str] = Column(String(32), nullable=False, unique=True)
    description: Mapped[str] = Column(String(256), nullable=False, default='')
    cost: Mapped[int] = Column(Integer, nullable=False, default=0)
    buildtime: Mapped[int] = Column(Integer, nullable=False, default=0) # in seconds


    def __init__(self, id: int = None, name: str = None, description: str = None, cost: int = 0, buildtime: int = 0):
        """
        Initialize the blueprint object
        :param id: The id of the blueprint
        :param name: The name of the blueprint (eg the building it creates)
        :param description: The description of the blueprint (eg what does the building it creates do)
        :param cost: The cost to build the building of this blueprint
        :param buildtime: The time it takes to build the building of this blueprint
        """
        if cost < 0:
            raise ValueError("Cost must be greater than or equal to 0")
        if buildtime < 0:
            raise ValueError("Buildtime must be greater than or equal to 0")

        self.id = id
        self.name = name
        self.description = description
        self.cost = cost
        self.buildtime = buildtime


    def update(self, data: dict):
        """
        Update the blueprint object with the given data
        :param data:
        :return:
        """
        if data.get('cost', self.cost) < 0:
            raise ValueError("Cost must be greater than or equal to 0")
        if data.get('buildtime', self.buildtime) < 0:
            raise ValueError("Buildtime must be greater than or equal to 0")

        self.name = data.get('name', self.name)
        self.description = data.get('description', self.description)
        self.cost = data.get('cost', self.cost)
        self.buildtime = data.get('buildtime', self.buildtime)

    def get_type(self) -> BlueprintType:
        """
        Get the type of the blueprint
        :return: The type of the blueprint
        """
        return BlueprintType(self.id)




