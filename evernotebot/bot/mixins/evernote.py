import logging
from typing import Tuple

from evernotebot.bot.errors import EvernoteBotException
from evernotebot.bot.mixins.chat import ChatMixin
from evernotebot.util.evernote.client import EvernoteApi

from requests_oauthlib.oauth1_session import TokenRequestDenied


class EvernoteMixin(ChatMixin):
    def __init__(self, config: dict):
        super(EvernoteMixin, self).__init__(config)
        self._evernote_api: EvernoteApi = EvernoteApi(sandbox=config['debug'])

    async def on_message(self, message: dict):
        await super(EvernoteMixin, self).on_message(message)
        token = self.user.evernote_access_token
        if not token:
            raise EvernoteBotException('You have to sign in to Evernote first. Send /start and link account')
        if self._evernote_api.token != token:
            self._evernote_api = EvernoteApi(token, sandbox=self.config['debug'])

    @property
    def evernote_api(self):
        token = self.user.evernote_access_token
        if token and self._evernote_api.token != token:
            self._evernote_api = EvernoteApi(token, sandbox=self.config['debug'])
        return self._evernote_api

    async def get_evernote_oauth_data(self, message_text: str, access: str = 'readonly') -> dict:
        auth_button = {'text': 'Waiting for Evernote...', 'url': self.url}
        status_message = await self.send_message(message_text, buttons=[auth_button])
        app_config = self.config['evernote']['access'][access]
        try:
            oauth_data = self.evernote_api.get_oauth_data(
                self.user.id,
                app_config['key'],
                app_config['secret'],
                self.config['oauth_callback_url'],
                access,
                sandbox=self.config['debug'])
            auth_button = {'text': 'Sign in with Evernote', 'url': oauth_data['oauth_url']}
            await self.edit_message(status_message['message_id'], buttons=[auth_button])
            return oauth_data
        except Exception as e:
            auth_button = {'text': 'Evernote request failed', 'url': self.url}
            await self.edit_message(status_message['message_id'], buttons=[auth_button])
            await self.send_message('It seems Evernote API does not work properly. Please, try again later')
            raise e

    async def evernote_auth(self, callback_key: str, access: str, oauth_verifier: str):
        if not oauth_verifier:
            raise EvernoteBotException('We are sorry, but you have declined authorization.')
        user = self.find_user({'evernote.oauth.callback_key': callback_key})
        oauth = user['evernote']['oauth']
        app_config = self.config['evernote']['access'][access]
        try:
            access_token = await self.evernote_api.get_access_token(
                app_config['key'],
                app_config['secret'],
                oauth['token'],
                oauth['secret'],
                oauth_verifier,
                sandbox=self.config['debug']
            )
            self.user['evernote']['access_token'] = access_token
            self._evernote_api = EvernoteApi(access_token, sandbox=self.config['debug'])
        except TokenRequestDenied as e:
            logging.getLogger('evernotebot').fatal(e, exc_info=True)
            raise EvernoteBotException('Evernote access token request failed. Try again later.')
        except Exception as e:
            logging.getLogger('evernotebot').fatal(e, exc_info=True)
            raise EvernoteBotException('Getting evernote access token failed. Try again later.')
        try:
            await self.user_setup_by_access(self.user, access)
            await self.save_user()
        except Exception as e:
            logging.getLogger('evernotebot').fatal(e, exc_info=True)
            raise EvernoteBotException('User initial setup failed. Try again later.')

    async def user_setup_by_access(self, user: dict, access_type: str) -> None:
        user['evernote']['access'] = access_type
        del user['evernote']['oauth']
        if access_type == 'readonly':
            await self.send_message('Evernote account is connected.\nFrom now you can just send a message and a note will be created.')
            default_notebook = await self.evernote_api.get_default_notebook()
            nb_name = default_notebook['name']
            user['evernote']['notebook'] = {
                'name': nb_name,
                'guid': default_notebook['guid'],
            }
            mode = user['bot_mode'].replace('_', ' ').capitalize()
            await self.send_message(f'Current notebook: {nb_name}\nCurrent mode: {mode}')

    async def evernote_check_quota(self, file_size: int):
        quota = await self.evernote_api.get_quota_info()
        if quota['remaining'] < file_size:
            reset_date = quota['reset_date'].strftime('%Y-%m-%d %H:%M:%S')
            remain_bytes = quota['remaining']
            raise EvernoteBotException(f'Your evernote quota is out ({remain_bytes} bytes remains till {reset_date})')

    async def evernote_get_notebooks(self, query: dict = None) -> Tuple[dict]:
        nbs = await self.evernote_api.get_all_notebooks(query)
        return tuple((nb for nb in nbs))

    async def create_shared_note(self, notebook_guid: str, title):
        note_id = await self.evernote_api.create_note(notebook_guid, title=title)
        note_url = self.evernote_api.get_note_link(note_id)
        return note_id, note_url

    async def save_note(self, text: str = None, title: str = None, **kwargs):
        user = self.user
        if user['bot_mode'] == 'one_note':
            note_id = user['evernote']['shared_note_id']
            await self.evernote_api.update_note(note_id, text, title, **kwargs)
        else:
            notebook_id = user['evernote']['notebook']['guid']
            await self.evernote_api.create_note(notebook_id, text, title, **kwargs)
