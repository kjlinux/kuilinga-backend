from app.crud.base import CRUDBase
from app.models.site import Site
from app.schemas.site import SiteCreate, SiteUpdate

class CRUDSite(CRUDBase[Site, SiteCreate, SiteUpdate]):
    pass

site = CRUDSite(Site)
