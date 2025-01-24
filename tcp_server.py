import asyncio
import time

class AsyncTCPServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        peername = transport.get_extra_info("peername")
        print(f"Connection established with {peername}")

    def data_received(self, data):
        # Respond back to the client with the same message
        message = data.decode()
        print(f"Received: {message}")

        # Echo the message back to the client
        self.transport.write(data)

    def connection_lost(self, exc):
        if exc:
            print(f"Connection lost: {exc}")
        else:
            print("Connection closed gracefully.")

async def main():
    loop = asyncio.get_running_loop()

    # Start the TCP server
    server = await loop.create_server(
        lambda: AsyncTCPServerProtocol(), host="127.0.0.1", port=4444
    )
    print("TCP server listening on 127.0.0.1:4444")

    try:
        await server.serve_forever()
    except asyncio.CancelledError:
        print("Server shut down.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shut down.")
