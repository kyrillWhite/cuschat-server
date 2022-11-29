# CuSChat

CuSChat (***Cu***stom ***S***tream ***Chat***) - application allowing customize and render stream chat from the most famous streaming platforms: Twitch and YouTube.

User can create your own chat design or use one of presented presets.

# Server

Server is python flask api application.

```
# run server
python cuschat_api.py
```
## API

<code>GET  /api/youtube/validation?video={video_id}</code>

<code>GET  /api/twitch/validation?channel={channel_name}</code>

<code>GET  /api/twitch/connect?channel={channel_name}</code>

<code>GET  /api/youtube/chat?video={video_id}&last_message_time={last_message_time}</code>

<code>GET  /api/twitch/chat?channel={channel_name}&last_message_time={last_message_time}</code>

# Client

Clilent repository presented at [cuschat-client](https://github.com/kyrillWhite/cuschat-client).