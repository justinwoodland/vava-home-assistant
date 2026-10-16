import pytest
import pytest_socket
from aiohttp import web

from custom_components.vava_projector.api.http import VavaHttpClient

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def _enable_socket_for_http_tests():
    pytest_socket.enable_socket()
    yield


@pytest.fixture
async def volume_app():
    async def get_volume(request):
        return web.Response(
            text="{'status':'ok','action':'get_volume,'currentVolume':'3','maxVolume':'100','mute':'false'}"
        )

    async def keycode(request):
        assert "keycode" in request.query
        assert request.query["keycode"] == "24"
        return web.Response(text="<title>OK</title>")

    app = web.Application()
    app.router.add_get("/remote/get_volume", get_volume)
    app.router.add_get("/remote/keycode_control", keycode)
    return app


async def test_get_volume(aiohttp_client, volume_app):
    client = await aiohttp_client(volume_app)
    url = client.make_url("/")
    http = VavaHttpClient(client.session, url.host, url.port)
    info = await http.async_get_volume()
    assert info.ok is True
    assert info.current == 3


async def test_send_keycode(aiohttp_client, volume_app):
    client = await aiohttp_client(volume_app)
    url = client.make_url("/")
    http = VavaHttpClient(client.session, url.host, url.port)
    await http.async_send_keycode(24)
