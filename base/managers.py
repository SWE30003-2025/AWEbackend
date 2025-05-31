from base.models.product_model import ProductModel

class InventoryManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InventoryManager, cls).__new__(cls)
        return cls._instance

    def get_stock(self, product_id):
        product = ProductModel.objects.get(pk=product_id)
        return getattr(product, 'stock', None)

    def set_stock(self, product_id, quantity):
        product = ProductModel.objects.get(pk=product_id)
        product.stock = quantity
        product.save()
        return product.stock

    def adjust_stock(self, product_id, amount):
        product = ProductModel.objects.get(pk=product_id)
        if not hasattr(product, 'stock'):
            product.stock = 0
        product.stock += amount
        product.save()
        return product.stock

    def all_inventory(self):
        return [(p, getattr(p, 'stock', None)) for p in ProductModel.objects.all()] 
