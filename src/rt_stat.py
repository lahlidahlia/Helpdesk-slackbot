from collections import namedtuple
from glob import glob
from rt import RT
from datetime import datetime

class RT_Stat:
    def __init__(self):
        pass


    def get_average_response_time(self, days_ago):
        """
        Get the average response time in seconds of tickets queried from given days ago.
        Returns: average time, slowest ticket (ticket, time), fastest ticket, no response amount (amount, ticket total)
        """
        query = "Queue = 'uss-helpdesk' AND Created > 'now - " + str(days_ago) + " days'"
        tickets = RT.rest_search_query(query)
        sum_ = 0
        ticket_count = len(tickets)

        slowest_ticket = (None, 0)  # (Ticket number, time (in sec))
        fastest_ticket = (None, 99999)
        no_response = 0
        for ticket in tickets:
            content = RT.get_ticket_from_cache(ticket)
            #print("Counting ticket #" + str(ticket))

            # Only get tickets from cache.
            if content == None:
                #print("Not in cache")
                ticket_count -= 1
                continue

            time = self.get_response_time(content)
            if not time:
                #print("No response")
                no_response += 1
                ticket_count -= 1
                continue

            #print(" - Response time: " + str(time) + "s")
            if time > slowest_ticket[1]:
                slowest_ticket = (ticket, time)
            if time < fastest_ticket[1]:
                fastest_ticket = (ticket, time)

            sum_ += time
        return sum_ / ticket_count, slowest_ticket, fastest_ticket, (no_response, len(tickets))
        

    def get_response_time(self, ticket_content):
        """
        Return the response time of the ticket in seconds.
        Return None if ticket has no correspondence.
        """
        created_time = self.parse_time(ticket_content['histories'][0]['Created'])

        corr = self.get_all_corr(ticket_content)
        if not corr:
            return None
        corr_time = self.parse_time(corr[0]['Created'])
        return (corr_time - created_time).seconds


    def get_all_corr(self, ticket_content):
        if not ticket_content or "histories" not in ticket_content:
            return None
        return [h for h in ticket_content["histories"] if h["Type"].strip() == "Correspond"]


    def parse_time(self, time):
        """
        time (str): The time string that is given by RT.
        Return a datetime.
        """
        time = time.strip()
        time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        return time


if __name__ == "__main__":
    rt_stat = RT_Stat()
    print(rt_stat.get_response_time(702522))
