from mongoengine import Document, IntField, ReferenceField


class ChatData(Document):
    chat_id = IntField(required=True)


class KarmaValue(Document):
    chat = ReferenceField(ChatData, required=True)
    user_id = IntField(ChatData, required=True, unique_with='chat')
    karma_value = IntField(default=0)

