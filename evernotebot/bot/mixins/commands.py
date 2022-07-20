from evernotebot.bot.errors import EvernoteBotException
from evernotebot.bot.mixins import EvernoteMixin
from evernotebot.bot.mixins.chat import ChatMixin


class StartCommandMixin(EvernoteMixin):
    def on_command(self, name: str):
        if name != 'start':
            return
        text = '''Welcome! It's bot for saving your notes to Evernote on fly.
    Please tap on button below to link your Evernote account with bot.'''
        oauth_data = self.get_evernote_oauth_data(text)
        self.user['evernote'] = {'oauth': oauth_data}
        self.save_user()


class SwitchModeCommand(EvernoteMixin):
    def on_command(self, name: str):
        if name != 'switch_mode':
            return
        buttons = []
        for mode in ('one_note', 'multiple_notes'):
            title = mode.capitalize().replace('_', ' ')
            if self.user['bot_mode'] == mode:
                title = f'> {title} <'
            buttons.append({'text': title})
        keyboard = {
            'keyboard': [[b] for b in buttons],
            'resize_keyboard': True,
            'one_time_keyboard': True,
        }
        self.send_message('Please, select mode', keyboard=keyboard)
        self.user['state'] = 'switch_mode'
        self.save_user()

    def on_user_state(self, state: str, message: dict):
        if state != 'switch_mode':
            return
        mode = message['text']
        if mode.startswith('> ') and mode.endswith(' <'):
            mode = mode[2:-2]
        title = mode
        mode = mode.lower().replace(' ', '_')
        if self.user['bot_mode'] == mode:
            self.send_message(f'The bot already in `{title}` mode.')
            return
        if mode == 'one_note':
            self.switch_mode_one_note()
            return
        if mode == 'multiple_notes':
            del self.user['evernote']['shared_note_id']
            self.user['bot_mode'] = mode
            self.save_user()
            self.send_message(f'The bot has switched to `{title}` mode.')
            return
        raise EvernoteBotException(f'Unknown mode `{title}`')

    def switch_mode_one_note(self):
        settings = self.user['evernote']
        if settings['access'] != 'readwrite':
            self.send_message('To enable `One note` mode you have to allow to the bot both reading and updating your notes')
            text = 'Please, sign in and give the permissions to the bot.'
            oauth_data = self.get_evernote_oauth_data(text, access='readwrite')
            self.user['evernote']['oauth'] = oauth_data
            self.save_user()
            return
        nb_id = settings['notebook']['guid']
        note_id, note_url = self.create_shared_note(nb_id, title='Telegram bot notes')
        settings['shared_note_id'] = note_id
        text = f'Your notes will be saved to <a href="{note_url}">this note</a>'
        self.send_message(text, parse_mode='Html')
        self.user['bot_mode'] = 'one_note'
        self.save_user()


class SwitchNotebookCommand(EvernoteMixin):
    def on_command(self, name: str):
        if name != 'switch_notebook':
            return
        all_notebooks = self.evernote_get_notebooks()
        buttons = []
        current_nb_name = self.user['evernote']['notebook']['name']
        for nb in all_notebooks:
            name = nb['name']
            if name == current_nb_name:
                name = f'> {name} <'
            buttons.append({'text': name})
        keyboard = {
            'keyboard': [[b] for b in buttons],
            'resize_keyboard': True,
            'one_time_keyboard': True,
        }
        self.send_message('Please, select notebook', keyboard=keyboard)
        self.user['state'] = 'switch_notebook'
        self.save_user()

    def on_user_state(self, state: str, message: dict):
        user = self.user
        if state != 'switch_notebook':
            return
        name = message['text']
        if name.startswith('> ') and name.endswith(' <'):
            name = name[2:-2]
        notebooks = self.evernote_get_notebooks({'name': name})
        if not notebooks:
            raise EvernoteBotException(f'Notebook `{name}` not found')
        # TODO: self.create_note(notebook) if bot_user.bot_mode == 'one_note'
        notebook = notebooks[0]
        user['evernote']['notebook']['name'] = notebook['name']
        user['evernote']['notebook']['guid'] = notebook['guid']
        self.send_message(f'Current notebook: {notebook["name"]}')
        self.save_user()


class HelpCommandMixin(ChatMixin):
    def on_command(self, name: str):
        if name != 'help':
            return
        self.send_message('''This is bot for Evernote (https://evernote.com).

Just send message to bot and it will create note in your Evernote notebook. 

You can send to bot:

* text
* photo (size < 12 Mb, telegram restriction)
* file (size < 12 Mb, telegram restriction)
* voice message (size < 12 Mb, telegram restriction)
* location

There are modes:

1) "One note" mode.
On this mode there is one note will be created in Evernote notebook. All messages you will send, be saved in this note.

2) "Multiple notes" mode (default).
On this mode for every message you sent, there will separate note be created in Evernote notebook.

You can switch bot mode with command /switch_mode
Note, every time you select "One note" mode, new note will create and set as current note for this bot.

Also, you can switch your current notebook with command /notebook
Note, if your bot is in "One note" mode and you are switching notebook, new note will create in newly selected notebook.

Contacts: djudman@gmail.com
''')
