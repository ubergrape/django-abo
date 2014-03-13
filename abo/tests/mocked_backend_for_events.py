from abo.factories import PlanFactory


class views(object):
    class EventProcessor:
        def __init__(self, backend_event):
            self.backend_event = backend_event

        def process(self):
            if self.backend_event.message.get("method") is "new_plan":
                plan = PlanFactory(name=self.backend_event.message.get("name"))
                self.backend_event.content_object = plan
                self.backend_event.save()
            else:
                raise NotImplementedError(self.backend_event.message.get("method"))
