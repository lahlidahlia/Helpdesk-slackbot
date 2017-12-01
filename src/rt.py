import os
from datetime import datetime
import threading
import time
import re
import yaml
import requests
import traceback

class RT:
    def __init__(self):
        self.base_url = "https://support.oit.pdx.edu/NoAuthCAS/REST/1.0/"
        self.cookies = None  # Not logged in if None.
        self.cache_dir = "../ticket_cache/"

        try:
            # Read in user/pass.
            f = open("../tokens/rt")
            self.username, self.password = tuple(f.read().strip().split(":"))
            f.close()
        except Exception as e:
            traceback.print_exc()
            print("Something went wrong while reading in username/password.")
            print("Make sure you have a file /tokens/rt with only username:password")
            f.close()
            exit()

        self.login()
        #now.strftime("%Y-%m-%d")


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


    def update_cache(self):
        """
        Update the ticket since the last time it was updated.
        There needs to be a file in the cache called last_updated.
        """
        last_updated_date = ""
        with open(self.cache_dir + "last_updated") as f:
            last_updated_date = f.read().strip()

        query = "Queue = 'uss-helpdesk' AND LastUpdated > '" + last_updated_date + "'"
        tickets = self.rest_search_query(query)
        print("Updating " + str(len(tickets)) + " tickets!")
        for ticket in tickets:
            self.update_ticket_cache(ticket)

        with open(self.cache_dir + "last_updated", "w") as f:
            f.write(datetime.now().strftime("%Y-%m-%d"))


    def update_ticket_cache(self, ticket_number):
        try:
            print(str(ticket_number))
            data = self.get_ticket(ticket_number)
            with open(self.cache_dir + str(ticket_number) + ".yaml", "w") as f:
                f.write(yaml.dump(data))
        except:
            print("Error on " + str(ticket_number))
            with open(self.cache_dir + "error.log", "a") as f:
                f.write(datetime.now())
                f.write("Ticket: " + str(ticket_number))
                f.write(traceback.format_exc())
                f.write("---------------------")
        

    def get_ticket(self, ticket_number):
        """ 
        Returns a ticket's properties and list of histories in a dictionary.

        Errors raised: 
        - Type error if ticket number is not a number.
        - LookupError if ticket doesn't exist.            
        """
        # Get histories first because it has better ticket validation.
        histories = self.rest_get_ticket_histories(ticket_number)
        properties = self.rest_get_ticket_properties(ticket_number)
        properties["histories"] = histories
        return properties


    def get_ticket_from_cache(self, ticket_number):
        """
        Return the ticket as a dictionary from the cache.
        Returns None if the ticket isn't cached.
        """
        file_name = self.cache_dir + str(ticket_number) + ".yaml"
        if not os.path.isfile(file_name):
            return None

        with open(file_name) as f:
            return yaml.load(f.read())


    def rest_search_query(self, query, orderby="-created", format_="i"):
        """ Run the given search query and return a list of ticket numbers. """
        url = self.base_url + "search/ticket?query= " + query + "&orderby=" + orderby + "&format=" + format_
        text = self.rest_get_url(url)
        return [int(x.split("/")[1]) for x in text.strip().splitlines()[2:]]


    def rest_get_ticket_properties(self, ticket_number):
        """
        ticket_number (int)
        Get the ticket number's properties from the rest API in text form.
        """
        ticket_url = self.base_url + "ticket/" + str(ticket_number) + "/show"
        text = self.rest_get_url(ticket_url)
        return self.rest_parse_ticket_properties(text)


    def rest_parse_ticket_properties(self, text):
        """
        Return a dictionary containing ticket's properties.
        """
        # Trim first two lines.
        text = text[text.find('\n', text.find('\n')+1)+1:]
        text = self.fix_yaml(text)

        return yaml.load(text)


    def rest_get_ticket_histories(self, ticket_number):
        """
        ticket_number (int)
        Get the ticket number's histories from the rest API as a dictionary.
        Raise errors according to rest_validate_ticket.
        """
        ticket_url = self.base_url + "ticket/" + str(ticket_number) + "/history?format=l"
        text = self.rest_get_url(ticket_url)
        self.rest_validate_ticket_histories(text)
        return self.rest_parse_ticket_histories(text)


    def rest_validate_ticket_histories(self, text):
        """
        Check to make sure input ticket number is good.
        Raise some errors if not.
        
        Errors raised: 
        - Type error if ticket number is not a number.
        - LookupError if ticket doesn't exist.            
        """
        to_validate = text.splitlines()[2]
        if (re.match("# Objects of type ticket must be specified by numeric id\.", to_validate) or
            re.match("# Invalid object specification\:", to_validate)):
            raise TypeError("Numeric only")
        if re.match("# Ticket [0-9]+ does not exist\.", to_validate):
            raise LookupError("Ticket doesn't exist")
        return True


    def rest_parse_ticket_histories(self, text):
        """
        text (str): Entire text returned from ticket history request.
        Returns a list of histories. Histories are events that happen in the ticket.
        Each history is a dictionary.
        """
        history_list = self.fix_yaml(text).split("--\n\n#")

        # Parse into yaml.
        for i in range(len(history_list)):
            history = history_list[i]
            # Trim one line from beginning.
            history = history[history.find('\n')+1:]
            history_list[i] = yaml.load(history)

        return history_list


    def rest_get_url(self, url):
        """
        Perform a requests get on the URL. Returns the content's text.
        This ensures that if the session disconnected, we will reconnect.
        """
        if not self.cookies:
            self.login()

        r = requests.get(url, cookies=self.cookies)

        if r.status_code == 302:
            # Try logging in again and do the same thing.
            self.cookies = None
            self.rest_get_url(url)
        elif r.status_code == 200:
            return r.text


    def fix_yaml(self, text):
        """
        Fix RT's yaml so that each values can contain special characters.
        This is done by making each values multiline strings by adding a > character.
        Returns the fixed yaml's text.
        """
        line_split = text.splitlines()

        # Trim response code.
        if "RT/4" in line_split[0]:
            line_split = line_split[1:]

        for i in range(len(line_split)):
            # Modify the yaml so that each value become a multiline string.
            # Otherwise special characters like # or : is not escaped properly.
            if line_split[i] and line_split[i][0] != ' ':
                line_split[i] = line_split[i].replace(":", ": >\n", 1)

        return  "\n".join(line_split)


if __name__ == '__main__':
    import sys

    rt = RT()

    if len(sys.argv) > 1:
        if sys.argv[1] in ["-u", "--update"]:
            rt.update_cache()

    print(rt.get_ticket_from_cache(699999))

    #query = "Queue = 'uss-helpdesk' AND Created > 'now - 360 days'"
    #tickets = rt.rest_search_query(query)

    #threads = 4
    #range_ = int(len(tickets)/threads)
    #print(range_)
    #for i in range(threads):
    #    split = tickets[range_*i : range_*(i+1)]
    #    if i == threads - 1:
    #        split = tickets[range_*i:]
    #    t = threading.Thread(target=save_tickets, args=((split,)))
    #    t.start()
