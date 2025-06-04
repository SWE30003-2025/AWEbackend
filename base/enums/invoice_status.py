from enum import Enum

class INVOICE_STATUS(Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled" 
