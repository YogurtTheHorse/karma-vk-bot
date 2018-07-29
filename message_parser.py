from typing import Callable


class CommandDescription:
    def __init__(self, command_name: str, action, help_message: str, args_description: str=None):
        self.name = command_name
        self.action = action
        self.help_message = help_message
        self.args_description = args_description


class MessageParser(object):
    def __init__(self, command_symbol: str='/'):
        self.command_symbol = command_symbol

        self.commands = {}

        self.add_command('help', action=self.list_commands, help_message='Lists all commands')

    def list_commands(self, *args):
        infos = []

        for command in self.commands.values():
            info = '{0}{1} - {2}'.format(self.command_symbol, command.name, command.help_message)
            if command.args_description is not None and len(command.args_description) > 0:
                info += '\n  Args: ' + command.args_description

            infos.append(info)

        return '\n\n'.join(infos)

    def add_command(self, command_name: str, action: Callable, help_message: str= '', args_description: str=None):
        if command_name in self.commands:
            raise ValueError('duplicate command {0}'.format(command_name))
        elif ' ' in command_name:
            raise ValueError('spaces in command name not allowed')

        self.commands[command_name] = CommandDescription(command_name, action, help_message, args_description)

    def parse(self, message: str):
        message = message.strip(' ')

        if not message.startswith(self.command_symbol):
            return None

        try:
            command_name = message[len(self.command_symbol):].split(' ')[0]
        except IndexError:
            raise ValueError('Can\'t parse command name')

        if command_name not in self.commands:
            raise ValueError('No such command: {0}'.format(command_name))

        command_description = self.commands[command_name]
        command_args = message.split(' ')[1:]

        return command_description.action, command_args
