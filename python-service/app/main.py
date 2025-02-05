from threading import Thread
from server import start_websocket_server

def main():
  # Start WebSocket server
  start_websocket_server()

if __name__ == '__main__':
  main()