import asyncio


class VavaTcpClient:
    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port

    async def async_send_keyevent(self, keycode: int) -> None:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self._host, self._port), timeout=3
        )
        try:
            writer.write(f"KEYEVENT\r\n{keycode}\r\n\r\n".encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
