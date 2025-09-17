import pytest

from flarchitect.utils.general import check_rate_prerequisites


@pytest.mark.parametrize(
    "service, module",
    [
        ("Memcached", "pymemcache"),
        ("Redis", "redis"),
        ("MongoDB", "pymongo"),
    ],
)
def test_check_rate_prerequisites_raises_when_missing(service, module):
    def fake_find_spec(name):
        return None if name == module else object()

    with pytest.raises(ImportError):
        check_rate_prerequisites(service, find_spec=fake_find_spec)

