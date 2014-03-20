from datetime import datetime
import pymill


class Mockmill(object):
    def __init__(*args, **kwargs):
        pass

    def new_client(self, *args, **kwargs):
        return pymill.Client(
            id="client1",
            email=kwargs.get('email'),
            created_at=datetime.now()
        )

    def new_card(self, token, client):
        '''return a new card without checking the token'''
        return pymill.Payment(
            id="payment1",
            client=client,
            type="creditcard",
            card_type="mastercard",
            card_holder="hans horst",
            expire_month="01",
            expire_year="2017",
            last_4="1234",
            code="123",
            created_at=datetime.now()
        )

    def new_offer(*args, **kwargs):
        return pymill.Offer(
            id="offer1",
            name="offer1",
            amount=1911,
            interval="1 MONTH",
            trial_perioade_days=None
        )

    def new_subscription(self, *args, **kwargs):
        return pymill.Subscription(
            id="subscription1",
            offer="offer1",
            livemode=False,
            cancel_at_period_end=None,
            canceled_at=None,
            interval="month",
            payment="payment1",
            client="client1",
            next_capture_at=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )


class MockmillFailOffer(Mockmill):
    def new_offer(*args, **kwargs):
        json_data = {'exception': 'mocked exception', 'error': 'something went wrong'}
        raise Exception(json_data)
