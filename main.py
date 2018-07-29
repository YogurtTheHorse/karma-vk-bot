import argparse
import json
from typing import Dict

import logging

import mongoengine
from flask import Flask, request, abort

import handlers

logger = logging.getLogger()


def create_app(config: Dict = None) -> Flask:
    # noinspection PyShadowingNames
    app = Flask(__name__)
    app.config.update(config or {})

    @app.route('/webhook', methods=['POST'])
    def handle_webhook_post():
        vk_json = request.get_json(force=True)
        if vk_json.get('secret') != app.config['vk_secret']:
            logger.warning(f'Got update from vk with no/wrong secret: {request.get_data()}')
            abort(403)
            return

        if vk_json['type'] == 'confirmation':
            if vk_json['group_id'] == app.config['vk_group']:
                logger.info(f'Accepting confirmation {request.data} with {app.config["confirmation_code"]}')
                return app.config["confirmation_code"]
            else:
                logger.warning('Refusing confirmation {}'.format(request.data))
                abort(400)
                return
        elif vk_json['type'] == 'message_new':
            logger.info('Got message from vk: {}'.format(json.dumps(vk_json['object'])))
            handlers.handle_vk_message(vk_json['object'])
            return 'ok'

        logger.info('Got unknown request from vk: {}'.format(request.data))
        abort(400)

    return app


if __name__ == '__main__':
    args_parser = argparse.ArgumentParser(description='Karma bot for vk')
    args_parser.add_argument('--vk_secret', '-s',
                             type=str,
                             dest='vk_secret',
                             required=True,
                             help='VK secret')
    args_parser.add_argument('--vk_group', '-g',
                             type=int,
                             dest='vk_group',
                             required=True,
                             help='VK group id')
    args_parser.add_argument('--vk_confirmation_code', '-c',
                             type=str,
                             dest='confirmation_code',
                             required=True,
                             help='VK confirmation code')
    args_parser.add_argument('--port', '-p',
                             type=int,
                             dest='port',
                             default=7000,
                             help='Flask port')

    args = args_parser.parse_args()
    #  Converts to dict all public members
    app = create_app({k: v for k, v in args.__dict__.items() if not k.startswith('_')})

    mongoengine.connect()
    app.run(host='0.0.0.0', port=args.port)
