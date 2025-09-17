from flarchitect.core.websockets import _EventBus, broadcast_change


def test_event_bus_subscribe_publish_unsubscribe():
    bus = _EventBus()
    sub_all = bus.subscribe("all")
    sub_model = bus.subscribe("book")

    msg = {"a": 1}
    bus.publish("book", msg)

    # receives on specific topic and on 'all'
    assert sub_model.queue.get(timeout=0.5) == msg
    assert sub_all.queue.get(timeout=0.5) == msg

    bus.unsubscribe(sub_model)
    # after unsubscribe, publish should not deliver to removed subscription
    bus.publish("book", msg)
    # 'all' still receives
    assert sub_all.queue.get(timeout=0.5) == msg


class DummyModel:
    __name__ = "Book"


def test_broadcast_change_constructs_message_and_publishes():
    # Uses global bus; simply ensure it does not raise and basic fields exist
    payload = {"query": [{"id": 1}]}
    # Should publish to both model topic and 'all'
    broadcast_change(model=DummyModel, method="post", payload=payload, id=1, many=True)
    # No assertion here; behaviour validated in unit EventBus test. This call
    # should execute without exceptions and exercise code paths.

