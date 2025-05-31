from enum import Enum

class ROLE(Enum):
    """
    Roles for UserModel
    """
    CUSTOMER = "customer"
    ADMIN = "admin"
    SHIPMENT_MANAGER = "shipment_manager"
    STATISTICS_MANAGER = "statistics_manager"
    INVENTORY_MANAGER = "inventory_manager"
