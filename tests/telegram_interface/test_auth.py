from telegram_interface.auth import is_authorized


def test_is_authorized_true_when_ids_match():
    assert is_authorized(111, 111) is True


def test_is_authorized_false_when_ids_differ():
    assert is_authorized(111, 222) is False
