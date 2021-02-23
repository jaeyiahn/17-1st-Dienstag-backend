import json
import jwt

from django.views   import View
from django.http    import JsonResponse, HttpResponse

from cart.models    import Cart, Order, OrderStatus, AddressInformation
from user.models    import User
from user.utils     import login_decorator
from product.models import Product
from voucher.models import Voucher


ORDER_STATUS_CHECK = 'checking_out'


class CartProductView(View):
    @login_decorator
    def post(self, request):
        try:
            data             = json.loads(request.body)
            product_id       = data.get('product_id')
            user_id          = request.user.id

            if Order.objects.filter(user_id=user_id, order_status__name=ORDER_STATUS_CHECK, carts__product_id=product_id).exists():

                return JsonResponse({'message': False}, status=403)

            if Order.objects.filter(user_id=user_id, order_status__name=ORDER_STATUS_CHECK).exists() and not Cart.objects.filter(product_id=product_id, order__order_status__name=ORDER_STATUS_CHECK, order__user_id=user_id).exists():
                Cart.objects.create(
                    product_id = product_id, 
                    order_id   = Order.objects.get(user_id=user_id, order_status__name=ORDER_STATUS_CHECK).id
                    )
                return JsonResponse({'message': 'SUCCESS'}, status=201)

            if not Order.objects.filter(user_id=user_id, order_status__name=ORDER_STATUS_CHECK).exists():
                Order.objects.create(
                        user_id         = user_id,
                        order_status_id = OrderStatus.objects.get(name=ORDER_STATUS_CHECK).id
                        )

                Cart.objects.create(
                        product_id = product_id,
                        order_id   = Order.objects.get(user_id=user_id, order_status__name=ORDER_STATUS_CHECK).id
                        )

                return JsonResponse({'message': 'SUCCESS'}, status=201)

        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)

class CartVoucherView(View):
    @login_decorator
    def post(self, request):
        try:
            data             = json.loads(request.body)
            voucher_quantity = data.get('voucher_quantity')
            voucher_price    = data.get('voucher_price')
            voucher_code     = data.get('voucher_code')
            user_id          = request.user.item_id

            if Order.objects.filter(user_id=user_id, order_status__name=ORDER_STATUS_CHECK).exists():
                Cart.objects.create(
                        voucher_id = Voucher.objects.create(
                            price    = voucher_price,
                            code     = voucher_code,
                            quantity = voucher_quantity).id,
                        order_id   = Order.objects.get(user_id=user_id, order_status__name=ORDER_STATUS_CHECK).id
                        )

                return JsonResponse({'message': 'SUCCESS'}, status=201) 

            Order.objects.create(
                    user_id         = user_id,
                    order_status_id = OrderStatus.objects.get(name=ORDER_STATUS_CHECK
                    ).id
                    )

            Cart.objects.create(
                    voucher_id = Voucher.objects.create(
                        price    = voucher_price,
                        code     = voucher_code,
                        quantity = voucher_quantity).id,
                    order_id   = Order.objects.get(user_id=user_id, order_status__name=ORDER_STATUS_CHECK).id
                    )

            return JsonResponse({'message': 'SUCCESS'}, status=201)

        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)

class CartView(View):
    @login_decorator
    def get(self, request):
        try:
            user_id          = request.user.id
            order            = Order.objects.get(user_id=user_id, order_status__name=ORDER_STATUS_CHECK)
            cart_list        = order.carts.all()
            total_price      = 0
            total_products   = 0
            total_items_list = []

            for cart in cart_list:
                if cart.product_id:
                    product_price  = int(Product.objects.get(id=cart.product_id).price)
                    total_price    += product_price
                    total_products += 1

                    total_items_list.append(
                            {
                                'product_id': cart.product_id,
                                'price'     : Product.objects.get(id=cart.product_id).price,
                                'quantity'  : 1,
                                'image_url' : Product.objects.get(id=cart.product_id).images.all()[0].image_url,
                                }
                            )

                if cart.voucher_id:
                    price          = int(Voucher.objects.get(id=cart.voucher_id).price)
                    quantity       = Voucher.objects.get(id=cart.voucher_id).quantity
                    voucher_price  = price * quantity
                    total_price    += voucher_price
                    total_products += quantity

                    total_items_list.append(
                            {
                                'voucher_id' : cart.voucher_id,
                                'price'      : Voucher.objects.get(id=cart.voucher_id).price,
                                'quantity'   : Voucher.objects.get(id=cart.voucher_id).quantity,
                                }
                            )

            return JsonResponse({
                'data': {
                    'total_price'      : total_price,
                    'total_items_list' : total_items_list,
                    'total_products'   : total_products
                    }}, status=200)
        
        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)

    @login_decorator
    def delete(self, request, item_id):
        try:
            user_id   = request.user.id
            order     = Order.objects.get(user_id=user_id, order_status__name=ORDER_STATUS_CHECK)
            cart_list = order.carts.all()

            for cart in cart_list:
                if cart.product_id == item_id:
                    cart.delete()
                if cart.voucher_id == item_id:
                    cart.delete()

            return JsonResponse({'message': 'SUCCESS'}, status=200)

        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)
