from django.contrib import admin

from .models import BackendClient, BackendPayment, BackendPlan, BackendSubscription, BackendEvent
from . import get_subscription_model, get_plan_model

Subscription = get_subscription_model()
Plan = get_plan_model()


class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'trial_period_days', 'visible')
    list_filter = ('visible', )
    search_fields = ('name', 'amount')


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('plan', 'quantity', 'total', 'currency', 'deleted')
    list_filter = ('plan', 'quantity', 'currency', 'deleted')


admin.site.register(Plan, PlanAdmin)
admin.site.register(Subscription, SubscriptionAdmin)


class BackendClientAdmin(admin.ModelAdmin):
    list_display = ('backend', 'created_at', 'email', 'description')
    list_filter = ('backend', )


class BackendPaymentAdmin(admin.ModelAdmin):
    list_display = ('backend', 'created_at', 'payment_type', 'card_type', 'holder')
    list_filter = ('backend', 'payment_type', 'card_type')


class BackendPlanAdmin(admin.ModelAdmin):
    list_display = ('backend', 'created_at', 'plan', 'quantity', 'subscription_count_active', 'subscription_count_inactive')
    list_filter = ('backend', )


class BackendSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('backend', 'created_at', 'status')
    list_filter = ('backend', )


class BackendEventAdmin(admin.ModelAdmin):
    list_display = ('backend', 'created_at', 'event_type', 'processed')
    list_filter = ('backend', 'processed', 'event_type')

admin.site.register(BackendClient, BackendClientAdmin)
admin.site.register(BackendPayment, BackendPaymentAdmin)
admin.site.register(BackendPlan, BackendPlanAdmin)
admin.site.register(BackendSubscription, BackendSubscriptionAdmin)
admin.site.register(BackendEvent, BackendEventAdmin)
