from sqlalchemy import Column, BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped

from src.model.placeable.placeable import Placeable


class Prop(Placeable):
    """
    The Prop class is a subclass of the Placeable class, representing a basic prop in the game world.
    """

    placeable_id: Mapped[int] = Column(BigInteger, ForeignKey('placeable.placeable_id'), primary_key=True)
    prop_type: Mapped[str] = Column(String(64), nullable=False)

    def __init__(self, prop_type: str, island_id: int = 0, x: int = 0, z: int = 0, blueprint_id: int = 0, rotation: int = 0):
        """
        Constructor for the Prop class
        :param prop_type: The unique identifier of the prop
        :param island_id: The id of the island that this prop belongs to
        :param xpos: The x position of the prop, in the grid. So it is bound by [-7,7]
        :param zpos: The z position of the prop, in the grid. So it is bound by [-7,7]
        :param blueprint_id: The id of the blueprint that builds this prop
        :param rotation: The rotation of the prop (0=North, 1=East, 2=South, 3=West)
        """
        super().__init__(island_id, xpos=x, zpos=z, blueprint_id=blueprint_id, rotation=rotation)
        self.prop_type = prop_type

    def update(self, data: dict):
        """
        Update the prop with the given data
        :param data: The data to update the prop with
        """
        super().update(data)
        self.prop_type = data.get('prop_type', self.prop_type)


    __mapper_args__ = {
        'polymorphic_identity': 'prop'
    }
