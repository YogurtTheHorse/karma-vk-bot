import logging
from typing import Dict

from vk_api import VkApi, ApiError

from database_models import ChatData, KarmaUpdate, UserInfo
from message_parser import MessageParser

logger = logging.getLogger('handlers')

message_parser = MessageParser(command_symbol='/')

vk = None


def set_token(token: str):
    global vk
    vk_session = VkApi(token=token)
    vk = vk_session.get_api()


def get_user_id(user_data: str) -> str:
    return ''.join(c for c in user_data.split('|')[0] if c.isdigit()) or 0


def show_stats(message: Dict, chat_data: ChatData):
    stats = KarmaUpdate.get_statistics(chat_data)

    if len(stats) == 0:
        return 'No karma here'

    names = chat_data.get_names()

    karma_string = '\n'.join(
        f'{names[user_id]}: {stats[user_id]}'
        for user_id in stats
        if user_id in names
    )

    return f'Karma is here.\n\n{karma_string}'


def give_karma(message: Dict, chat_data: ChatData, user_data: str):
    increases, decreases = KarmaUpdate.count_today_karma_in_chat(chat_data, message['from_id'])

    if increases < 3:
        user_id = get_user_id(user_data)

        KarmaUpdate.give_karma(chat_data, int(user_id), message['from_id'])
        return 'ok'
    else:
        return 'maybe tomorrow.'


# TODO: Remove code duplication
def remove_karma(message: Dict, chat_data: ChatData, user_data: str):
    increases, decreases = KarmaUpdate.count_today_karma_in_chat(chat_data, message['from_id'])

    if decreases < 3:
        user_id = get_user_id(user_data)

        KarmaUpdate.take_karma(chat_data, int(user_id), message['from_id'])
        return 'ok'
    else:
        return 'maybe tomorrow.'


message_parser.add_command(
    'stats',
    action=show_stats,
    help_message='Shows karma stats'
)
message_parser.add_command(
    'karma',
    action=give_karma,
    help_message='Adds karma',
    args_description='id or mention'
)
message_parser.add_command(
    'dekarm',
    action=remove_karma,
    help_message='Decreases karma',
    args_description='id or mention'
)


def handle_vk_message(message: Dict):
    logger.debug(f'Got message {message}.')

    answer = None
    chat_data = ChatData.get_or_default(message['peer_id'])

    try:
        chat_members = vk.messages.get_conversation_members(
            peer_id=message['peer_id'],
            fields='screen_name'
        )

        chat_data.user_infos = [
            UserInfo(user_id=profile['id'],
                     name=f'{profile["first_name"]} {profile["last_name"]}',
                     nickname=profile.get('screen_name', ''))
            for profile in chat_members['profiles']
        ]
    except ApiError:
        logging.warning(f'Not an admin in chat {message["peer_id"]} :(')

    chat_data.save()

    try:
        res = message_parser.parse(message['text'])
        if res is not None:
            action, args = res

            answer = action(message, chat_data, *args)
    except ValueError as e:
        answer = f'Error at parsing: {e}'
    except Exception as e:
        answer = str(e)

    if answer is None:
        return

    vk.messages.send(peer_id=message['peer_id'], message=answer)
