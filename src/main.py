import argparse
import getpass
import logging
import os
import socket
import sys
import time
from datetime import datetime, timedelta
from typing import Final, Optional

from pyVim.connect import SmartConnect
from pyVmomi import vim

from eventTypes import EventType

ENCODING: Final[str] = "utf-8"
APP_NAME: Final[str] = 'vmwarelog'
APP_VERSION: Final[str] = '0.1'

# The default and also the max event number per page till vSphere v6.5, you can change it to a smaller value by SetCollectorPageSize().
PAGE_SIZE: Final[int] = 1000


def retry(func, ex_type=Exception, limit=0, wait_ms=100, wait_increase_ratio=2, logger=None):  # -> Any:
    """
    Retry a function invocation until no exception occurs
    :param func: function to invoke
    :param ex_type: retry only if exception is subclass of this type
    :param limit: maximum number of invocation attempts
    :param wait_ms: initial wait time after each attempt in milliseconds.
    :param wait_increase_ratio: increase wait period by multiplying this value after each attempt.
    :param logger: if not None, retry attempts will be logged to this logging.logger
    :return: result of first successful invocation
    :raises: last invocation exception if attempts exhausted or exception is not an instance of ex_type

    Reference: https://davidoha.medium.com/python-retry-on-exception-d36fa58df4e1
    """
    attempt = 1
    while True:
        try:
            return func()
        except Exception as ex:
            if not isinstance(ex, ex_type):
                raise ex  # type: ignore
            if 0 < limit <= attempt:
                print("no more attempts")

                if logger:
                    logger.warning("no more attempts")
                raise ex

            print(f"failed execution attempt {attempt}")
            if logger:
                logger.error(
                    f"failed execution attempt {attempt}", exc_info=ex)

            attempt += 1
            print(f"waiting {wait_ms} ms before attempt {attempt}")
            if logger:
                logger.info(f"waiting {wait_ms} ms before attempt {attempt}")
            time.sleep(wait_ms / 1000)
            wait_ms *= wait_increase_ratio


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


def main() -> None:

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=f"""
            {APP_NAME} ({APP_VERSION}) is a tool to pull VMware vCenter logs based on time and type filters. It is better than collecting syslog with all of the noise.
            """)
    if (len(sys.argv)) == 1:
        parser.print_help()

    parser.add_argument("-t", "--target",
                        dest="vCenter",
                        required=True,
                        help="VMware vCenter host IP or FQDN")

    parser.add_argument("-p", "--port",
                        dest="port",
                        required=False,
                        default=443,
                        help="VMware vCenter host port to connect (Default: 443)")

    parser.add_argument("-o", "--output",
                        dest='output',
                        required=True,
                        help="The file where vCenter logs are written")

    args = parser.parse_args()

    host: str = str(args.vCenter)  # type: ignore
    try:
        fqdn = socket.getfqdn(host)
        ip = socket.gethostbyname(fqdn)
    except:
        raise Exception(f"Could not resolve target host name: {host}")

    port: int = int(args.port)  # type: ignore
    output: str = str(args.output)  # type: ignore
    output = os.path.abspath(output)
    # if os.path.exists(os.path.dirname(output)):
    #     raise Exception(
    #         "The parent folder of the vCenter log path does not exist.")

    user: str = input('VMware username:\n')
    password: str = getpass.getpass()

    print(f"Connecting to {fqdn}:{port} ({ip}) as {user}...")
    logging.info(f"Connecting to {fqdn}:{port} ({ip}) as {user}...")

    # The EventFilterSpec full params details:
    # https://vdc-repo.vmware.com/vmwb-repository/dcr-public/da47f910-60ac-438b-8b9b-6122f4d14524/16b7274a-bf8b-4b4c-a05e-746f2aa93c8c/doc/vim.event.EventFilterSpec.html
    # https://helpcenter.veeam.com/docs/mp/vmware_reference/vceventsdoc.html?ver=9a
    #
    event_types: list[EventType] = [
        EventType.AccountCreatedEvent,
        EventType.AccountRemovedEvent,
        EventType.AccountUpdatedEvent,
        EventType.UserUpgradeEvent,
        EventType.UserPasswordChanged,
        EventType.AdminPasswordNotChangedEvent,
        EventType.VimAccountPasswordChangedEvent,
        EventType.UserAssignedToGroup,
        EventType.UserUnassignedFromGroup,
        EventType.UserLoginSessionEvent,
        EventType.UserLogoutSessionEvent,
        EventType.HostAdminEnableEvent,
        EventType.HostAdminDisableEvent,
        EventType.AuthorizationEvent,
        EventType.RoleAddedEvent,
        EventType.RoleRemovedEvent,
        EventType.RoleUpdatedEvent,
        EventType.PermissionAddedEvent,
        EventType.PermissionRemovedEvent,
        EventType.PermissionUpdatedEvent,
        EventType.HostConfigAppliedEvent,
        EventType.ClusterReconfiguredEvent,
        EventType.ClusterCreatedEvent,
        EventType.ClusterDestroyedEvent,
        EventType.HostAddedEvent,
        EventType.HostRemovedEvent,
        EventType.VmCreatedEvent,
        EventType.VmCreatedEvent,
        EventType.VmRenamedEvent,
        EventType.VmClonedEvent,
        EventType.VmRemovedEvent,
        EventType.VmMigratedEvent
    ]

    time_filter, filter_spec = get_filters(
        from_now=timedelta(hours=1), event_types=event_types)

    # Try once, wait 10 seconds and retry. Then 20, then 30...
    # Retry 5 times in total.
    event_collector: vim.event.EventHistoryCollector = retry(
        func=get_collector(
            host, port, user, password, filter_spec),
        ex_type=Exception,
        limit=5,
        wait_ms=10000,
        wait_increase_ratio=10000,
        logger=logging.getLogger())

    print("Connected.")
    logging.info("Connected.")
    print("Generated collector.")
    logging.info("Connected.")

    print("Querying events...")
    logging.info("Connected.")
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
            vcenter_logs.write(event.fullFormattedMessage)

    print("Log collection completed!")
    logging.info("Log collection completed!")


if __name__ == "__main__":
    try:
        logging.basicConfig(filename=os.path.join(f'./{APP_NAME}.log'),
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
