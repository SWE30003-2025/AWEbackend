from datetime import timedelta
import uuid

from django.db import transaction
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from base.models import ShoppingCartModel, CartItemModel, ProductModel, OrderModel, OrderItemModel, InvoiceModel, PaymentModel, ReceiptModel
from base.managers import InventoryManager, ShipmentManager
from base.enums import ROLE, INVOICE_STATUS, ORDER_PAYMENT_STATUS

from api.serializers import ShoppingCartModelSerializer
from api.permissions import HasRolePermission, get_authenticated_user

class ShoppingCartViewSet(viewsets.ViewSet):
    def get_permissions(self):
        """Ensure only customers can access the shopping cart"""
        return [HasRolePermission([ROLE.CUSTOMER])]

    def list(self, request):
        """Get the current user's shopping cart - GET /api/shopping-cart/"""
        user = get_authenticated_user(request)
        cart, created = ShoppingCartModel.objects.get_or_create(user=user)
        serializer = ShoppingCartModelSerializer(cart)

        return Response(serializer.data)

    def create(self, request):
        """Add item to cart - POST /api/shopping-cart/"""
        user = get_authenticated_user(request)
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)

        if not product_id:
            return Response(
                {"error": "product_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = ProductModel.objects.get(id=product_id)
            cart, created = ShoppingCartModel.objects.get_or_create(user=user)
            
            # Check if item already exists in cart
            cart_item, item_created = CartItemModel.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={"quantity": quantity}
            )
            
            if not item_created:
                # Update quantity if item already exists
                cart_item.quantity += quantity
                cart_item.save()

            serializer = ShoppingCartModelSerializer(cart)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ProductModel.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["put"], url_path="update-item")
    def update_item(self, request):
        """
        Update item quantity in cart - 
        PUT /api/shopping-cart/update-item/
        """
        user = get_authenticated_user(request)
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity")

        if not product_id or quantity is None:
            return Response(
                {"error": "product_id and quantity are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cart = ShoppingCartModel.objects.get(user=user)
            cart_item = CartItemModel.objects.get(cart=cart, product_id=product_id)
            
            if quantity <= 0:
                cart_item.delete()
            else:
                cart_item.quantity = quantity
                cart_item.save()

            serializer = ShoppingCartModelSerializer(cart)

            return Response(serializer.data)

        except (ShoppingCartModel.DoesNotExist, CartItemModel.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["delete"], url_path="remove-item")
    def remove_item(self, request):
        """
        Remove item from cart - 
        DELETE /api/shopping-cart/remove-item/
        """
        user = get_authenticated_user(request)
        product_id = request.data.get("product_id")

        if not product_id:
            return Response(
                {"error": "product_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cart = ShoppingCartModel.objects.get(user=user)
            cart_item = CartItemModel.objects.get(cart=cart, product_id=product_id)
            cart_item.delete()

            serializer = ShoppingCartModelSerializer(cart)
            return Response(serializer.data)

        except (ShoppingCartModel.DoesNotExist, CartItemModel.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["post"], url_path="place-order")
    def place_order(self, request):
        """
        Place order from cart items - creates order and invoice (payment pending)
        POST /api/shopping-cart/place-order/
        """
        user = get_authenticated_user(request)
        
        shipping_data = {
            "shipping_full_name": request.data.get("full_name"),
            "shipping_address": request.data.get("address"),
            "shipping_city": request.data.get("city"),
            "shipping_postal_code": request.data.get("postal_code")
        }
        
        for field, value in shipping_data.items():
            if not value:
                return Response(
                    {"error": f"{field} is required for shipping"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            cart = ShoppingCartModel.objects.get(user=user)
            
            if not cart.items.exists():
                return Response(
                    {"error": "Cart is empty"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check stock availability
            inventory_manager = InventoryManager()
            for item in cart.items.all():
                available_stock = inventory_manager.get_stock(item.product.id)
                if available_stock is None or available_stock < item.quantity:
                    return Response(
                        {"error": f"Insufficient stock for {item.product.name}. Available: {available_stock}, Requested: {item.quantity}"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Create order and reserve stock in a transaction
            with transaction.atomic():
                # Create order
                order = OrderModel.objects.create(
                    user=user,
                    payment_status=ORDER_PAYMENT_STATUS.PENDING.value,
                    **shipping_data
                )

                # Create order items and reserve stock
                for item in cart.items.all():
                    OrderItemModel.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price
                    )
                    
                    # Reserve stock (reduce from inventory)
                    inventory_manager.adjust_stock(item.product.id, -item.quantity)

                invoice = self._create_invoice(order)

                cart.clear()

                print(f"Order {order.id} placed successfully! Stock reserved, invoice generated.")

                return Response({
                    "message": "Order placed successfully! Please proceed to payment.",
                    "order_id": order.id,
                    "invoice": {
                        "id": invoice.id,
                        "invoice_number": invoice.invoice_number,
                        "amount_due": str(invoice.amount_due),
                        "due_date": invoice.due_date,
                        "status": invoice.status
                    }
                }, status=status.HTTP_201_CREATED)

        except ShoppingCartModel.DoesNotExist:
            return Response(
                {"error": "Cart not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to place order: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], url_path="pay-invoice")
    def pay_invoice(self, request):
        """
        Pay an invoice using wallet - processes payment and generates receipt
        POST /api/shopping-cart/pay-invoice/
        """
        user = get_authenticated_user(request)
        invoice_id = request.data.get("invoice_id")

        if not invoice_id:
            return Response(
                {"error": "invoice_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get invoice and verify ownership
            invoice = InvoiceModel.objects.get(id=invoice_id, order__user=user)
            
            if invoice.status == INVOICE_STATUS.PAID.value:
                return Response(
                    {"error": "Invoice has already been paid"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            payment_result = self._process_payment(invoice, user)
            
            if not payment_result["success"]:
                return Response(
                    {"error": payment_result["error"]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create shipment after successful payment
            shipment_manager = ShipmentManager()
            shipment = shipment_manager.create_shipment(invoice.order)

            return Response({
                "message": "Payment successful! Your order is now being processed for shipment.",
                "payment": {
                    "transaction_id": payment_result['payment'].transaction_id,
                    "amount": str(payment_result['payment'].amount),
                    "status": payment_result['payment'].status
                },
                "receipt": {
                    "receipt_number": payment_result['receipt'].receipt_number,
                    "amount_paid": str(payment_result['receipt'].amount_paid)
                },
                "shipment": {
                    "tracking_number": shipment.tracking_number,
                    "status": shipment.status,
                    "estimated_delivery": shipment.estimated_delivery
                }
            }, status=status.HTTP_200_OK)

        except InvoiceModel.DoesNotExist:
            return Response(
                {"error": "Invoice not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Payment failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _create_invoice(self, order):
        """Create an invoice for an order"""
        invoice_number = f"INV{uuid.uuid4().hex[:8].upper()}"
        
        due_date = timezone.now() + timedelta(days=7)
        
        invoice = InvoiceModel.objects.create(
            order=order,
            invoice_number=invoice_number,
            amount_due=order.total,
            due_date=due_date
        )
        
        print(f"Invoice {invoice_number} created for Order {order.id} - Amount: ${order.total}")
        return invoice

    def _process_payment(self, invoice, user):
        """Process wallet payment for an invoice"""
        transaction_id = f"TXN{uuid.uuid4().hex[:10].upper()}"
        
        if user.wallet < invoice.amount_due:
            return {
                "success": False,
                "error": f"Insufficient wallet balance. Required: ${invoice.amount_due}, Available: ${user.wallet}"
            }
        
        try:
            # Create payment record
            payment = PaymentModel.objects.create(
                invoice=invoice,
                user=user,
                amount=invoice.amount_due,
                transaction_id=transaction_id
            )
            
            # Deduct from wallet
            user.wallet -= invoice.amount_due
            user.save()
            
            payment.mark_as_completed()
            
            invoice.mark_as_paid()
            
            order = invoice.order
            order.payment_status = ORDER_PAYMENT_STATUS.PAID.value
            order.save()
            
            receipt = self._generate_receipt(payment)
            
            print(f"Payment {transaction_id} completed for Invoice {invoice.invoice_number}")
            
            return {
                "success": True,
                "payment": payment,
                "receipt": receipt
            }
            
        except Exception as e:
            print(f"Payment failed: {str(e)}")
            return {
                "success": False,
                "error": f"Payment processing failed: {str(e)}"
            }

    def _generate_receipt(self, payment):
        """Generate a receipt for a completed payment"""
        receipt_number = f"RCP{uuid.uuid4().hex[:8].upper()}"
        
        receipt = ReceiptModel.objects.create(
            payment=payment,
            receipt_number=receipt_number,
            amount_paid=payment.amount
        )
        
        print(f"Receipt {receipt_number} generated for Payment {payment.transaction_id}")
        return receipt 
