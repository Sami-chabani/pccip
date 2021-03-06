import datetime
from pm4py.objects.log.log import Event, EventLog
from pccip.passage_decomp.algorithm.constants import ARTIFICIAL_START, ARTIFICIAL_END


def generate_start_event() -> Event:
    """Generate an artificial start event.

    Returns:
        Event: Artificial start event.
    """
    start = {'concept:name': ARTIFICIAL_START,
             'lifecycle:transition': 'complete',
             'time:timestamp':
                 datetime.datetime(1, 1, 1, 0, 0,
                                   tzinfo=datetime.timezone(
                                       datetime.timedelta(seconds=3600)))
             }

    return Event(start)


def generate_end_event() -> Event:
    """Generate an artificial end event.

    Returns:
        Event: Artificial end event.
    """
    end = {'concept:name': ARTIFICIAL_END,
           'lifecycle:transition': 'complete',
           'time:timestamp':
               datetime.datetime(9999, 12, 31, 0, 0,
                                 tzinfo=datetime.timezone(
                                     datetime.timedelta(seconds=3600)))
           }

    return Event(end)


def extend_log(log: EventLog) -> EventLog:
    """Extend all traces in anevent log with an artificial start and
    end activity.

    Args:
        log (EventLog): Event log to extend

    Raises:
        TypeError: Raised when log parameter is not of type EventLog

    Returns:
        EventLog: Extended event log.
    """
    if not isinstance(log, EventLog):
        raise TypeError("Invalid log type")

    start = generate_start_event()
    end = generate_end_event()
    for trace in log:
        if trace[0]['concept:name'] is not ARTIFICIAL_START:
            trace.insert(0, start)
        if trace[-1]['concept:name'] is not ARTIFICIAL_END:
            trace.append(end)

    return log
