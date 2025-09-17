import pytest

from flarchitect.authentication.roles import roles_required, roles_accepted
from flarchitect.authentication.user import set_current_user
from flarchitect.exceptions import CustomHTTPException


class U:
    def __init__(self, roles):
        self.roles = roles


def test_roles_required_and_accepted():
    @roles_required("admin", "editor")
    def fn1():
        return "ok"

    @roles_accepted("user", "moderator")
    def fn2():
        return "ok"

    # Unauthenticated
    set_current_user(None)
    with pytest.raises(CustomHTTPException):
        fn1()

    # Missing one role -> forbidden for roles_required
    set_current_user(U(["admin"]))
    with pytest.raises(CustomHTTPException):
        fn1()

    # Any of -> allowed when one matches
    set_current_user(U(["moderator"]))
    assert fn2() == "ok"

