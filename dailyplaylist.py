import os
from urllib.parse import urlparse, parse_qs
import re
import json

from flask import Flask, redirect, Response, request

app = Flask(__name__)

SLACK_WEBHOOK_TOKEN = os.environ.get('SLACK_WEBHOOK_TOKEN')

DATA_FILENAME = "video_ids.json"
OLDEST_FIRST = True


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


def get_current_video_ids():
    with open(DATA_FILENAME) as data_file:
        video_ids = json.load(data_file)
        return list(video_ids)


@app.route('/slack/webhook', methods=['POST'])
def handle_slack_webhook():
    if request.form.get('token') == SLACK_WEBHOOK_TOKEN:
        text = request.form.get('text', '')
        urls = get_urls_from_text(text)

        new_video_ids = []
        for url in urls:
            video_id = get_youtube_video_id(url)
            if video_id:
                new_video_ids.append(video_id)

        if new_video_ids:
            current_video_ids = get_current_video_ids()
            current_video_ids.extend(new_video_ids)
            with open(DATA_FILENAME, 'w') as data_file:
                json.dump(current_video_ids, data_file)

    return Response(), 200


@app.route('/', methods=['GET'])
def redirect_to_playlist():
    """
    Redirect to playlist which is based on YouTube urls
    which are aggregated from a specific Slack channel.

    [https://lifehacker.com/create-a-youtube-playlist-without-an-account-with-this-1688862486]
    """
    video_ids = get_current_video_ids()
    if OLDEST_FIRST:
        video_ids.reverse()

    playlist_url = 'https://www.youtube.com/watch_videos?video_ids={}'.format(','.join(video_ids))

    return redirect(playlist_url)


if __name__ == '__main__':
    app.run()
