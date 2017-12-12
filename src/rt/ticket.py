from datetime import datetime

class Ticket:
    def __init__(self, content):
        """
        content (dict): The dictionary of ticket contents given by get_ticket()
        """
        self.content = content

        # Get ticket_number
        self.number = self._get_ticket_number()
        self.correspondences = self._get_correspondences()
        self.histories = self.content['histories']


    def _get_correspondences(self):
        """
        Returns a list of histories that has the type "correspond".
        """
        if not self.content or "histories" not in self.content:
            return None
        return [h for h in self.content["histories"] if h["Type"].strip() == "Correspond"]


    def _get_ticket_number(self):
        """
        Returns the ticket number.
        """
        # example: ticket/699999
        return self.content['id'].split('/')[1]


    def get_response_time(self):
        """
        Return the response time of the ticket in seconds.
        Return None if ticket has no correspondence.
        """
        created_time = self.parse_time(self.content['histories'][0]['Created'])

        if not self.correspondences:
            return None
        corr_time = self.parse_time(self.correspondences[0]['Created'])
        return (corr_time - created_time).seconds


    def parse_time(self, time):
        """
        time (str): The time string that is given by RT.
        Return a datetime.
        """
        time = time.strip()
        time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        return time
