import json
import requests
import os

auth_url = ""


def google_mini_notify(text):
    requests.get("http://192.168.86.39:5000/say", params={"text": text})


def slack_notify(text):
    global auth_url
    if not auth_url:
        with open(os.path.dirname(__file__) + "/../keys/slack-webhook.json") as f:
            auth_url = json.loads(f.read())["auth_url"]
    slack_payload = {"channel": "#kingslanding",
                     "username": "dumbot",
                     "text": "<!here> {}".format(text),
                     "icon_emoji": ":slack:"}
    requests.post(f"https://hooks.slack.com/services/{auth_url}",
                  data=json.dumps(slack_payload))

# google_mini_notify("stonks are through the roof right now!")
# slack_notify("test")
