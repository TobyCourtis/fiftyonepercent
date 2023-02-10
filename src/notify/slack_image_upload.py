import json
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.notify import notifier


# If you're using this in production, you can change this back to INFO and add extra log entries as needed.
# logging.basicConfig(level=logging.INFO)


def upload_image(file_path, title, comment, channel="crypto-trading"):
    try:
        with open(os.path.dirname(__file__) + "/../keys/slack-notifier-bot-oauth.json") as f:
            SLACK_BOT_TOKEN = json.loads(f.read())["SLACK_BOT_TOKEN"]

        client = WebClient(SLACK_BOT_TOKEN)

        new_file_res = client.files_upload(
            channels=channel,
            title=title,
            file=file_path,
            initial_comment=comment,
        )
    except SlackApiError as e:
        notifier.slack_notify(f"Current plot upload failed with exception: {e}")


def upload_current_plot(window_min, window_max, units):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    graph_snapshot_path = f"{current_dir}/../live/current_plot_snapshot.png"
    title = "Current Plot"
    comment = f"Latest plot using windows length {window_min} and {window_max} with units '{units}'"
    upload_image(file_path=graph_snapshot_path, title=title, comment=comment, channel="prod-data")


if __name__ == "__main__":
    upload_current_plot(1, 2, "days")
