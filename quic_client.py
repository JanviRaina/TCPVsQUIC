import asyncio
import platform
from aioquic.asyncio import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import HandshakeCompleted, StreamDataReceived
import time

class EchoClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sent_count = 0
        self.round_trip_times = []
        self.message_count = 500  # Total messages to send
        self.batch_size = 50  # Print average RTT every 50 messages

    def quic_event_received(self, event):
        if isinstance(event, HandshakeCompleted):
            print("Handshake completed.")
            self.send_message()  # Start sending messages

        elif isinstance(event, StreamDataReceived):
            # Extract only the timestamp from the server's message (e.g., "Echo: Message 1:1737621740.722383")
            message = event.data.decode()
            try:
                timestamp_str = message.split(":")[2]  # Get the timestamp part from the message
                start_time = float(timestamp_str)  # Convert to float
            except IndexError:
                print("Error: Could not extract timestamp from the server's message.")
                return

            # Calculate round-trip time
            end_time = time.time()
            round_trip_time = end_time - start_time
            self.round_trip_times.append(round_trip_time)
            self.sent_count += 1

            # Calculate average RTT after every batch of messages
            if self.sent_count % self.batch_size == 0:
                avg_rtt = sum(self.round_trip_times[-self.batch_size:]) / self.batch_size
                print(f"Batch {self.sent_count // self.batch_size} - Average RTT: {avg_rtt:.6f} seconds")

            # Continue sending if not complete
            if self.sent_count < self.message_count:
                self.send_message()

    def send_message(self):
        # Use the next available stream ID for client-initiated streams
        stream_id = self._quic.get_next_available_stream_id()
        message = f"Message {self.sent_count + 1}:{time.time()}"  # Send current time with message
        self._quic.send_stream_data(stream_id, message.encode(), end_stream=True)

async def main():
    configuration = QuicConfiguration(is_client=True)
    configuration.load_verify_locations("cert.pem")

    async with connect(
        "127.0.0.1", 4433, configuration=configuration, create_protocol=EchoClientProtocol
    ) as protocol:
        await asyncio.sleep(10)  # Allow enough time for all messages to be processed

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            pass
