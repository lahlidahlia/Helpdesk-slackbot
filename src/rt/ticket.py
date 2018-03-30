import pytz
from datetime import datetime
from datetime import timedelta

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
        self.tag = self.content['CF.{USS_Ticket_Category}'] if 'CF.{USS_Ticket_Category}' in self.content else None
        self.subtag = self.content['CF.{USS_Ticket_Subcategory}'] if 'CF.{USS_Ticket_Subcategory}' in self.content else None

        self.correspondences = self._get_correspondences()
        self.first_non_user_corr = self._first_corr_from_non_user()
        self.last_correspondence = None if not self.correspondences \
                                        else self.correspondences[len(self.correspondences) - 1]

        self.touches = self._get_touches()  # List of people that touched this ticket.


        self.resolves = self._get_resolves()



    def _get_correspondences(self):
        """
        Returns a list of histories that has the type "correspond".
        """
        if not self.content or 'histories' not in self.content:
            return None
        return [h for h in self.histories if h['Type'] == 'Correspond']


    def _first_corr_from_non_user(self):
        """
        Returns first history of a correspondence from non-user.
        """
        for history in self.correspondences:
            if history['Creator'] != self.user:
                return history

        return None
                

    def _get_touches(self):
        """
        Return a list of people that have touched this ticket.
        Filters out RT_System as well as users with actual email (aka not from OIT).
        """
        ret = []
        for h in self.histories:
            if '@' in h['Creator'] or 'RT_System' in h['Creator']:
                # Filter out RT_System and emails (assuming no OIT usernames include '@'.
                continue
            if h['Creator'] not in ret:
                ret.append(h['Creator'])
        return ret
            

        

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

        #import pdb; pdb.set_trace()
        if corr_list[0]['Creator'] != self.user:
            # First correspondence is from OIT (aka replying to a ticket created by user).
            created_time = self.parse_time(self.histories[0]['Created'])
            first_corr_time = self.parse_time(corr_list[0]['Created'])
            total_time += self.get_time_difference(created_time, first_corr_time)
            count = 1

        for i in range(len(corr_list)):
            if corr_list[i]['Creator'] == self.user:
                if i+1 != len(corr_list) and corr_list[i+1]['Creator'] != self.user:
                    corr_list[i]
                    total_time += self.get_time_difference(self.parse_time(corr_list[i]['Created']),
                                                           self.parse_time(corr_list[i+1]['Created']))
                    count += 1

        if count == 0:
            return None

        return total_time / count


    def get_time_difference(self, startTime, endTime):
        """
        Returns the difference between two datetimes in seconds.
        Ignores weekends. Weekends is Saturday and Sunday, aka 48 hours worth of seconds.
        """
        sec_in_day = 86400
        #import pdb; pdb.set_trace()
        if startTime.weekday() in [5, 6]:
            # If time is weekend, use Monday instead.
            # This does assume that replies will never be made during the weekend.
            startTime = startTime + timedelta(days=7-startTime.weekday())
            startTime = startTime.replace(hour=0, minute=0, second=0, microsecond=0)
        if endTime.weekday() in [5,6]:
            endTime = endTime + timedelta(days=7-endTime.weekday())
            endTime = endTime.replace(hour=0, minute=0, second=0, microsecond=0)
        time_delta = endTime - startTime
        ret = time_delta.days * sec_in_day + time_delta.seconds
        if endTime.weekday() < startTime.weekday():
            ret -= sec_in_day * 2
        if time_delta.days / 7 > 0:
            ret -= sec_in_day * int(time_delta.days/7) * 2
        return ret


    def parse_time(self, time):
        """
        time (str): The time string that is given by RT. RT gives UTC time, so it needs to be converted.
        Return a datetime in the PST timezone.
        """
        time = time.strip()
        time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone('UTC'))
        return time.astimezone(pytz.timezone('US/Pacific'))


if __name__ == '__main__':
    from rt import RT
    t = RT.get_ticket(700000)
    #print(t.get_response_time())
    print(t.touches)
