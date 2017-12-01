from rt import RT
from listener import Listener
import traceback
class Ticket:
    def __init__(self, client):
        self.client = client
        Listener.register(self.on_ready, "on_ready")
        Listener.register(self.on_message, "on_message")
        self.rt = RT()
        self.ticket_url = "https://support.oit.pdx.edu/Ticket/Display.html?id="


    def on_ready(self):
        pass


    def on_message(self, ctx):
        try:  # Don't exit the bot when an error happens.
            if ctx.command in ["!ticket"]:
                if len(ctx.args) == 1:
                    ticket = None
                    try:
                        ticket = self.rt.get_ticket(ctx.args[0])
                        self.client.rtm_send_message(ctx.channel, self.ticket_url + ctx.args[0] + "\n" +
                                                                  "Subject: " + ticket["Subject"])
                    except TypeError as e:
                        if len(e.args) and e.args[0] == "Numeric only":
                            self.client.rtm_send_message(ctx.channel, "Please enter ticket numbers only!")
                        else:
                            raise TypeError
                    except LookupError as e:
                        if len(e.args) and e.args[0] == "Ticket doesn't exist":
                            self.client.rtm_send_message(ctx.channel, "That ticket doesn't exist!")
                        else:
                            raise LookupError
        except:
            self.client.rtm_send_message(ctx.channel, "An error has occured in the bot... :thinking_face:")
            traceback.print_exc()
