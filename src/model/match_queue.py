from flask import current_app


class MatchQueueEntry(current_app.db.Model):
    """
    A MatchQueueEntry is an entry in the match queue, containing a player_id
    A player_id in this table is waiting for an opponent of the same level (or close to it)
    When two players are in the match queue, they are matched together and their entries in the queue are removed
    Players are matched to each other based on their level
    """

    __tablename__ = 'match_queue'

    player_id = current_app.db.Column(current_app.db.Integer, current_app.db.ForeignKey('player.user_profile_id'), nullable=False, primary_key=True)
    player = current_app.db.relationship('Player', back_populates='match_queue_entry')

    def __init__(self, player_id):
        self.player_id = player_id