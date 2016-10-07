import pytest
from mock import ANY

from wampy import Peer
from wampy.messages import Message
from wampy.roles.callee import rpc
from wampy.roles.subscriber import subscribe

from test.helpers import assert_stops_raising


class MetaClient(Peer):

    def __init__(self, *args, **kwargs):
        super(MetaClient, self).__init__(*args, **kwargs)

        self.on_create_call_count = 0
        self.on_register_call_count = 0
        self.on_unregister_call_count = 0

    @subscribe(topic="wamp.registration.on_create")
    def on_create_handler(self, *args, **kwargs):
        """ Fired when a registration is created through a
        registration request for an URI which was
        previously without a registration. """
        self.on_create_call_count += 1

    @subscribe(topic="wamp.registration.on_register")
    def on_register_handler(self, *args, **kwargs):
        """ Fired when a _Callee_ session is added to a
        registration. """
        self.on_register_call_count += 1

    @subscribe(topic="wamp.registration.on_unregister")
    def on_unregister_handler(self, *args, **kwargs):
        """Fired when a Callee session is removed from a
        registration. """
        self.on_unregister_call_count += 1


@pytest.yield_fixture
def meta_client(router):
    peer = MetaClient(name="meta subscriber")
    with peer:
        yield peer


class TestMetaEvents:

    def test_on_create(self, meta_client):

        class Client(Peer):
            @rpc
            def foo(self):
                pass

        callee = Client(name="foo")

        assert meta_client.on_create_call_count == 0

        with callee:
            def check_call_count():
                assert meta_client.on_create_call_count == 1

            assert_stops_raising(check_call_count)

    def test_on_register(self, meta_client):

        class Client(Peer):
            @rpc
            def foo(self):
                pass

        callee = Client(name="foo provider")
        caller = Peer(name="foo consumner")

        with callee:
            with caller:
                caller.rpc.foo()

            def check_call_count():
                assert meta_client.on_register_call_count == 1

            assert_stops_raising(check_call_count)

    def test_on_unregister(self, meta_client):

        class Client(Peer):
            @rpc
            def foo(self):
                pass

        callee = Client(name="foo provider")

        assert meta_client.on_unregister_call_count == 0

        with callee:
            pass

        def check_call_count():
            assert meta_client.on_unregister_call_count == 1

        assert_stops_raising(check_call_count)


class TestMetaProcedures:

    def test_get_registration_list(self, router):
        client = Peer(name="Caller")
        with client:
            registrations = client.get_registration_list()
            registered = registrations['exact']
            assert len(registered) == 0

            class DateService(Peer):
                @rpc
                def get_date(self):
                    return "2016-01-01"

            service = DateService(name="Date Service")
            with service:
                registrations = client.get_registration_list()
                registered = registrations['exact']
                assert len(registered) == 1

    def test_get_registration_lookup(self, router):
        client = Peer(name="Caller")
        with client:
            registration_id = client.get_registration_lookup(
                procedure_name="spam")
            assert registration_id is None

            class SpamService(Peer):
                @rpc
                def spam(self):
                    return "eggs and ham"

            service = SpamService(name="Spam Service")
            with service:
                registration_id = client.get_registration_lookup(
                    procedure_name="spam")
                assert registration_id in service.registration_map.values()
                assert len(service.registration_map.values()) == 1

    def test_registration_info_not_found(self, router):
        client = Peer(name="Caller")
        with client:
            response_msg = client.get_registration_info(registration_id="spam")

            response_code, call_code, _, _, error_uri, args = (
                response_msg)

            assert response_code == Message.ERROR
            assert call_code == Message.CALL
            assert error_uri == u'wamp.error.no_such_registration'
            assert args == [
                u'no registration with ID spam exists on this dealer']

    def test_get_registration_info(self, router):
        class SpamService(Peer):
            @rpc
            def spam(self):
                return "eggs and ham"

        service = SpamService(name="Spam Service")
        with service:
            registration_id = service.registration_map['spam']
            with Peer(name="Caller") as client:
                info = client.get_registration_info(
                    registration_id=registration_id
                )

        expected_info = {
            'match': 'exact',
            'created': ANY,
            'uri': 'spam',
            'invoke': 'single',
            'id': registration_id,
        }

        assert expected_info == info
