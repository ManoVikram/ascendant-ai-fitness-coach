import logging
import os
from concurrent.futures import ThreadPoolExecutor
import signal
import time

import grpc
from dotenv import load_dotenv
from progress_analyzer import ProgressAnalyzerService
from workout_generator_servicer import WorkoutGeneratorService
from coach_chat_servicer import CoachChatService
from proto import coach_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GracefulKiller:
    def __init__(self):
        self.kill_now = False
        signal.signal(signalnum=signal.SIGINT, handler=self.exit_gracefully)
        signal.signal(signalnum=signal.SIGTERM, handler=self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True

def serve():
    """
    Start the gRPC server for all the services
    """
    print("=" * 60)
    print("🚀 Starting Fitness Coach AI Services")
    print("=" * 60)

    # Step 1 - Load the environment variables
    load_dotenv()
    assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY is not set in the environment variables."

    # Step 2 - Created the gRPC server
    server = grpc.server(
        thread_pool=ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )

    # Step 3 - Register all the services to the server
    print("\n📦 Registering services...")

    coach_pb2_grpc.add_CoachChatServiceServicer_to_server(servicer=CoachChatService(), server=server)
    print("  ✅ CoachChat")

    coach_pb2_grpc.add_WorkoutGeneratorServiceServicer_to_server(servicer=WorkoutGeneratorService(), server=server)
    print("  ✅ WorkoutGenerator")

    coach_pb2_grpc.add_ProgressAnalyzerServiceServicer_to_server(servicer=ProgressAnalyzerService(), server=server)
    print("  ✅ ProgressAnalyzer")

    # Step 4 - Bind the server to a port
    grpc_port = os.getenv("GRPC_PORT", 50051)
    server.add_insecure_port(f"[::]:{grpc_port}")

    # Step 5 - Start the server
    server.start()
    print(f"🚀 Python gRPC server is running!")
    print("\n" + "=" * 60)
    print(f"✨ All services running on localhost: {grpc_port}")
    print("=" * 60)
    print("\n📡 Available gRPC services:")
    print("  • CoachChat.SendMessage")
    print("  • WorkoutGenerator.GenerateWorkout")
    print("  • ProgressAnalyzer.AnalyzeProgress")
    print("⏹️  Press Ctrl+C to stop\n")

    # Step 6 - Keep the server running and exit gracefully
    killer = GracefulKiller()

    try:
        while not killer.kill_now:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    print("🛑 Stopping server...")
    server.stop(grace=5)
    print("✅ Server stopped cleanly")


if __name__ == "__main__":
    serve()
