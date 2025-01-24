import asyncio
import time

class AsyncTCPClientProtocol(asyncio.Protocol):
    def __init__(self, loop, message_count, batch_size):
        self.loop = loop
        self.transport = None
        self.start_time = None
        self.message_count = message_count
        self.batch_size = batch_size
        self.sent_count = 0
        self.round_trip_times = []  # Store RTTs for the current batch

    def connection_made(self, transport):
        self.transport = transport
        print("Connected to the server.")
        self.send_message()

    def data_received(self, data):
        message = data.decode()
        try:
            # Extract timestamp from the message (e.g., "Message 1:1632342345.2345")
            timestamp_str = message.split(":")[1]
            start_time = float(timestamp_str)  # Convert to float
        except IndexError:
            start_time = time.time()  # Default to current time if not available
        
        # Calculate round-trip time
        end_time = time.time()
        round_trip_time = end_time - start_time
        self.round_trip_times.append(round_trip_time)

        self.sent_count += 1

        # Once the batch size is reached, calculate and print the average RTT
        if self.sent_count % self.batch_size == 0:
            avg_rtt = sum(self.round_trip_times[-self.batch_size:]) / self.batch_size
            print(f"Batch {self.sent_count // self.batch_size} - Average RTT for {self.batch_size} messages: {avg_rtt:.6f} seconds")
            self.round_trip_times = []  # Clear RTTs for the next batch

        # Send next message if the total message count is not reached
        if self.sent_count < self.message_count:
            self.send_message()
        else:
            # After sending all messages, close the connection
            self.close_connection()

    def send_message(self):
        self.start_time = time.time()  # Record the timestamp before sending
        message = f"Message {self.sent_count + 1}:{self.start_time}"  # Send message with timestamp
        self.transport.write(message.encode())

    def close_connection(self):
        if self.transport:
            print("Closing connection...")
            self.transport.close()

    def connection_lost(self, exc):
        if exc:
            print(f"Connection lost: {exc}")
        else:
            print("Connection closed gracefully.")

        # Ensure the loop is stopped only after the connection has been closed
        if self.loop.is_running():
            self.loop.stop()  # Safely stop the event loop


async def run_client():
    loop = asyncio.get_running_loop()
    
    # Define message count and batch size
    message_count = 500  # Send 500 messages
    batch_size = 50    # Print RTT every 50 messages

    # Connect to the server
    _, protocol = await loop.create_connection(
        lambda: AsyncTCPClientProtocol(loop, message_count, batch_size), host="127.0.0.1", port=4444
    )

    # Wait for the connection to finish processing
    await asyncio.sleep(1)  # Increased time to allow more messages to send/receive

if __name__ == "__main__":
    try:
        asyncio.run(run_client())  # Run the event loop and manage the tasks correctly
    except KeyboardInterrupt:
        print("Client interrupted and stopped.")
