from pprint import pprint
import yaml
import requests
import traceback
from listener import Listener

class Ticket:
    def __init__(self):
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
        if ctx.command in ["!ticket"]:
            if len(ctx.args) == 1:
                pass
                self.get_ticket(ctx.args[0])

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
        self.parse_ticket(text)
        

    def parse_ticket(self, text):
        # Parsing might require some optimizations. We're dealing with pretty large number of lines.
        trimmed_text = text[text.find('\n')+1:]  # Trim the first line (get rid of HTTP code)
        history_list = trimmed_text.split("--\n\n#")  # Split the ticket into histories.

        for history in history_list:
            # Trim the first 2 lines (get rid of "#37/37 (id/.....")
            history = history[history.find('\n')+1:]
            history = history.replace("Content:", "Content: |\n")


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
