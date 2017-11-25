import re
from pprint import pprint
import yaml
import requests
import traceback
from listener import Listener

class Ticket:
    def __init__(self, client):
        self.client = client
        self.base_url = "https://support.oit.pdx.edu/NoAuthCAS/REST/1.0/"
        self.cookies = None  # Not logged in if None.

        try:
            f = open("../tokens/rt")
            self.username, self.password = tuple(f.read().strip().split(":"))
            f.close()
        except Exception as e:
            traceback.print_exc()
            print("Something went wrong while reading in username/password.")
            print("Make sure you have a file /tokens/rt with only username:password")
            f.close()
            exit()

        Listener.register(self.on_message, "on_message")
        self.login()


    def on_message(self, ctx):
        try:  # Don't exit the bot when an error happens.
            if ctx.command in ["!ticket"]:
                if len(ctx.args) == 1:
                    try:
                        self.get_ticket(ctx.args[0])
                    except TypeError as e:
                        if len(e.args) and e.args[0] == "Numeric only":
                            self.client.rtm_send_message(ctx.channel, "Please enter ticket numbers only!")
                        else:
                            traceback.print_exc()
                    except LookupError as e:
                        if len(e.args) and e.args[0] == "Ticket doesn't exist":
                            self.client.rtm_send_message(ctx.channel, "That ticket doesn't exist!")
                        else:
                            traceback.print_exc()
        except:
            self.client.rtm_send_message(ctx.channel, "An error has occured in the bot...")
            traceback.print_exc()



    def login(self):
        payload = {"user": self.username, "pass": self.password}
        r = requests.post(self.base_url, data=payload)
        if r.status_code == 200:
            print("Logged in successfully as " + self.username + "!")
            self.cookies = r.cookies
        elif r.status_code == 302:
            # 302 means you got redirected to SSO.
            print("Your username or password is incorrect!")
            exit()


    def get_ticket(self, ticket_number):
        """
        ticket_number (int)
        """
        ticket_url = self.base_url + "ticket/" + str(ticket_number) + "/history?format=l"
        text = self.get_url(ticket_url)
        self.validate_ticket(text)
        self.parse_ticket(text)


    def validate_ticket(self, text):
        to_validate = text.splitlines()[2]
        if (re.match("# Objects of type ticket must be specified by numeric id\.", to_validate) or
            re.match("# Invalid object specification\:", to_validate)):
            raise TypeError("Numeric only")
        if re.match("# Ticket [0-9]+ does not exist\.", to_validate):
            raise LookupError("Ticket doesn't exist")
        return True

    def parse_ticket(self, text):
        # Parsing might require some optimizations. We're dealing with pretty large number of lines.
        # Trim the first two lines (get rid of HTTP code)
        trimmed_text = text[text.find('\n', text.find('\n')+1)+1:]
        history_list = trimmed_text.split("--\n\n#")  # Split the ticket into histories.

        for i in range(len(history_list)):
            # Trim the first 2 lines (get rid of "#37/37 (id/.....")
            history = history_list[i]
            history = history[history.find('\n')+1:]
            history = history.replace("Content:", "Content: |\n")
            history = yaml.load(history)
            history_list[i] = history

        pprint(history_list)


    def get_url(self, url):
        """
        Perform a requests get on the URL. Returns the content.
        This ensures that if the session disconnected, we will reconnect.
        """
        if not self.cookies:
            self.login()

        r = requests.get(url, cookies=self.cookies)

        if r.status_code == 302:
            # Try logging in again and do the same thing.
            self.cookies = None
            self.get_url(url)
        elif r.status_code == 200:
            return r.text
