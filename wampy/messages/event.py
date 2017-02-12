from wampy.messages.message import Message


class Event(Message):
    """ When a Subscriber_is deemed to be a receiver, the Broker sends
    the Subscriber an "EVENT" message:

        [EVENT, SUBSCRIBED.Subscription|id, PUBLISHED.Publication|id,
         Details|dict]

            or

        [EVENT, SUBSCRIBED.Subscription|id, PUBLISHED.Publication|id,
               Details|dict, PUBLISH.Arguments|list]

            or

        [EVENT, SUBSCRIBED.Subscription|id, PUBLISHED.Publication|id,
         Details|dict, PUBLISH.Arguments|list, PUBLISH.ArgumentKw|dict]

    """
    WAMP_CODE = 36

    def __init__(
    		self, wamp_code, subscription_id, publication_id, details_dict,
    		publish_args=None, publish_kwargs=None,
    ):

        assert wamp_code == self.WAMP_CODE

        self.subscription_id = subscription_id
        self.publication_id = publication_id
        self.details = details_dict
        self.publish_args = publish_args or []
        self.publish_kwargs = publish_kwargs or {}

        self.message = [
            self.WAMP_CODE, self.subscription_id, self.publication_id,
            self.details, self.publish_args, self.publish_kwargs,
        ]