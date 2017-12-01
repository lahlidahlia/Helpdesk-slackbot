from glob import glob
from rt import RT
from datetime import datetime

class RT_Stat:
    def __init__(self):
        pass


    def get_average_response_time(self, days_ago):
        """
        Get the average response time in seconds of tickets queried from given days ago.
        """
        query = "Queue = 'uss-helpdesk' AND Created > 'now - " + str(days_ago) + " days'"
        tickets = RT.rest_search_query(query)
        sum_ = 0
        ticket_count = len(tickets)
        #import pdb; pdb.set_trace()
        for ticket in tickets:
            content = RT.get_ticket_from_cache(ticket)
            if content == None:
                continue
            time = self.get_response_time(content)
            if not time:
                ticket_count -= 1
                continue
            sum_ += time
        return sum_ / ticket_count
        

    def get_response_time(self, ticket_content):
        """
        Return the response time of the ticket in seconds.
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
