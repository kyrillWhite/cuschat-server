from stream_sources.strsource import strsource
import socket
import time
import httpx
import json
import re
from threading import Thread, Event

server = 'irc.chat.twitch.tv'
port = 6667
nickname = 'justinfan67420'
max_messages_count = 50

class twitchApi(strsource):
  def __init__(self):
    self.channel = None
    self.sock = None
    self.messages = None
    self.event = None
    self.thread = None
    self.token = None
    self.removeChannel = None
    super().__init__()
  
  def validate(self, channel):
    """
    Validate twitch channel.

    ```channel``` - twitch channel's name

    Return: channel is valide.
    """

    print(self.config['twitch'])
    client_id = self.config['twitch']['CLIENT_ID']
    client_secret = self.config['twitch']['CLIENT_SECRET']
    token_url = f'https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials'
    token_response = httpx.post(token_url, headers={
      'Content-Type': 'application/x-www-form-urlencoded'
    })

    if not token_response.is_success:
      return False

    access_token = json.loads(token_response.text)['access_token']

    channel_url = f'https://api.twitch.tv/helix/users?login={channel}'
    channel_response = httpx.get(channel_url, headers={
      'Authorization': f'Bearer {access_token}',
      'Client-Id': self.config['twitch']['CLIENT_ID']
    })
    is_valid = channel_response.is_success and json.loads(channel_response.text)['data']

    if is_valid:
      print(f'Channel \'{channel}\' is valid')
    else:
      print(f'Channel \'{channel}\' is invalid')

    return is_valid

  def connect(self, channel, token, removeChannel):
    """
    Initialize socket and class fields.

    ```channel``` - twitch channel's name,

    ```token``` - channel's token,

    ```removeChannel``` - function of removing channel
    """

    channel = '#' + channel
    self.channel = channel
    sock = socket.socket()
    sock.settimeout(10)
    sock.connect((server, port))
    sock.send(f'CAP REQ :twitch.tv/tags\r\n'.encode('utf-8'))
    sock.send(f"PASS oauth:SCHMOOPIIE\r\n".encode('utf-8'))
    sock.send(f"NICK {nickname}\r\n".encode('utf-8'))
    sock.send(f"JOIN {channel}\r\n".encode('utf-8'))
    self.sock = sock
    self.messages = []
    self.event = Event()
    self.thread = Thread(target=self.background_worker)
    self.thread.start()
    self.last_request_time = time.time()
    self.token = token
    self.removeChannel = removeChannel

  def getNewMessages(self, last_message_time):
    """
    Get new messages passed later then last message.

    ```last_message_time``` - time of last message,

    Return: list of messages.
    """

    self.last_request_time = time.time()
    return list(filter(lambda m: m['time'] > last_message_time, self.messages))

  def background_worker(self):
    """
    Start background worker.
    """
    
    print("Background worker created")
    while True:
      try:
        response = self.sock.recv(4096).decode('utf-8')

        if response.startswith('PING'):
          self.sock.send('PONG\r\n'.encode('utf-8'))
          print('PONG')
          continue

        if not response:
          continue

        messages = list(filter(None, response.split("\r\n")))

        for message_text in messages:
          match = re.search(
              '.*display-name=([^\;]*)(;emote-only=1)?;emotes=(.*);first-msg.*tmi-sent-ts=(.*)(?=;turbo).*tmi\.twitch\.tv PRIVMSG #.* :(.*)', message_text
          ).groups()
          author_name, _, emotes_text, sended_time, _message_text = match

          if len(self.messages) == max_messages_count:
            self.messages = self.messages[1:]

          emotes = []

          if emotes_text:
            emotes_text_array = emotes_text.split('/')

            for emote_text in emotes_text_array:
              emote_id, emote_positions = emote_text.split(':')

            emotes.append({ 'id': emote_id, 'positions': [{
              'from': emote_position.split('-')[0],
              'to': emote_position.split('-')[1]
              } for emote_position in emote_positions.split(',')] })

          message = {
            'text': _message_text,
            'author': author_name,
            'time': int(sended_time),
            'emotes': emotes,
          }
          self.messages.append(message)
      except:
        pass
      finally:
        if self.event.is_set():
          break
        
        if time.time() - self.last_request_time > 10:
          print(f'Listening channel \'{self.channel}\' is over')
          self.removeChannel(self.token)
          break

  def __del__(self):
    if self.event:  
      try:
        self.event.set()
        self.thread.join()
      except:
        pass
    if self.sock:
      self.sock.close()