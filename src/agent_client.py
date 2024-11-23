from collections import defaultdict
from zmq import Context, Socket, DEALER, REQ
import zmq
import json
import threading
import time
from typing import List, Callable, Dict
import logging

from src.helpers.orchestrator import Message

class AgentClient:
    def __init__(self, 
                 name: str, 
                 orchestrator_host: str,
                 message_port: int = 5555,
                 registration_port: int = 5556):
        self.name = name
        self.orchestrator_host = orchestrator_host
        self.message_port = message_port
        self.registration_port = registration_port
        self.agent_id = None
        self.subscriptions: Dict[str, List[Callable]] = {}
        self._running = False
        self._lock = threading.Lock()
        self.logger = logging.getLogger(f"Agent-{name}")
        self.ingress_messages_callbacks = defaultdict(set)

    def start(self) -> bool:
        with self._lock:
            if not self._running:
                # Initialize ZMQ context
                self.context = Context()
                
                # Socket for registration (do this first)
                self.registration_socket = self.context.socket(REQ)
                self.registration_socket.connect(f"tcp://{self.orchestrator_host}:{self.registration_port}")
                
                # Register with orchestrator before setting up message socket
                if self._register():
                    # Socket for receiving messages
                    self.message_socket = self.context.socket(DEALER)
                    self.message_socket.setsockopt_string(zmq.IDENTITY, self.agent_id)
                    self.message_socket.connect(f"tcp://{self.orchestrator_host}:{self.message_port}")
                    
                    self._running = True
                    self._start_heartbeat()
                    self._start_receive_message_handler()
                    self.logger.info(f"Agent {self.name} started and registered")
                    return True
                return False

    def _register(self) -> bool:
        """Register with the orchestrator"""
        registration_data = {
            'action': 'register',
            'name': self.name,
            'address': f"{self.orchestrator_host}:{self.message_port}",
            'subscriptions': list(self.ingress_messages_callbacks.keys())
        }

        print(f"Sending registration data: {registration_data}")
        
        self.registration_socket.send_json(registration_data)
        response = self.registration_socket.recv_json()
        
        if response['status'] == 'success':
            self.agent_id = response['agent_id']
            return True
        return False
    
    def set_ingress_message_callback(self, message: str, callback: Callable):
        try:
            self.ingress_messages_callbacks[message].add(callback)
        except KeyError:
            self.ingress_messages_callbacks[message] = set([callback])


    def _start_receive_message_handler(self):
        """Start the message handler thread"""
        def message_handler_loop():
            while self._running:
                try:
                    # Receive multipart message
                    message_parts = self.message_socket.recv_multipart()
                    # Message format is [delimiter, message]
                    print(f"Received message parts: {message_parts}")
                    message_data = json.loads(message_parts[-1].decode())
                    self.logger.info(f"Received message: {message_data}")
                    
                    message_name = message_data.get('name')
                    if message_name in self.ingress_messages_callbacks:
                        for callback in self.ingress_messages_callbacks[message_name]:
                            callback(message_data.get('data'))
                            
                except Exception as e:
                    self.logger.error(f"Message handling error: {e}")
                    time.sleep(0.1)
        
        thread = threading.Thread(target=message_handler_loop)
        thread.daemon = True
        thread.start()
    
    def _start_heartbeat(self):
        """Send periodic heartbeats to orchestrator"""
        def heartbeat_loop():
            while self._running:
                print("Sending heartbeat")
                try:
                    self.registration_socket.send_json({
                        'action': 'heartbeat',
                        'agent_id': self.agent_id
                    })
                    self.registration_socket.recv_json()  # Wait for acknowledgment
                    time.sleep(10)  # Send heartbeat every 10 seconds
                except Exception as e:
                    self.logger.error(f"Heartbeat error: {e}")

        thread = threading.Thread(target=heartbeat_loop)
        thread.daemon = True
        thread.start()

    def on_receive_message(self, message_names: List[str]):
        """Decorator to register a method as a message handler.
        
        Args:
            message_name: The name of the message to handle
            
        Returns:
            Decorator function that registers the method as a handler
        """
        def decorator(func):
            print(f"Decorating {func.__name__} for messages {message_names} for agent {self.name}")
            self.set_ingress_message_callback((",").join(message_names), func)
            setattr(self, func.__name__, func)

        return decorator

    def emit_message(self, message_names: List[str]):
        """Decorator to register a method as a message handler."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                data = kwargs.get('data', args[0] if args else None)
                result = func(data)
                for message_name in message_names:
                    print(f"Emitting message {message_name} with data: {result}")
                    message = Message(name=message_name, data=result)
                    self.send_message(message)
            # Attach the wrapped function to the instance
            setattr(self, func.__name__, wrapper)
            return wrapper
        return decorator
    

    def send_message(self, message: Message) -> bool:
        """Send message to orchestrator"""
        try:
            message_data = json.dumps({
                'name': message.name,
                'data': message.data
            }).encode()
            
            # For DEALER socket, just send empty delimiter and message
            self.message_socket.send_multipart([
                b"",  # Empty delimiter
                message_data  # Message content
            ])
            return True
        except Exception as e:
            self.logger.error(f"Send error: {e}")
            return False
    


    def stop(self) -> None:
        """Stop the agent client"""
        with self._lock:
            if self._running:
                self._running = False
                # Unregister from orchestrator
                self.registration_socket.send_json({
                    'action': 'unregister',
                    'agent_id': self.agent_id
                })
                self.registration_socket.recv_json()  # Wait for acknowledgment
                
                # Close sockets
                self.message_socket.close()
                self.registration_socket.close()
                self.context.term() 