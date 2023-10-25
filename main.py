import argparse
import logging
import os
import sys
import getpass

from typing import Final

from datetime import datetime, timedelta

from pyVmomi.vim.event import EventHistoryCollector, Event, EventManager, EventFilterSpec
from pyVim.connect import SmartConnect
from pyVmomi import vim

ENCODING: Final[str] = "utf-8"
APP_NAME: Final[str] = 'vmwarelog'
APP_VERSION: Final[str] = '0.1'

# The default and also the max event number per page till vSphere v6.5, you can change it to a smaller value by SetCollectorPageSize().
PAGE_SIZE: Final[int] = 1000


def main() -> None:

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=f"""
            {APP_NAME} ({APP_VERSION}) is a demo tool which allows a file encrypted using a shared key allowing decryption via k of n number of keys.
            """)
    if (len(sys.argv)) == 1:
        parser.print_help()

    parser.add_argument("-h", "--host",
                        dest="host",
                        required=True,
                        help="VMware vCenter host IP or FQDN")

    parser.add_argument("-p", "--port",
                        dest="port",
                        required=True,
                        help="VMware vCenter host port to connect")

    args = parser.parse_args()

    host: str = str(args.host)  # type: ignore
    port: int = int(args.port)  # type: ignore

    user: str = input('VMware username:\n')
    password: str = getpass.getpass()

    time_filter, filter_spec = get_filters(from_now=timedelta(hours=1))

    event_collector: EventHistoryCollector = get_collector(
        host, port, user, password, filter_spec)

    events: list[Event] = get_events(
        event_collector=event_collector)

    print(
        "Got totally {} events in the given time range from {} to {}.".format(
            len(events), time_filter.beginTime, time_filter.endTime
        )
    )
    vmwarelogger = logging.getLogger('vmware')

    for _, event in enumerate(events):
        print(event.fullFormattedMessage)

        if (event.EventSeverity == Event.EventSeverity.error):
            vmwarelogger.error(event.fullFormattedMessage)
        elif (event.EventSeverity == Event.EventSeverity.warning):
            vmwarelogger.warning(event.fullFormattedMessage)
        else:
            vmwarelogger.info(event.fullFormattedMessage)


def get_events(event_collector: EventHistoryCollector) -> list[Event]:
    events: list[Event] = []

    while True:
        # If there's a huge number of events in the expected time range, this while loop will take a while.
        events_in_page: list[Event] = event_collector.ReadNext(
            maxCount=PAGE_SIZE)

        if len(events_in_page) == 0:
            break
        # or do other things on the collected events
        events.extend(events_in_page)

    # Please note that the events collected are not ordered by the event creation time
    # You might find the first event in the third page for example.
    return sorted(events, key=lambda x: x.createdTime)


def get_collector(host: str, port: int, user: str, password: str, filter_spec: EventFilterSpec) -> EventHistoryCollector:
    si: vim.ServiceInstance = SmartConnect(
        host=host, user=user, pwd=password, port=port)
    eventManager: EventManager = si.content.eventManager
    event_collector: EventHistoryCollector = eventManager.CreateCollector(
        filter=filter_spec)

    return event_collector


def get_filters(from_now: timedelta) -> tuple[EventFilterSpec.ByTime, EventFilterSpec]:
    time_filter = vim.event.EventFilterSpec.ByTime()
    now: datetime = datetime.now()
    time_filter.beginTime = now - from_now
    time_filter.endTime = now
    event_type_list: list[str] = []
    # If you want to also filter on certain events, uncomment the below event_type_list.
    # The EventFilterSpec full params details:
    # https://pubs.vmware.com/vsphere-6-5/topic/com.vmware.wssdk.smssdk.doc/vim.event.EventFilterSpec.html
    # event_type_list = ['VmRelocatedEvent', 'DrsVmMigratedEvent', 'VmMigratedEvent']
    filter_spec = vim.event.EventFilterSpec(
        eventTypeId=event_type_list, time=time_filter)

    return time_filter, filter_spec


def get_root_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    elif __file__:
        return os.path.dirname(__file__)
    else:
        return './'


if __name__ == "__main__":
    try:
        logging.basicConfig(filename=os.path.join(get_root_dir(), f'{APP_NAME}.log'),
                            encoding=ENCODING,
                            format='%(asctime)s:%(levelname)s:%(message)s',
                            datefmt="%Y-%m-%dT%H:%M:%S%z",
                            level=logging.INFO)

        excepthook = logging.error
        logging.info('Starting')
        main()
        logging.info('Exiting.')
    except KeyboardInterrupt:
        print('Cancelled by user.')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    except Exception as ex:
        print('ERROR: ' + str(ex))
        try:
            sys.exit(1)
        except SystemExit:
            os._exit(1)
