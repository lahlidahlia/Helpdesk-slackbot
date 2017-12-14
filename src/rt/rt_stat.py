from rt import RT

class RT_Stat:
    def __init__(self):
        pass


    def get_average_response_time(self, days_ago):
        """
        Get the average response time in seconds of tickets queried from given days ago.
        Returns: average time, slowest ticket (ticket_number, time), fastest ticket, (no response amount, ticket total).
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
        

if __name__ == "__main__":
    rt_stat = RT_Stat()
    print(rt_stat.get_response_time(702522))
