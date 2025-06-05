from rest_framework.routers import DefaultRouter
from .controllers import *

router = DefaultRouter()
router.register(r"user", UserViewSet, "user")
router.register(r"product", ProductViewSet, "product")
router.register(r"inventory", InventoryViewSet, "inventory")
router.register(r"order", OrderViewSet, "order")
router.register(r"category", CategoryViewSet, "category")
router.register(r"shipment", ShipmentViewSet, "shipment")
router.register(r"shopping-cart", ShoppingCartViewSet, "shopping-cart")

urlpatterns = router.urls
