from typing import Final, Optional

from eventTypes import EventType

# Creds
USERNAME: Final[str] = ''
PASSWORD: Final[str] = ''

INTERVAL_MINUTES: int = 15

# The EventFilterSpec full params details:
# https://vdc-repo.vmware.com/vmwb-repository/dcr-public/da47f910-60ac-438b-8b9b-6122f4d14524/16b7274a-bf8b-4b4c-a05e-746f2aa93c8c/doc/vim.event.EventFilterSpec.html
# https://helpcenter.veeam.com/docs/mp/vmware_reference/vceventsdoc.html?ver=9a
#
# If you want to filter by event type, uncomment the sample types. If not defined, it would collect all types of events.
EVENT_TYPES: Optional[list[EventType]] = None
# = [
#     EventType.AccountCreatedEvent,
#     EventType.AccountRemovedEvent,
#     EventType.AccountUpdatedEvent,
#     EventType.UserUpgradeEvent,
#     EventType.UserPasswordChanged,
#     EventType.AdminPasswordNotChangedEvent,
#     EventType.VimAccountPasswordChangedEvent,
#     EventType.UserAssignedToGroup,
#     EventType.UserUnassignedFromGroup,
#     EventType.UserLoginSessionEvent,
#     EventType.UserLogoutSessionEvent,
#     EventType.HostAdminEnableEvent,
#     EventType.HostAdminDisableEvent,
#     EventType.AuthorizationEvent,
#     EventType.RoleAddedEvent,
#     EventType.RoleRemovedEvent,
#     EventType.RoleUpdatedEvent,
#     EventType.PermissionAddedEvent,
#     EventType.PermissionRemovedEvent,
#     EventType.PermissionUpdatedEvent,
#     EventType.HostConfigAppliedEvent,
#     EventType.ClusterReconfiguredEvent,
#     EventType.ClusterCreatedEvent,
#     EventType.ClusterDestroyedEvent,
#     EventType.HostAddedEvent,
#     EventType.HostRemovedEvent,
#     EventType.VmCreatedEvent,
#     EventType.VmCreatedEvent,
#     EventType.VmRenamedEvent,
#     EventType.VmClonedEvent,
#     EventType.VmRemovedEvent,
#     EventType.VmMigratedEvent,
#     EventType.EventEx,
#     EventType.ExtendedEvent
# ]
