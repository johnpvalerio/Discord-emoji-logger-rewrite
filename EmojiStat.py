class EmojiStat:
    def __init__(self, emoji_obj, instance_count=0, total_count=0, last_used=None):
        self.emoji_obj = emoji_obj  # Discord Emoji object
        self.instance_count = instance_count  # All emote use in a msg = 1 count
        self.total_count = total_count  # All emote use in a msg
        self.last_used = last_used  # Datetime last used
