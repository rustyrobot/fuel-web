from sqlalchemy import Integer
from sqlalchemy import Column

from nailgun.db.sqlalchemy.models.base import Base
from nailgun.db.sqlalchemy.models.fields import JSON


class NodeVolumes(Base):
    # TODO(eli): Tablename should have extension name and version as a prefix
    __tablename__ = 'volume_manager_1_0_0_node_volumes'
    # TODO(eli): figure out why there is duplicated definition error
    __table_args__ = {"useexisting": True}
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer)
    volumes = Column(JSON, default={})
    disks = Column(JSON, default={})
