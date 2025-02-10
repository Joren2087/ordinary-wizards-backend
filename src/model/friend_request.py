from flask import current_app
from sqlalchemy import Column, BigInteger, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship


class FriendRequest(current_app.db.Model):
    """
    A friend request is a request from one player to another to become friends
    A friend request is deleted when it is accepted (and the players are added to each other's friends list) or rejected (ignored)
    """
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    sender_id = Column(BigInteger, ForeignKey('player.user_profile_id', ondelete='CASCADE'))
    receiver_id = Column(BigInteger, ForeignKey('player.user_profile_id', ondelete='CASCADE'))

    sender = relationship("Player", foreign_keys=[sender_id])
    receiver = relationship("Player", foreign_keys=[receiver_id])

    __table_args__ = (
        UniqueConstraint('sender_id', 'receiver_id', name='unique_sender_receiver'),
        CheckConstraint('sender_id != receiver_id')
    )

    def __init__(self, sender: 'Player', receiver: 'Player'):
        """
        Initialize the friend request object
        :param sender: The player sending the request
        :param receiver: The player receiving the request
        """
        self.sender = sender
        self.receiver = receiver