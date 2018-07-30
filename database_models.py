from collections import OrderedDict

import datetime
from typing import Dict, List

from mongoengine import Document, IntField, ReferenceField, StringField, DoesNotExist, EmbeddedDocumentListField, \
    EmbeddedDocument, DateTimeField


class UserInfo(EmbeddedDocument):
    user_id = IntField(required=True)
    name = StringField(required=True)

    nickname = StringField(default='')


class ChatData(Document):
    chat_id = IntField(required=True)
    user_infos = EmbeddedDocumentListField(UserInfo) # type: List[UserInfo]

    @classmethod
    def get_or_default(cls, chat_id: int):
        try:
            return cls.objects.get(chat_id=chat_id)
        except DoesNotExist:
            return ChatData(chat_id=chat_id)

    def get_names(self) -> Dict[int, str]:
        return {
            user_info.user_id: user_info.name
            for user_info in self.user_infos
        }


class KarmaUpdate(Document):
    chat = ReferenceField(ChatData, required=True)
    user_id = IntField(required=True)
    from_id = IntField(required=True)
    update_type = StringField(required=True, choices=['increase', 'decrease'])

    update_time = DateTimeField(default=datetime.datetime.now())

    @classmethod
    def _new_update(cls, chat: ChatData, user_id: int, from_id: int, update_type: str):
        cls(chat=chat, user_id=user_id, from_id=from_id, update_type=update_type).save(force_insert=True)

    @classmethod
    def give_karma(cls, chat: ChatData, user_id: int, from_id: int):
        cls._new_update(chat, user_id, from_id, 'increase')

    @classmethod
    def take_karma(cls, chat: ChatData, user_id: int, from_id: int):
        cls._new_update(chat, user_id, from_id, 'decrease')

    @classmethod
    def get_statistics(cls, chat: ChatData):
        aggregation = cls.objects.aggregate(
            {'$match': {
                'chat': chat.id
            }},
            {'$project': {
                'user_id': 1,
                'update': {
                    '$cond': {
                        'if': {'$eq': ['$update_type', 'increase']},
                        'then': 1,
                        'else': -1
                    }
                }
            }},
            {'$group': {
                '_id': '$user_id',
                'karma': {'$sum': '$update'}
            }},
            {'$sort': {
                'karma': -1
            }}
        )

        resulted_dict = OrderedDict()
        for karma in list(aggregation):
            resulted_dict[karma['_id']] = karma['karma']

        return resulted_dict
