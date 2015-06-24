from .handlers.disks import NodeDefaultsDisksHandler
from .handlers.disks import NodeDisksHandler
from .handlers.disks import NodeVolumesInformationHandler


# TODO(eli): Extension's urls must be versioned
urls = (
    r'/nodes/(?P<node_id>\d+)/disks/?$',
    NodeDisksHandler,
    r'/nodes/(?P<node_id>\d+)/disks/defaults/?$',
    NodeDefaultsDisksHandler,
    r'/nodes/(?P<node_id>\d+)/volumes/?$',
    NodeVolumesInformationHandler)
