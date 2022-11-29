from stream_sources.strsource import strsource
import traceback
import httpx
import json
from bs4 import BeautifulSoup

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36 Edg/86.0.622.63,gzip(gfe)',
}
url = 'https://www.youtube.com/live_chat'

class youtubeApi(strsource):
  def validate(self, videoId):
    try:
      _url = url + f'?v={videoId}'
      response = httpx.get(_url, headers=headers)
      soup = BeautifulSoup(response.text, 'html.parser')
      return not(soup.body and soup.body.div and soup.body.div.h1 and soup.body.div.h1.string == 'Something went wrong')
    except:
      return False

  def connect(self, videoId):
    """
    Initialize class fields.

    ```videoId``` - youtube stream's id,
    """

    self.last_message = {'time': 0, 'id': ''}
    self.url = url + f'?v={videoId}'

  def getNewMessages(self, last_message_time):
    """
    Get new messages passed later then last message.

    ```last_message_time``` - time of last message,

    Return: list of messages.
    """

    response = httpx.get(self.url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    str_response = soup.body.find_all('script')[-1].get_text()[26:-1]
    json_response = json.loads(str_response)

    messages = []
    try:
      message_actions = filter(lambda a: 'addChatItemAction' in a,
                              json_response['contents']['liveChatRenderer']['actions'])
      for message_action in message_actions:
        try:
          if 'liveChatTextMessageRenderer' not in message_action['addChatItemAction']['item']:
            continue

          message_renderer = message_action['addChatItemAction']['item']['liveChatTextMessageRenderer']
          message_text = ''.join(map(lambda m: m['text'] if 'text' in m else m['emoji']['emojiId'],
                                    message_renderer['message']['runs']))
          author_name = message_renderer['authorName']['simpleText']
          sended_time = int(message_renderer['timestampUsec']) // 1000

          if sended_time <= last_message_time:
            continue
          
          message = {
            'text': message_text,
            'author': author_name,
            'time': sended_time
          }
          messages.append(message)
        except:
          print('Message data error')
          traceback.print_exc()
    except:
      print('No messages')
    return list(filter(lambda m: m['time'] > last_message_time, messages))