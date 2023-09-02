from datetime import datetime, timedelta, date, time

WEEKDAY = {
    0: 'MON',
    1: 'TUE',
    2: 'WED',
    3: 'THU',
    4: 'FRI',
    5: 'SAT',
    6: 'SUN'
}


def get_timeslots(docs, scheds, appoints):
    # Considerations:
    #   - time slots have a 1-hour size
    #   - a continuous schedule doesn't span across different days
    #   - the current day is 06-11-2022 (SUN)
    #   - calculates 2 weeks of timeslots, starting on current day
    timeslots = {}  # { id_doctor: [(datetime, enabled),...] }
    num_weeks = 2
    for d in docs:  # For each doctor

        timeslots[d['id']] = []

        curr_day = date(2022, 11, 6)  # Considered as the current day
        test_day = curr_day

        while test_day < curr_day + timedelta(days=7 * num_weeks):  # For each day
            test_weekday = WEEKDAY[test_day.weekday()]  # MON, TUE,...

            test_scheds = [s for s in scheds
                           if s['id_doctor'] == d['id'] and s['day_of_week'] == test_weekday]

            for s in test_scheds:  # For all schedules of the doctor on the day
                test_timeslot = datetime.combine(test_day, time()) + s['start_time']

                test_appoints = [a for a in appoints
                                 if a['id_doctor'] == d['id'] and a['start_date'].date() == test_day]

                while test_timeslot < datetime.combine(test_day, time()) + s['end_time']:  # For each timeslot
                    timeslots[d['id']] += [
                        (test_timeslot,
                         True if test_timeslot not in [a['start_date'] for a in test_appoints] else False)
                    ]
                    test_timeslot += timedelta(hours=1)
            test_day += timedelta(days=1)
    return timeslots
