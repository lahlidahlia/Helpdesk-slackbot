from listener import Listener
from kudos import Kudos
from ticket import Ticket
from slackclient import SlackClient
import time
from pprint import pprint


class Context:
    """ Pass in an event to parse it into useful variables. """
    def __init__(self):
        self.message = None
        self.command = None
        self.args = None
        self.arg_text = None
        self.channel = None

    def message_event(self, event):
        self.message = event["text"]
        self.command = self.message.split(" ")[0]
        self.args = self.message.split(" ")[1:]  # List of aguments.
        self.arg_text = " ".join(self.args)  # Entire string after command.
        self.channel = event["channel"]

def parse_events(events):
    print(events)
    for event in events:
        ctx = Context()
        if "type" in event and event["type"] == "message":
            ctx.message_event(event)
            Listener.update("on_message", ctx)
            if ctx.command in ["!test", "!t"]:
                sc.rtm_send_message(channel, "Helpdesk assemble!")


if __name__ == "__main__":
    f = open("../tokens/slack")
    slack_token = f.read().strip()
    f.close()
    sc = SlackClient(slack_token)
    kudos = Kudos()
    ticket = Ticket()

    if sc.rtm_connect():
        while True:
            parse_events(sc.rtm_read())
            time.sleep(0.3)
    else:
        print("Connection failed")
