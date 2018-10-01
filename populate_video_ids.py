import os
import json

from slackclient import SlackClient

from dailyplaylist import get_urls_from_text, get_youtube_video_id, DATA_FILENAME


SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
NUMBER_OF_MESSAGES = 1000


if __name__ == '__main__':
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

        video_ids.reverse()

        with open(DATA_FILENAME, 'w') as data_file:
            json.dump(video_ids, data_file)

    else:
        print(response['error'])
