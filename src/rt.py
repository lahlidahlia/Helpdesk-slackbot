import os
from datetime import datetime
import threading
import time
import re
import yaml
import json
import requests
import traceback

def call_clsinit(cls):
    cls.__clsinit__()
    return cls

@call_clsinit
class RT:
    base_url = "https://support.oit.pdx.edu/NoAuthCAS/REST/1.0/"
    cookies = None  # Not logged in if None.
    cache_dir = "../ticket_cache/"


    @classmethod
    def __clsinit__(cls):
        try:
            # Read in user/pass.
            f = open("../tokens/rt")
            cls.username, cls.password = tuple(f.read().strip().split(":"))
            f.close()
        except Exception as e:
            traceback.print_exc()
            print("Something went wrong while reading in username/password.")
            print("Make sure you have a file /tokens/rt with only username:password")
            f.close()
            exit()

        cls.login()
        #now.strftime("%Y-%m-%d")


    @classmethod
    def login(cls):
        payload = {"user": cls.username, "pass": cls.password}
        r = requests.post(cls.base_url, data=payload)
        if r.status_code == 200:
            print("Logged in successfully as " + cls.username + "!")
            cls.cookies = r.cookies
        elif r.status_code == 302:
            # 302 means you got redirected to SSO.
            print("Your username or password is incorrect!")
            exit()


    @classmethod
    def update_cache(cls):
        """
        Update the ticket since the last time it was updated.
        There needs to be a file in the cache called last_updated.
        """
        last_updated_date = ""
        with open(cls.cache_dir + "last_updated") as f:
            last_updated_date = f.read().strip()

        query = "Queue = 'uss-helpdesk' AND LastUpdated > '" + last_updated_date + "'"
        tickets = cls.rest_search_query(query)
        print("Updating " + str(len(tickets)) + " tickets!")
        for ticket in tickets:
            cls.update_cache_ticket(ticket)

        with open(cls.cache_dir + "last_updated", "w") as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


    @classmethod
    def get_cache_last_updated(cls):
        with open(cls.cache_dir + "last_updated") as f:
            return f.read().strip()
        

    @classmethod
    def update_cache_ticket(cls, ticket_number):
        try:
            print(str(ticket_number))
            data = cls.get_ticket(ticket_number)
            with open(cls.cache_dir + str(ticket_number) + ".json", "w") as f:
                json.dump(data, f, indent=2, sort_keys=True)
        except:
            print("Error on " + str(ticket_number))
            with open(cls.cache_dir + "error.log", "a") as f:
                f.write(datetime.now())
                f.write("Ticket: " + str(ticket_number))
                f.write(traceback.format_exc())
                f.write("---------------------")
        

    @classmethod
    def get_ticket(cls, ticket_number):
        """ 
        Returns a ticket's properties and list of histories in a dictionary.

        Errors raised: 
        - Type error if ticket number is not a number.
        - LookupError if ticket doesn't exist.            
        """
        ticket_number = int(ticket_number)
        # Get histories first because it has better ticket validation.
        histories = cls.rest_get_ticket_histories(ticket_number)
        properties = cls.rest_get_ticket_properties(ticket_number)
        properties["histories"] = histories
        return properties


    @classmethod
    def get_ticket_from_cache(cls, ticket_number):
        """
        Return the ticket as a dictionary from the cache.
        Returns None if the ticket isn't cached.
        """
        file_name = cls.cache_dir + str(ticket_number) + ".json"
        if not os.path.isfile(file_name):
            return None

        print("Retrieved ticket " + str(ticket_number))
        with open(file_name) as f:
            return json.load(f)

    @classmethod
    def rest_search_query(cls, query, orderby="-created", format_="i"):
        """ Run the given search query and return a list of ticket numbers. """
        url = cls.base_url + "search/ticket?query= " + query + "&orderby=" + orderby + "&format=" + format_
        print("Query URL: " + url)
        text = cls.rest_get_url(url)
        print("Got query!")
        return [int(x.split("/")[1]) for x in text.strip().splitlines()[2:]]


    @classmethod
    def rest_get_ticket_properties(cls, ticket_number):
        """
        ticket_number (int)
        Get the ticket number's properties from the rest API in text form.
        """
        ticket_url = cls.base_url + "ticket/" + str(ticket_number) + "/show"
        text = cls.rest_get_url(ticket_url)
        return cls.rest_parse_ticket_properties(text)


    @classmethod
    def rest_parse_ticket_properties(cls, text):
        """
        Return a dictionary containing ticket's properties.
        """
        # Trim first two lines.
        text = text[text.find('\n', text.find('\n')+1)+1:]
        text = cls.fix_yaml(text)
        properties = yaml.load(text)
        for k in properties:
            properties[k] = properties[k].strip()
        return properties


    @classmethod
    def rest_get_ticket_histories(cls, ticket_number):
        """
        ticket_number (int)
        Get the ticket number's histories from the rest API as a dictionary.
        Raise errors according to rest_validate_ticket.
        """
        ticket_url = cls.base_url + "ticket/" + str(ticket_number) + "/history?format=l"
        text = cls.rest_get_url(ticket_url)
        cls.rest_validate_ticket_histories(text)
        histories = cls.rest_parse_ticket_histories(text)
        return histories


    @classmethod
    def rest_validate_ticket_histories(cls, text):
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


    @classmethod
    def rest_parse_ticket_histories(cls, text):
        """
        text (str): Entire text returned from ticket history request.
        Returns a list of histories. Histories are events that happen in the ticket.
        Each history is a dictionary.
        """
        history_list = cls.fix_yaml(text).split("--\n\n#")

        # Parse into yaml.
        for i in range(len(history_list)):
            history = history_list[i]
            # Trim one line from beginning.
            history = history[history.find('\n')+1:]
            # Trim whitespaces from the end of each values.
            history = yaml.load(history)
            for k in history:
                history[k] = history[k].strip()
            history_list[i] = history
        return history_list


    @classmethod
    def rest_get_url(cls, url):
        """
        Perform a requests get on the URL. Returns the content's text.
        This ensures that if the session disconnected, we will reconnect.
        """
        if not cls.cookies:
            cls.login()

        r = requests.get(url, cookies=cls.cookies)

        if r.status_code == 302:
            # Try logging in again and do the same thing.
            cls.cookies = None
            cls.rest_get_url(url)
        elif r.status_code == 200:
            return r.text


    @classmethod
    def fix_yaml(cls, text):
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

    if len(sys.argv) > 1:
        if sys.argv[1] in ["-u", "--update"]:
            RT.update_cache()

    #s = RT.get_ticket_from_cache(699999)
    s = RT.get_ticket(699999)
    print(s)

    #from glob import glob
    #ticket_files = glob("../ticket_cache/*.yaml")
    #for file_name in ticket_files:
    #    print(str(len(ticket_files) - ticket_files.index(file_name)))
    #    with open(file_name) as f:
    #        ticket = f.read()
    #    ticket = yaml.load(ticket)
    #    with open(file_name[:-5] + ".json", 'w') as f:
    #        json.dump(ticket, f, indent=2, sort_keys=True)

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
