import logging
from typing import Dict

from vk_api import VkApi

from database_models import ChatData
from message_parser import MessageParser

logger = logging.getLogger('handlers')

message_parser = MessageParser(command_symbol='/')

vk = None


def set_token(token: str):
    global vk
    vk_session = VkApi(token=token)
    vk = vk_session.get_api()


def show_stats(message: Dict, chat_data: ChatData):
    return 's'


def give_karma(message: Dict, chat_data: ChatData):
    return 'g'


def remove_karma(message: Dict, chat_data: ChatData):
    return 'r'


message_parser.add_command(
    'stats',
    action=show_stats,
    help_message='Shows karma stats'
)
message_parser.add_command(
    'karma',
    action=give_karma,
    help_message='Adds karma'
)
message_parser.add_command(
    'dekarm',
    action=remove_karma,
    help_message='Decreases karma'
)


def handle_vk_message(message: Dict):
    logger.debug(f'Got message {message}.')

    answer = None
    try:
        res = message_parser.parse(message['text'])
        if res is not None:
            action, args = res

            answer = action(message, None, *args)
    except ValueError as e:
        answer = f'Error at parsing: {e}'
    except Exception as e:
        answer = str(e)

    if answer is None:
        return

    vk.messages.send(peer_id=message['peer_id'], message=answer)
