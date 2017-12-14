from datetime import datetime

class Ticket:
    """
    Contains shortcut variables to data on a single ticket.
    Beware that as more shortcut variables get added, this class can become a performance choke point
    since every ticket gets constructed into this object.
    """


    def __init__(self, content):
        """
        content (dict): The dictionary of ticket contents given by get_ticket()
        """
        self.content = content

        # Trivial shortcuts (for frequently used items).
        self.status = self.content['Status']
        self.histories = self.content['histories']
        # What RT returns for ticket number: ticket/699999
        self.number = self.content['id'].split('/')[1]
        self.user = self.content['Requestors']
        # Was this ticket made by qthelper.
        self.is_qthelper = True if self.content['Creator'] == 'qthelper' else False

        self.correspondences = self._get_correspondences()
        self.last_correspondence = None if not self.correspondences \
                                        else self.correspondences[len(self.correspondences) - 1]
        self.resolves = self._get_resolves()


    def _get_correspondences(self):
        """
        Returns a list of histories that has the type "correspond".
        """
        if not self.content or 'histories' not in self.content:
            return None
        return [h for h in self.histories if h['Type'] == 'Correspond']


    def _get_resolves(self):
        """
        Return list of histories that indicate someone resolving a ticket.
        """
        if not self.content or 'histories' not in self.content:
            return None
        return [h for h in self.histories if h['Type'].strip() == 'Status' and h['NewValue'] == 'resolved']


    def get_response_time(self):
        """
        Return the average response time of the ticket in seconds.
        This looks for user correspondence and times the follow-up correspondence.
        Return None if ticket has no correspondence from non-users.
        """
        if not self.correspondences:
            return None

        corr_list = self.correspondences  # Variable shortener.

        total_time = 0
        count = 0

        if corr_list[0]['Creator'] != self.user:
            # First correspondence is from OIT (aka replying to a ticket created by user).
            created_time = self.parse_time(self.histories[0]['Created'])
            first_corr_time = self.parse_time(corr_list[0]['Created'])
            total_time = (first_corr_time - created_time).seconds
            count = 1

        for i in range(len(corr_list)):
            if corr_list[i]['Creator'] == self.user:
                if i+1 != len(corr_list) and corr_list[i+1]['Creator'] != self.user:
                    corr_list[i]
                    total_time += (self.parse_time(corr_list[i-1]['Created']) - 
                                    self.parse_time(corr_list[i]['Created'])).seconds
                    count += 1

        if count == 0:
            return None

        return total_time / count


    def parse_time(self, time):
        """
        time (str): The time string that is given by RT.
        Return a datetime.
        """
        time = time.strip()
        time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        return time
