class EmojiStat:
    def __init__(self, emoji_obj, instance_count=0, total_count=0):
        self.emoji_obj = emoji_obj
        self.instance_count = instance_count
        self.total_count = total_count
        self.instance_increase = 0
        self.total_increase = 0
