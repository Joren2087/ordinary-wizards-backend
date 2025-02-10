from flask import current_app
from sqlalchemy import Column, BigInteger, ForeignKey, SmallInteger, Boolean, String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.model.player import Player


class UserSettings(current_app.db.Model):
    """
    UserSettings contains all the settings for a player
    This includes audio settings, keybinds, etc.

    Keybinds are represented as a key and a value. The key is the key code that is universally the same for each keyboard
     layout. The value is the actual symbol on that key, which may differ when using different keyboard layouts.
    """

    player_id: Mapped[int] = mapped_column("Player", ForeignKey("player.user_profile_id"), primary_key=True)
    player: Mapped[Player] = relationship(back_populates="user_settings")

    # The player's settings
    audio_volume: Mapped[int] = Column(SmallInteger, CheckConstraint("audio_volume >= 0 AND audio_volume <= 100"), nullable=False, default=100)
    performance: Mapped[int] = Column(SmallInteger, CheckConstraint("performance >= 0 AND performance <= 2"), nullable=False, default=2)
    selected_cursor: Mapped[int] = Column(SmallInteger, CheckConstraint("selected_cursor >= 0 AND selected_cursor <= 3"), nullable=False, default=0)
    horz_sensitivity: Mapped[int] = Column(SmallInteger, CheckConstraint("horz_sensitivity >= 0 AND horz_sensitivity <= 100"), nullable=False, default=50)
    vert_sensitivity: Mapped[int] = Column(SmallInteger, CheckConstraint("vert_sensitivity >= 0 AND vert_sensitivity <= 100"), nullable=False, default=50)

    # Keybinds
    move_fwd_key: Mapped[str] = Column(String(12), nullable=False, default='KeyW')
    move_fwd_val: Mapped[str] = Column(String(12), nullable=True)
    move_bkwd_key: Mapped[str] = Column(String(12), nullable=False, default='KeyS')
    move_bkwd_val: Mapped[str] = Column(String(12), nullable=True)
    move_left_key: Mapped[str] = Column(String(12), nullable=False, default='KeyA')
    move_left_val: Mapped[str] = Column(String(12), nullable=True)
    move_right_key: Mapped[str] = Column(String(12), nullable=False, default='KeyD')
    move_right_val: Mapped[str] = Column(String(12), nullable=True)
    jump_key: Mapped[str] = Column(String(12), nullable=False, default='Space')
    jump_val: Mapped[str] = Column(String(12), nullable=True)
    interact_key: Mapped[str] = Column(String(12), nullable=False, default='KeyE')
    interact_val: Mapped[str] = Column(String(12), nullable=True)
    eat_key: Mapped[str] = Column(String(12), nullable=False, default='KeyQ')
    eat_val: Mapped[str] = Column(String(12), nullable=True)
    chat_key: Mapped[str] = Column(String(12), nullable=False, default='KeyC')
    chat_val: Mapped[str] = Column(String(12), nullable=True)
    slot_1_key: Mapped[str] = Column(String(12), nullable=False, default='Digit1')
    slot_1_val: Mapped[str] = Column(String(12), nullable=True)
    slot_2_key: Mapped[str] = Column(String(12), nullable=False, default='Digit2')
    slot_2_val: Mapped[str] = Column(String(12), nullable=True)
    slot_3_key: Mapped[str] = Column(String(12), nullable=False, default='Digit3')
    slot_3_val: Mapped[str] = Column(String(12), nullable=True)
    slot_4_key: Mapped[str] = Column(String(12), nullable=False, default='Digit4')
    slot_4_val: Mapped[str] = Column(String(12), nullable=True)
    slot_5_key: Mapped[str] = Column(String(12), nullable=False, default='Digit5')
    slot_5_val: Mapped[str] = Column(String(12), nullable=True)
    sprint_key: Mapped[str] = Column(String(12), nullable=False, default='ShiftLeft')
    sprint_val: Mapped[str] = Column(String(12), nullable=True)

    def __init__(self, player_id: int, audio_volume: int = 100, performance: int = 2, selected_cursor: int = 0, horz_sensitivity: int = 50, vert_sensitivity: int = 50,
                    move_fwd_key: str = 'KeyW', move_fwd_val: str = None, move_bkwd_key: str = 'KeyS', move_bkwd_val: str = None, move_left_key: str = 'KeyA', move_left_val: str = None,
                    move_right_key: str = 'KeyD', move_right_val: str = None, jump_key: str = 'Space', jump_val: str = None, interact_key: str = 'KeyE', interact_val: str = None,
                    eat_key: str = 'KeyQ', eat_val: str = None, chat_key: str = 'KeyC', chat_val: str = None, slot_1_key: str = 'Digit1', slot_1_val: str = None, slot_2_key: str = 'Digit2',
                    slot_2_val: str = None, slot_3_key: str = 'Digit3', slot_3_val: str = None, slot_4_key: str = 'Digit4', slot_4_val: str = None, slot_5_key: str = 'Digit5', slot_5_val: str = None,
                    sprint_key: str = 'ShiftLeft', sprint_val: str = None):
        """
        Initialize the UserSettings object
        """
        if audio_volume < 0 or audio_volume > 100:
            raise ValueError("audio_volume must be in the range [0,100]")
        if performance < 0 or performance > 2:
            raise ValueError("performance must be in the range [0,2]")
        if selected_cursor < 0 or selected_cursor > 3:
            raise ValueError("selected_cursor must be in the range [0,3]")
        if horz_sensitivity < 0 or horz_sensitivity > 100:
            raise ValueError("horz_sensitivity must be in the range [0,100]")
        if vert_sensitivity < 0 or vert_sensitivity > 100:
            raise ValueError("vert_sensitivity must be in the range [0,100]")

        self.player_id = player_id
        self.audio_volume = audio_volume
        self.performance = performance
        self.selected_cursor = selected_cursor
        self.horz_sensitivity = horz_sensitivity
        self.vert_sensitivity = vert_sensitivity

        self.move_fwd_key = move_fwd_key
        self.move_fwd_val = move_fwd_val
        self.move_bkwd_key = move_bkwd_key
        self.move_bkwd_val = move_bkwd_val
        self.move_left_key = move_left_key
        self.move_left_val = move_left_val
        self.move_right_key = move_right_key
        self.move_right_val = move_right_val
        self.jump_key = jump_key
        self.jump_val = jump_val
        self.interact_key = interact_key
        self.interact_val = interact_val
        self.eat_key = eat_key
        self.eat_val = eat_val
        self.chat_key = chat_key
        self.chat_val = chat_val
        self.slot_1_key = slot_1_key
        self.slot_1_val = slot_1_val
        self.slot_2_key = slot_2_key
        self.slot_2_val = slot_2_val
        self.slot_3_key = slot_3_key
        self.slot_3_val = slot_3_val
        self.slot_4_key = slot_4_key
        self.slot_4_val = slot_4_val
        self.slot_5_key = slot_5_key
        self.slot_5_val = slot_5_val
        self.sprint_key = sprint_key
        self.sprint_val = sprint_val


    def update(self, data: dict):
        """
        Update the UserSettings with the given data
        :param data: The data to update the UserSettings with
        """
        if data.get('audio_volume', self.audio_volume) < 0 or data.get('audio_volume', self.audio_volume) > 100:
            raise ValueError("audio_volume must be in the range [0,100]")
        if data.get('performance', self.performance) < 0 or data.get('performance', self.performance) > 2:
            raise ValueError("performance must be in the range [0,2]")
        if data.get('selected_cursor', self.selected_cursor) < 0 or data.get('selected_cursor', self.selected_cursor) > 3:
            raise ValueError("selected_cursor must be in the range [0,3]")
        if data.get('horz_sensitivity', self.horz_sensitivity) < 0 or data.get('horz_sensitivity', self.horz_sensitivity) > 100:
            raise ValueError("horz_sensitivity must be in the range [0,100]")
        if data.get('vert_sensitivity', self.vert_sensitivity) < 0 or data.get('vert_sensitivity', self.vert_sensitivity) > 100:
            raise ValueError("vert_sensitivity must be in the range [0,100]")

        self.audio_volume = data.get('audio_volume', self.audio_volume)
        self.performance = data.get('performance', self.performance)
        self.selected_cursor = data.get('selected_cursor', self.selected_cursor)
        self.horz_sensitivity = data.get('horz_sensitivity', self.horz_sensitivity)
        self.vert_sensitivity = data.get('vert_sensitivity', self.vert_sensitivity)

        self.move_fwd_key = data.get('move_fwd_key', self.move_fwd_key)
        self.move_fwd_val = data.get('move_fwd_val', self.move_fwd_val)
        self.move_bkwd_key = data.get('move_bkwd_key', self.move_bkwd_key)
        self.move_bkwd_val = data.get('move_bkwd_val', self.move_bkwd_val)
        self.move_left_key = data.get('move_left_key', self.move_left_key)
        self.move_left_val = data.get('move_left_val', self.move_left_val)
        self.move_right_key = data.get('move_right_key', self.move_right_key)
        self.move_right_val = data.get('move_right_val', self.move_right_val)
        self.jump_key = data.get('jump_key', self.jump_key)
        self.jump_val = data.get('jump_val', self.jump_val)
        self.interact_key = data.get('interact_key', self.interact_key)
        self.interact_val = data.get('interact_val', self.interact_val)
        self.eat_key = data.get('eat_key', self.eat_key)
        self.eat_val = data.get('eat_val', self.eat_val)
        self.chat_key = data.get('chat_key', self.chat_key)
        self.chat_val = data.get('chat_val', self.chat_val)
        self.slot_1_key = data.get('slot_1_key', self.slot_1_key)
        self.slot_1_val = data.get('slot_1_val', self.slot_1_val)
        self.slot_2_key = data.get('slot_2_key', self.slot_2_key)
        self.slot_2_val = data.get('slot_2_val', self.slot_2_val)
        self.slot_3_key = data.get('slot_3_key', self.slot_3_key)
        self.slot_3_val = data.get('slot_3_val', self.slot_3_val)
        self.slot_4_key = data.get('slot_4_key', self.slot_4_key)
        self.slot_4_val = data.get('slot_4_val', self.slot_4_val)
        self.slot_5_key = data.get('slot_5_key', self.slot_5_key)
        self.slot_5_val = data.get('slot_5_val', self.slot_5_val)
        self.sprint_key = data.get('sprint_key', self.sprint_key)
        self.sprint_val = data.get('sprint_val', self.sprint_val)
