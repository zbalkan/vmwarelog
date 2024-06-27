import argparse
import getpass
import json
import logging
import os
import socket
import sys
from datetime import datetime, timedelta
from typing import Final, Optional

from pyVim.connect import SmartConnect
from pyVmomi import vim

from eventTypes import EventType

USE_CONF: bool = False
try:
    from conf import EVENT_TYPES, HOST, INTERVAL_MINUTES, LOG_PATH, PASSWORD, PORT, USERNAME
    USE_CONF = True
except ImportError:
    print('No configuration file defined.')


ENCODING: Final[str] = "utf-8"
APP_NAME: Final[str] = 'vmwarelog'
APP_VERSION: Final[str] = '0.2'

# The default and also the max event number per page till vSphere v6.5, you can change it to a smaller value by SetCollectorPageSize().
PAGE_SIZE: Final[int] = 1000


def get_events(event_collector: vim.event.EventHistoryCollector) -> list[vim.event.Event]:
    events: list[vim.event.Event] = []

    while True:
        # If there's a huge number of events in the expected time range, this while loop will take a while.
        events_in_page: list[vim.event.Event] = event_collector.ReadNext(
            maxCount=PAGE_SIZE)

        if len(events_in_page) == 0:
            break
        # or do other things on the collected events
        events.extend(events_in_page)

    # Please note that the events collected are not ordered by the event creation time
    # You might find the first event in the third page for example.
    return sorted(events, key=lambda x: x.createdTime)


def get_collector(host: str, port: int, user: str, password: str, filter_spec: vim.event.EventFilterSpec) -> vim.event.EventHistoryCollector:

    si: vim.ServiceInstance = SmartConnect(
        host=host,
        port=port,
        user=user,
        pwd=password,
        disableSslCertValidation=True,
        connectionPoolTimeout=30)  # 30 seconds for timeout
    eventManager: vim.event.EventManager = si.content.eventManager
    event_collector: vim.event.EventHistoryCollector = eventManager.CreateCollector(
        filter=filter_spec)

    return event_collector


def get_filters(from_now: timedelta, event_types: Optional[list[EventType]] = None) -> tuple[vim.event.EventFilterSpec.ByTime, vim.event.EventFilterSpec]:
    time_filter = vim.event.EventFilterSpec.ByTime()
    now: datetime = datetime.now()
    time_filter.beginTime = now - from_now
    time_filter.endTime = now
    if event_types:
        filter_spec = vim.event.EventFilterSpec(
            eventTypeId=[e.name for e in event_types], time=time_filter)
    else:
        filter_spec = vim.event.EventFilterSpec(time=time_filter)

    return time_filter, filter_spec


def add_entity_to_root(root, entity_name, entity) -> None:
    if entity is not None:
        try:
            if (hasattr(entity, "name")):
                root["vmware"][entity_name] = {
                    "name": entity.name
                }
            else:
                root["vmware"][entity_name] = entity
        except Exception as e:
            print(f"Error adding {entity_name} to root: {e}")


def main() -> None:

    start_time = datetime.now()

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=f"""
            {APP_NAME} ({APP_VERSION}) is a tool to pull VMware vCenter logs based on time and type filters. It is better than collecting syslog with all of the noise.
            """)

    parser.add_argument("-t", "--target",
                        dest="vCenter",
                        required=False,
                        help="VMware vCenter host IP or FQDN")

    parser.add_argument("-p", "--port",
                        dest="port",
                        required=False,
                        default=443,
                        help="VMware vCenter host port to connect (Default: 443)")

    parser.add_argument("-o", "--output",
                        dest='output',
                        required=False,
                        help="The file where vCenter logs are written")

    parser.add_argument("-c", "--conf",
                        dest="conf",
                        required=False,
                        default="conf.py",
                        help="Path to configuration file (Default: conf.py)")

    args = parser.parse_args()

    if (USE_CONF):
        host: str = HOST
    else:
        host = str(args.vCenter)  # type: ignore

    try:
        fqdn = socket.getfqdn(host)
        ip = socket.gethostbyname(fqdn)
    except:
        raise Exception(f"Could not resolve target host name: {host}")

    if (USE_CONF):
        port: int = PORT
    else:
        port = int(args.port)  # type: ignore

    if (USE_CONF):
        output: str = LOG_PATH
    else:
        output = str(args.output)  # type: ignore

    output = os.path.abspath(output)
    output_dir: str = os.path.dirname(output)
    if ((os.path.exists(output_dir) is False) and (os.access(output_dir, os.W_OK) is False)):
        raise Exception(f"Path does not exist or is not accessible.")
    logging.info(f"Output: {output}")

    if (USE_CONF):
        user: str = USERNAME
        password: str = PASSWORD
    else:
        user = input('VMware username:\n')
        password = getpass.getpass()

    print(f"Connecting to {fqdn}:{port} ({ip}) as {user}...")
    logging.info(f"Connecting to {fqdn}:{port} ({ip}) as {user}...")

    if (USE_CONF):
        interval: int = INTERVAL_MINUTES * 60
    else:
        interval = 15 * 60

    # In order to tolerate the query time drift between two runs,
    # we calculate the time between the start of application and filtering time
    # Also, we add 2 extra seconds as a buffer.
    if (EVENT_TYPES):
        time_filter, filter_spec = get_filters(
            from_now=timedelta(seconds=interval + (datetime.now() - start_time).seconds + 2), event_types=EVENT_TYPES)
    else:
        time_filter, filter_spec = get_filters(
            from_now=timedelta(seconds=interval + (datetime.now() - start_time).seconds + 2))

    event_collector: vim.event.EventHistoryCollector = get_collector(
        host, port, user, password, filter_spec)

    print("Connected.")
    logging.info("Connected.")
    print("Generated collector.")
    logging.info("Generated collector.")

    print("Querying events...")
    logging.info("Querying events...")
    events: list[vim.event.Event] = get_events(
        event_collector=event_collector)

    msg: str = "Fetched totally {} events in the given time range from {} to {}.".format(
        len(events), time_filter.beginTime, time_filter.endTime
    )
    print(msg)
    logging.info(msg)

    print(f"Writing events to target: {output}...")
    logging.info(f"Writing events to target: {output}...")
    with open(output, mode="a+", encoding=ENCODING) as vcenter_logs:
        for _, event in enumerate(events):
            try:
                root = {
                    "vmware": {
                        "timestamp": event.createdTime.isoformat(),
                        "event": event.fullFormattedMessage,
                        "username": event.userName,
                        "properties": {k: v for k, v in event.__dict__.items() if (
                            v is not None and v != '<unset>')}
                    }
                }

                add_entity_to_root(root, "host", event.host)
                add_entity_to_root(root, "vm", event.vm)
                add_entity_to_root(root, "ds", event.ds)
                add_entity_to_root(root, "dvs", event.dvs)
                add_entity_to_root(root, "net", event.net)
                add_entity_to_root(root, "computeResource",
                                   event.computeResource)
                add_entity_to_root(root, "datacenter", event.datacenter)
                add_entity_to_root(root, "info", getattr(event, "info", None))
                add_entity_to_root(root, "ipAddress",
                                   getattr(event, "ipAddress", None))

                vcenter_logs.write(json.dumps(
                    root, sort_keys=True, default=str) + "\n")
            except AttributeError as e:
                logging.error(f"Error processing event {event}: {e}")

    print("Log collection completed!")
    logging.info("Log collection completed!")


if __name__ == "__main__":
    try:
        logging.basicConfig(filename=os.path.join(f'/var/log/{APP_NAME}.log'),
                            encoding=ENCODING,
                            format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
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
