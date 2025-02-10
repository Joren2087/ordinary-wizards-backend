from flask import current_app
from sqlalchemy import Integer, Column, String, ForeignKey
from sqlalchemy.orm import Mapped



class Spell(current_app.db.Model):
    """
    A spell in the game. The set of spells is expected to be static and not change often.
    Info such as description & mana cost are stored in the client side code as these are not expected to change
    This entity exists so that we can store the name of the spell in the database and use it as a foreign key in
    other tables (such as the player ownership of spells)
    """
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String, nullable=False)


    def __init__(self, name: str):
        """
        Initializes the spell object
        :param name: The (display) name of the spell
        """
        self.name = name

    def update(self, data: dict):
        """
        Update the spell profile with new data
        :param data: The new data
        :return:
        """
        self.name = data.get('name', self.name)

    def _to_json(self):
        return {
            'id': self.id,
            'name': self.name
        }