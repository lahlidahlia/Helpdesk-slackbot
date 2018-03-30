from rt import RT

class RT_Stat:
    def __init__(self):
        pass


    def get_average_response_time(self, days_ago=30):
        """
        Get the average response time in seconds of tickets queried from given days ago.
        Returns: average time, slowest ticket (ticket_number, time), fastest ticket, (no response amount, ticket total), list of no response tickets.
        """
        query = "Queue = 'uss-helpdesk' AND Created > 'now - " + str(days_ago) + " days'"
        ticket_numbers = RT.rest_search_query(query)

        sum_ = 0
        ticket_count = len(ticket_numbers)

        slowest_ticket = (None, 0)  # (Ticket number, time (in sec))
        fastest_ticket = (None, 99999999)
        no_response = 0
        no_response_list = []
        for ticket_number in ticket_numbers:
            ticket = RT.get_ticket_from_cache(ticket_number)

            # Only get tickets from cache.
            if ticket == None:
                # Not in cache.
                ticket_count -= 1
                continue

            time = ticket.get_response_time()
            if not time:
                # No correspondences.
                if ticket.status != 'resolved' and \
                   ticket.status != 'rejected' and \
                   not ticket.is_qthelper:
                    # Instant resolves and rejected tickets don't count as no_response.
                    no_response += 1
                    no_response_list.append(ticket_number)
                ticket_count -= 1
                continue

            if time > slowest_ticket[1]:
                slowest_ticket = (ticket.number, time)
            if time < fastest_ticket[1]:
                fastest_ticket = (ticket.number, time)

            sum_ += time
        if ticket_count == 0:
            return None
        return sum_ / ticket_count, slowest_ticket, fastest_ticket, (no_response, len(ticket_numbers)), no_response_list

    def untag_blame(self):
        """
        Returns dict of {person: [tickets], ...}, where person is who should have tagged it. 
        On the basis that the first person who respond to a ticket should tag it. 
        If there's no response then the person who resolved it should have tagged it.
        Returns None if there is no untagged ticket.
        """
        query = "Created > '2015-09-13' AND Queue = 'uss-helpdesk' AND Status = 'resolved' AND ( CF.{USS_Ticket_Category} IS NULL OR CF.{USS_Ticket_Subcategory} IS NULL )"
        ticket_numbers = RT.rest_search_query(query)

        ticket_count = len(ticket_numbers)

        untagged_list = {}

        def add_untagged(person, ticket_number):
            """
            Add the ticket number to the person's list.
            person (str): name of the blamed person.
            """
            if person in untagged_list:
                untagged_list[person].append(ticket_number)
            else:
                untagged_list[person] = [ticket_number]

        for ticket_number in ticket_numbers:
            ticket = RT.get_ticket_from_cache(ticket_number)

            if ticket == None:
                # Not in cache.
                ticket_count -= 1
                continue

            if ticket.first_non_user_corr:
                # If ticket has a response from non user then blame that person.
                add_untagged(ticket.first_non_user_corr['Creator'], ticket_number)
            elif len(ticket.resolves) and 'Creator' in ticket.resolves[0]:
                # Else blames the person who resolved it.
                add_untagged(ticket.resolves[0]['Creator'], ticket_number)

        if ticket_count == 0:
            return None

        return untagged_list


    def ticket_touches(self, days_ago=30, username=None):
        """ 
        Count the ticket touches. If username is not provided, will include everyone in the result.
        Returns a dictionary of {name: count}. If username is provided, will only return count.
        """
        query = "Queue = 'uss-helpdesk' AND LastUpdated > 'now - " + str(days_ago) + " days'"
        ticket_numbers = RT.rest_search_query(query)
        
        touch_dict = {}
        for ticket_number in ticket_numbers:
            ticket = RT.get_ticket_from_cache(ticket_number)

            # Only get tickets from cache.
            if ticket == None:
                # Not in cache.
                continue

            # This also handles case one username case.
            # Definitely slower than handling that separately, but this is cleaner.
            # If performance is necessary, can add separate check for one username case.
            for un in ticket.touches:
                if un not in touch_dict:
                    touch_dict[un] = 0
                touch_dict[un] += 1
                        
        if username:
            return touch_dict[username]
        return touch_dict 
                



if __name__ == "__main__":
    rt_stat = RT_Stat()
    #print(rt_stat.get_response_time(702522))
    print(rt_stat.untag_blame())
