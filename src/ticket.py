import string
from rt import *
from listener import Listener
import traceback
import pytz
from datetime import datetime


class Ticket:
    def __init__(self, client):
        self.client = client
        Listener.register(self.on_ready, "on_ready")
        Listener.register(self.on_message, "on_message")
        Listener.register(self.on_loop, "on_loop")
        self.rt_stat = RT_Stat()
        self.ticket_url = "https://support.oit.pdx.edu/Ticket/Display.html?id="
        self.update_thread = None
        self.current_day = 0  # To detect day change
        self.updated_today = 0  # To check if the bot have updated today.

    def send_message(self, *args):
        """ Shortener. """
        return self.client.rtm_send_message(*args)


    def on_ready(self):
        pass

    def on_loop(self):
        if not self.updated_today:
            self.updated_today = 1
            self.update_thread = RT.update_cache()
            
        current_time = datetime.now(pytz.timezone('US/Pacific') )
        if current_time.weekday() != self.current_day:
            self.current_day = current_time.weekday()

        if self.update_thread and not self.update_thread.is_alive():
            self.update_thread = None
            if hasattr(self.update_thread, 'channel'):
                # If a channel is bundled, then send a message to the channel.
                error_count = self.update_thread.result.get()
                response = "Done updating\n"
                if error_count:
                    response += "There were {} errors found. Check the error log to see what they were.".format(error_count)
                self.send_message(self.update_thread.channel, response)
            print("Done updating!")

        

    def on_message(self, ctx):
        try:  # Don't exit the bot when an error happens.
            if ctx.command and ctx.command[0] != '!':
            # Ticket linker.
                try:
                    ticket_list = self.parse_message_for_tickets(ctx.message)
                    response = ""
                    for ticket_number in ticket_list:
                        ticket = RT.get_ticket(ticket_number)
                        response += self.ticket_url + str(ticket_number) + "\n" + \
                                    "Subject: " + ticket.content['Subject'] + "\n"
                    self.send_message(ctx.channel, response)
                except:
                    traceback.print_exc()

            if ctx.command in ["!response"]:
                if len(ctx.args) == 1:
                    try:
                        days_ago = int(ctx.args[0])
                    except ValueError:
                        traceback.print_exc()
                        self.client.rtm_send_message(channel_id, "Invalid value. Please enter amount of days.")
                    self.response_command(ctx.channel, days_ago)



            if ctx.command in ["!update"]:
                pre_response = "Updating {} tickets since {}".format(RT.get_amount_to_update(), RT.get_last_updated())
                self.send_message(ctx.channel, pre_response)
                self.update_thread = RT.update_cache()
                self.update_thread.channel = ctx.channel

            if ctx.command in ["!last_updated"]:
                response = "There are {} tickets to update since {}".format(RT.get_amount_to_update(), RT.get_last_updated())
                self.send_message(ctx.channel, response)


            if ctx.command in ["!untagged"]:
                untagged = self.rt_stat.untag_blame()
                if not untagged:
                    response = ":smile: Woo! All the tickets are tagged! :smile:"
                    self.send_message(ctx.channel, response)
                    return
                response = ":angry: Hey! You guys didn't tag your tickets!!! :angry:\n"
                for person in untagged.keys():
                    response += "{}: {}.\n".format(person, ", ".join(map(str, untagged[person])))
                #response = response[:-2] + ".\n"  # Replace the last comma with a period.
                response += "(This is only for fun, it's not designed to place blame on anyone!)"
                self.send_message(ctx.channel, response)


            if ctx.command in ['!touch', '!touches', '!tt']:
                if len(ctx.args) >= 1:
                    username = ctx.args[0]
                    try:
                        days_ago = int(ctx.args[1])
                    except ValueError:
                        traceback.print_exc()
                        self.client.rtm_send_message(channel_id, "Invalid value. Please enter amount of days.")
                    self.ticket_touch_command(ctx.channel, days_ago, username)
                    
                
                
        except:
            traceback.print_exc()
            self.send_message(ctx.channel, "An error has occured in the bot... :thinking_face:")


    def response_command(self, channel_id, days_ago):
        self.validate_days_ago(channel_id, days_ago)
        response = self.rt_stat.get_average_response_time(days_ago)
        if response == None:
            self.send_message(channel_id, "No tickets found for the last {} days. Do !update to update cache.".format(days_ago))
            return
        avg_time, slowest, fastest, no_response, no_response_list = response
        avg_time = self.hms(int(avg_time))
        response = "Response time in the last " + str(days_ago) + " days:\n" + \
                   "Average time: {:.0f}h, {:.0f}m, {:.0f}s.".format(*avg_time) + \
                   "\nSlowest time: {:.0f}h, {:.0f}m, {:.0f}s, ticket #{}\n".format(*self.hms(slowest[1]), slowest[0]) + \
                   "Fastest time: {:.0f}h, {:.0f}m, {:.0f}s, ticket #{}\n".format(*self.hms(fastest[1]), fastest[0]) + \
                   "No response: {} out of {}.\n".format(*no_response) + \
                   "No response tickets: {}.\n".format(' '.join(["#" + str(s) for s in no_response_list])) + \
                   "(Note that this does not include weekends while calculating time)"
        self.send_message(channel_id, response)


    def ticket_touch_command(self, channel_id, days_ago, username=None):
        self.validate_days_ago(channel_id, days_ago)
        touch_dict = self.rt_stat.ticket_touches(days_ago, username)
        if username:
            touch_count = touch_dict  # Rename.
            response = "{} ticket touches for {}".format(touch_count, username)

        self.send_message(channel_id, response)


    def validate_days_ago(self, channel_id, days_ago):
        """ Generic responder for invalid days_ago input. Returns false for invalid input."""
        if days_ago < 0:
            self.send_message(channel_id, "Positive numbers please!")
            return False
        if days_ago > 365:
            self.send_message(channel_id, "Sorry I only have tickets up to 1 year old... :cry:")
            return False
        return True

    def parse_message_for_tickets(self, message):
        """ Parse a message and create an integer list of ticket numbers. """
        message_split = message.split(" ")
        ticket_list = []
        for word in message_split:
            if not word:
                continue
            if word[0] == '#':
                try:
                    # Create a 
                    # Make sure things behind # is a legit issue
                    ticket_number = int(word[1:].translate(str.maketrans('', '', string.punctuation)))
                except ValueError:
                    continue
                if ticket_number < 0 or ticket_number in ticket_list:
                    continue
                ticket_list.append(ticket_number)
        ticket_list.sort()
        return ticket_list


    def hms(self, seconds):
        """
        Convert seconds to H:M:S in a tuple.
        """
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return (h, m, s)
