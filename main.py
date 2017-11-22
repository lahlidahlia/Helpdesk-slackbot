from slackclient import SlackClient
import time
from pprint import pprint

f = open("tokens/slack")
slack_token = f.read().strip()
f.close()
sc = SlackClient(slack_token)

#pprint(sc.api_call("channels.list"))

if sc.rtm_connect():
    while True:
        events = sc.rtm_read()
        print(events)
        for event in events:
            if "type" in event and event["type"] == "message":
                if event["text"] == "!test":
                    channel = event["channel"]
                    sc.rtm_send_message(channel, "Helpdesk assemble!")
        
        time.sleep(1)
else:
    print("Connection failed")
