import os
from urllib.parse import urlparse, parse_qs
import re

from flask import Flask, redirect

from slackclient import SlackClient

app = Flask(__name__)

SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
NUMBER_OF_MESSAGES = 1000


def get_urls_from_text(text):
    return re.findall('(?P<url>https?://[^\s>]+)', text)


def get_youtube_video_id(url):
    """
    Examples:
    - http://youtu.be/SA2iWivDJiE
    - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    - http://www.youtube.com/embed/SA2iWivDJiE
    - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    """
    query = urlparse(url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            p = parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    # fail?
    return None


@app.route('/')
def redirect_to_playlist():
    """
    Redirect to playlist which is based on YouTube urls
    which are aggregated from all messages in specific Slack channel.
    """
    sc = SlackClient(SLACK_TOKEN)

    response = sc.api_call(
      method="channels.history",
      channel=CHANNEL_ID,
      count=NUMBER_OF_MESSAGES
    )

    if response.get('ok'):
        messages = response.get('messages', [])

        urls = []
        video_ids = []

        for message in messages:
            text = message.get('text', '')
            urls_from_text = get_urls_from_text(text)
            urls.extend(urls_from_text)

        for url in urls:
            video_id = get_youtube_video_id(url)
            if video_id:
                video_ids.append(video_id)

        playlist_url = 'https://www.youtube.com/watch_videos?video_ids={}'.format(','.join(video_ids))
        return redirect(playlist_url)

    return response['error']

if __name__ == '__main__':
    app.run()
