from app.api.routes import interactions as interaction_routes


def test_track_client_event_requires_event_name():
    request = type("Req", (), {"client": type("Client", (), {"host": "127.0.0.1"})(), "headers": {}})()
    payload = interaction_routes.ClientEventRequest(event_name="   ", qa_log_id=None, metadata=None)

    try:
        interaction_routes.track_client_event(payload, request, db=object())
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400
        assert getattr(exc, "detail", None) == "Missing event_name"
    else:
        raise AssertionError("Expected HTTPException")


def test_track_client_event_accepts_low_match_event():
    request = type("Req", (), {"client": type("Client", (), {"host": "127.0.0.1"})(), "headers": {}})()
    payload = interaction_routes.ClientEventRequest(
        event_name="low_match_action",
        qa_log_id=12,
        metadata={"action": "refine_question", "theme": "Healing"},
    )

    called = {}

    def fake_log_product_event(db, event_name, user_ip, qa_log_id=None, metadata=None):
        called["db"] = db
        called["event_name"] = event_name
        called["user_ip"] = user_ip
        called["qa_log_id"] = qa_log_id
        called["metadata"] = metadata

    import app.storage.repository as repository

    original = repository.log_product_event
    repository.log_product_event = fake_log_product_event
    response = interaction_routes.track_client_event(payload, request, db=object())
    repository.log_product_event = original

    assert response == {"status": "ok"}
    assert called["event_name"] == "low_match_action"
    assert called["user_ip"] == "127.0.0.1"
    assert called["qa_log_id"] == 12
    assert called["metadata"]["action"] == "refine_question"
