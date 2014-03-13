from django.dispatch import Signal

new_subscription = Signal(providing_args=['subscription'])
new_subscription.__doc__ = """Sent after creating a subscription"""

payment_error = Signal(providing_args=['error_code', 'exception'])
payment_error.__doc__ = """Is sent whenever an error occurs during payment"""
