from flask import current_app
from sqlalchemy import BigInteger, Integer, Column, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship, declared_attr


class Entity(current_app.db.Model):
    """
    Abstract class for entities that have to be persistent (such as players, minions etc)
    In contradiction to Placable, the coordinates are absolute from in the THREE.js world and not transformed onto a grid.
    """
    __tablename__ = "entity"

    entity_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    island_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('island.owner_id'), nullable=False) # Backref to Island

    @declared_attr
    def island(self):
        return relationship("Island", back_populates="entities")

    type: Mapped[str] = Column(String(32)) # Keep track of polymorphic identities

    xpos: Mapped[int] = Column(Integer, nullable=False, default=0)
    ypos: Mapped[int] = Column(Integer, nullable=False, default=0)
    zpos: Mapped[int] = Column(Integer, nullable=False, default=0)

    level: Mapped[int] = Column(Integer, CheckConstraint('level >= 0'), nullable=False, default=0)


    def __init__(self, island_id: int = 0, xpos: int = 0, ypos: int = 0, zpos: int = 0, level: int = 0):
        """
        Initialize the entity object
        :param island_id: The id of the island that this entity belongs to
        :param xpos: The x position of the entity. Not related to the grid of the island
        :param ypos: The y position of the entity. Not related to the grid of the island
        :param zpos: The z position of the entity. Not related to the grid of the island
        :param level: The level of the entity
        """
        if level < 0:
            raise ValueError("Level must be greater than or equal to 0")

        self.island_id = island_id
        self.xpos = xpos
        self.zpos = zpos
        self.ypos = ypos
        self.level = level

    def update(self, data: dict):
        """
        Update the entity with new data
        Updating the id, island id and type are not allowed and therefore not implemented in this method
        :param data: The new data
        :return:
        """
        if data.get('level', self.level) < 0:
            raise ValueError("Level must be greater than or equal to 0")

        self.xpos = data.get('x', self.xpos)
        self.zpos = data.get('z', self.zpos)
        self.ypos = data.get('y', self.ypos)
        self.level = data.get('level', self.level)


    __mapper_args__ = {
        # 'polymporphic_abstract': True,
        'polymorphic_on': 'type'
    }
