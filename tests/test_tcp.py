import asyncio

import pytest
import pytest_socket

from custom_components.vava_projector.api.tcp import VavaTcpClient

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def _enable_socket_for_tcp_tests():
    pytest_socket.enable_socket()
    yield


async def test_send_keyevent_payload():
    received = asyncio.Future()

    async def handle(reader, writer):
        data = await reader.read(64)
        received.set_result(data)
        writer.close()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    client = VavaTcpClient("127.0.0.1", port)
    await client.async_send_keyevent(24)
    payload = await asyncio.wait_for(received, 2)
    assert payload == b"KEYEVENT\r\n24\r\n\r\n"
    server.close()
    await server.wait_closed()
