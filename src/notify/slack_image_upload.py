import json
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.notify import notifier


# If you're using this in production, you can change this back to INFO and add extra log entries as needed.
# logging.basicConfig(level=logging.INFO)


def upload_plot():
    try:
        with open(os.path.dirname(__file__) + "/../keys/slack-notifier-bot-oauth.json") as f:
            SLACK_BOT_TOKEN = json.loads(f.read())["SLACK_BOT_TOKEN"]

        client = WebClient(SLACK_BOT_TOKEN)

        current_dir = os.path.dirname(os.path.realpath(__file__))
        file_dir = f"{current_dir}/../clients/current_plot_snapshot.png"

        new_file_res = client.files_upload(
            channels="crypto-trading",
            title="Current Plot",
            file=file_dir,
            initial_comment="Latest plot using {windowMin}, {windowMax}, units='days'",
        )
    except SlackApiError as e:
        notifier.slack_notify(f"Current plot upload failed with exception: {e}")
