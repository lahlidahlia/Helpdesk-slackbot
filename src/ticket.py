from rt_stat import RT_Stat
from rt import RT
from listener import Listener
import traceback
class Ticket:
    def __init__(self, client):
        self.client = client
        Listener.register(self.on_ready, "on_ready")
        Listener.register(self.on_message, "on_message")
        self.rt_stat = RT_Stat()
        self.ticket_url = "https://support.oit.pdx.edu/Ticket/Display.html?id="

    def send_message(self, *args):
        """ Shortener. """
        return self.client.rtm_send_message(*args)


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

            if ctx.command in ["!response"]:
                if len(ctx.args) == 1:
                    try:
                        days_ago = int(ctx.args[0])
                        if days_ago < 0:
                            self.send_message(ctx.channel, "Positive numbers please!")
                            return
                    except ValueError:
                        traceback.print_exc()
                        self.client.rtm_send_message(ctx.channel, "Invalid value. Please enter amount of days.")
                        return
                    avg_time, slowest, fastest, no_response = self.rt_stat.get_average_response_time(days_ago)
                    avg_time = self.hms(int(avg_time))
                    response = "Response time in the last " + str(days_ago) + " days:\n" + \
                               "Average time: {}h, {}m, {}s.".format(*avg_time) + \
                               "\nSlowest time: {}h, {}m, {}s, ticket #{}\n".format(*self.hms(slowest[1]), slowest[0]) + \
                               "Fastest time: {}h, {}m, {}s, ticket #{}\n".format(*self.hms(fastest[1]), fastest[0]) + \
                               "No response: {} out of {}.\n".format(*no_response)
                    self.send_message(ctx.channel, response)
                
        except:
            self.client.rtm_send_message(ctx.channel, "An error has occured in the bot... :thinking_face:")
            traceback.print_exc()


    def hms(self, seconds):
        """
        Convert seconds to H:M:S in a tuple.
        """
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return (h, m, s)
