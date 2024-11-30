import csv
from django.core.management.base import BaseCommand
from shop.models import Order
from datetime import datetime

class Command(BaseCommand):
    help = 'Export orders to CSV for recommendation model'

    def handle(self, *args, **kwargs):

        orders = Order.objects.all()

        with open('orders_export.csv', 'w', newline='') as csvfile:
            fieldnames = ['USER_ID', 'ITEM_ID', 'TIMESTAMP', 'EVENT_TYPE']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            for order in orders:
                writer.writerow({
                    'USER_ID': order.user.id,
                    'ITEM_ID': order.product.id,
                    'TIMESTAMP': int(order.date_ordered.timestamp()), 
                    'EVENT_TYPE': 'buy'  
                })

        self.stdout.write(self.style.SUCCESS('DONE'))
