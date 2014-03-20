from django.test import TestCase

from abo.models import BackendEvent


class BackendEventTestCase(TestCase):
    def test_event_processor_add_object(self):
        event = BackendEvent.objects.create(
            backend="abo.tests.mocked_backend_for_events",
            livemode=False,
            message={"method": "new_plan", "name": "test123"}
        )

        # processor should create new plan
        event.process()

        self.assertTrue(event.processed)
        self.assertEqual(event.content_object.name, "test123")

    def test_event_processor_fail(self):
        event = BackendEvent.objects.create(
            backend="abo.tests.mocked_backend_for_events",
            livemode=False,
            message={"method": "fail", "name": "test123"}
        )

        # processor should fail
        self.assertRaises(NotImplementedError, event.process)

        self.assertFalse(event.processed)
        self.assertEquals(event.object_id, None)
