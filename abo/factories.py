# -*- coding: UTF-8 -*-

import factory
import random
from factory import fuzzy

from .models import AbstractSubscription, AbstractPlan, PLAN_INTERVAL_CHOICES

from . import get_plan_model, get_subscription_model

INTERVAL_CHOICES = [x for (x, y) in PLAN_INTERVAL_CHOICES]


class AbstractPlanFactory(factory.django.DjangoModelFactory):
    ABSTRACT_FACTORY = True
    FACTORY_FOR = AbstractPlan

    name = factory.LazyAttribute(lambda o: "{} {}{}".format(
        random.choice(['Simple', 'Almost Free', 'Wow so', 'Lean', 'Product']),
        random.choice(['Premium', 'Pro', 'Plus', 'Extended', 'Enterprise']),
        random.choice(['', ' 50% off', ' Extended', ' X', ' 9000']),
    ))
    amount = fuzzy.FuzzyInteger(1, 50000)
    interval = fuzzy.FuzzyChoice(INTERVAL_CHOICES)
    interval_count = fuzzy.FuzzyInteger(1, 3)
    trial_period_days = fuzzy.FuzzyChoice([None, 7, 30])
    visible = True


class PlanFactory(AbstractPlanFactory):
    FACTORY_FOR = get_plan_model()


class AbstractSubscriptionFactory(factory.django.DjangoModelFactory):
    ABSTRACT_FACTORY = True
    FACTORY_FOR = AbstractSubscription

    quantity = fuzzy.FuzzyInteger(1, 100)
    currency = 'EUR'
    deleted = False


class SubscriptionFactory(AbstractSubscriptionFactory):
    FACTORY_FOR = get_subscription_model()

    plan = factory.SubFactory(PlanFactory)
