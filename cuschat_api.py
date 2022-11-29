import re
from stream_sources import youtube, twitch
from flask import Flask, request, make_response, redirect
from flask_restful import Api, Resource, reqparse, abort, url_for
from flask_cors import CORS
import json
import secrets

app = Flask(__name__)
api = Api()
host = '192.168.88.90'
CORS(app, origins=[f'http://{host}:8080'])

twitchChannels = {}
def removeChannel(channel):
  del twitchChannels[channel]

@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data, ensure_ascii=False), code)
    resp.headers.extend(headers or {})
    return resp

@api.resource('/api/youtube/validation')
class YouTubeValidation(Resource):
  def get(self):
    args = request.args
    if 'video' not in args:
      abort(400)
    video_id = args['video']
    ytApi = youtube.youtubeApi()
    if not ytApi.validate(video_id):
      abort(422)
    return output_json({
        'messages': 'validation successful'
    }, 200)

@api.resource('/api/twitch/validation')
class TwitchValidation(Resource):
  def get(self):
    args = request.args
    if 'channel' not in args:
      abort(400)
    channel_name = args['channel']
    if channel_name not in twitchChannels or not twitchChannels[channel_name].thread.is_alive():
      twApi = twitch.twitchApi()
      if not twApi.validate(channel_name):
        abort(422)
    return output_json({
        'messages': 'validation successful'
    }, 200)

@api.resource('/api/twitch/connect')
class TwitchConnect(Resource):
  def get(self):
    args = request.args
    if 'channel' not in args:
      abort(400)
    channel_name = args['channel']
    twApi = twitch.twitchApi()
    if not twApi.validate(channel_name):
      abort(422)
    token = secrets.token_hex(16)
    twApi.connect(channel_name, token, removeChannel)
    twitchChannels[token] = twApi
    return output_json({
        'token': token
    }, 200)

@api.resource('/api/youtube/chat')
class YouTubeChat(Resource):
  def get(self):
    args = request.args
    if 'video' not in args or 'last_message_time' not in args:
      abort(400)
    video_id = args['video']
    last_message_time = int(args['last_message_time'])
    ytApi = youtube.youtubeApi()
    if not ytApi.validate(video_id):
      abort(422)
    ytApi.connect(video_id)
    return output_json({
        'messages': ytApi.getNewMessages(int(last_message_time))
    }, 200)

@api.resource('/api/twitch/chat')
class TwitchChat(Resource):
  def get(self):
    args = request.args
    if 'channel' not in args or 'token' not in args or 'last_message_time' not in args:
      abort(400)
    channel_name = args['channel']
    token = args['token']
    last_message_time = int(args['last_message_time'])
    if token not in twitchChannels or not twitchChannels[token].thread.is_alive():
      return redirect(url_for('twitchconnect') + f'?channel={channel_name}')
    return output_json({
        'messages': twitchChannels[token].getNewMessages(int(last_message_time))
    }, 200)


api.init_app(app)

if __name__ == '__main__':
  app.run(debug=True, host=host)