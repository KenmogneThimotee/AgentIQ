from copy import deepcopy
import time
from uuid import uuid4
from src.helpers.agents import NotificationType
from src.helpers.orchestrator import Message
from src.mixins.agent_mixin import AgentMixin
from src.mixins.input_mixin import InputMixin
from src.mixins.processor import ProcessorMixin
from typing import Any, Union, Tuple, Dict, Optional, List
from hashlib import sha256
from collections import deque, defaultdict
from zmq import Context, Socket, ROUTER, REP
import zmq
import json
import threading
from dataclasses import dataclass
import logging

@dataclass
class RemoteAgent:
    name: str
    id: str
    address: str
    subscriptions: list
    last_heartbeat: float
    status: str = "ACTIVE"

class ExecutionGraphNode:
    id: str
    children: Optional[List[str]]
    parents: Optional[List[str]]


class OrchestratorMixin:

    agents: Dict[str, AgentMixin]
    message_queue: Dict[str, List]

    def __init__(self, name: str, message_port: int = 5555, registration_port: int = 5556):
        self.name = name
        self.message_port = message_port
        self.registration_port = registration_port
        self.remote_agents: Dict[str, RemoteAgent] = {}
        self._running = False
        self._lock = threading.Lock()
        self.logger = logging.getLogger("Orchestrator")
        self.message_queue = defaultdict(list)

    def start(self) -> None:
        """Start the orchestrator service"""
        with self._lock:
            if not self._running:
                # Initialize ZMQ context
                self.context = Context()
                
                # Socket for message handling
                self.message_socket = self.context.socket(ROUTER)
                self.message_socket.bind(f"tcp://127.0.0.1:{self.message_port}")
                
                # Socket for agent registration
                self.registration_socket = self.context.socket(REP)
                self.registration_socket.bind(f"tcp://127.0.0.1:{self.registration_port}")
                
                self._running = True
                
                # Start message and registration handling threads
                self._start_receive_message_handler()
                self._start_registration_handler()
                self._start_heartbeat_monitor()
                
                self.logger.info(f"Orchestrator started on ports {self.message_port} (messages) and {self.registration_port} (registration)")
    
    def _start_receive_message_handler(self):
        """Start the receive message handler in a separate thread"""
        def message_loop():
            while self._running:
                try:
                    print("Waiting for message")
                    message_parts = self.message_socket.recv_multipart()
                    print(f"Received message parts: {message_parts}")
                    
                    # ROUTER socket format: [identity, empty delimiter, message content]
                    agent_id = message_parts[0].decode()  # ZMQ automatically adds the identity
                    message_data = json.loads(message_parts[2].decode())
                    
                    self.logger.info(f"Received message from {agent_id}: {message_data}")
                    
                    if agent_id not in self.remote_agents:
                        self.logger.warning(f"Received message from unregistered agent: {agent_id}")
                        continue
                        
                    # Get subscribers for this message type
                    message_name = message_data.get('name')
                    agent_ids = self.message_queue[message_name]
                    
                    # Forward message to subscribers
                    for subscriber_id in agent_ids:
                        agent = self.remote_agents[subscriber_id]
                        self.message_socket.send_multipart([
                            subscriber_id.encode(),
                            b"",
                            message_parts[2]  # Original message content
                        ])
                        
                except Exception as e:
                    self.logger.error(f"Message handling error: {e}")
                    time.sleep(0.1)

        thread = threading.Thread(target=message_loop)
        thread.daemon = True
        thread.start()

    def _start_registration_handler(self):
        """Handle agent registration requests"""
        def registration_loop():
            while self._running:
                try:
                    # Wait for registration request
                    request = self.registration_socket.recv_json()
                    self.logger.info(f"Received registration request: {request}")
                    if request['action'] == 'register':
                        agent_id = self._register_remote_agent(
                            name=request['name'],
                            address=request['address'],
                            subscriptions=request['subscriptions']
                        )
                        # Send back the agent_id
                        self.registration_socket.send_json({
                            'status': 'success',
                            'agent_id': agent_id
                        })
                        
                    elif request['action'] == 'unregister':
                        success = self._unregister_remote_agent(request['agent_id'])
                        self.registration_socket.send_json({
                            'status': 'success' if success else 'failed'
                        })
                        
                    elif request['action'] == 'heartbeat':
                        self._update_agent_heartbeat(request['agent_id'])
                        self.registration_socket.send_json({'status': 'success'})
                        
                except Exception as e:
                    self.logger.error(f"Registration error: {e}")
                    try:
                        self.registration_socket.send_json({'status': 'error', 'message': str(e)})
                    except:
                        pass

        thread = threading.Thread(target=registration_loop)
        thread.daemon = True
        thread.start()

    def _unregister_remote_agent(self, agent_id: str) -> bool:
        """Unregister a remote agent"""
        with self._lock:
            if agent_id in self.remote_agents:
                del self.remote_agents[agent_id]
                return True
            return False

    def _update_agent_heartbeat(self, agent_id: str):
        """Update the heartbeat timestamp for an agent"""
        with self._lock:
            self.remote_agents[agent_id].last_heartbeat = time.time()

    def _start_heartbeat_monitor(self):
        """Monitor agent heartbeats and mark inactive agents"""
        def monitor_loop():
            while self._running:
                current_time = time.time()
                with self._lock:
                    for agent_id, agent in self.remote_agents.items():
                        if current_time - agent.last_heartbeat > 30:  # 30 seconds timeout
                            agent.status = "INACTIVE"
                time.sleep(5)

        thread = threading.Thread(target=monitor_loop)
        thread.daemon = True
        thread.start()

    def _register_remote_agent(self, name: str, address: str, subscriptions: list) -> str:
        """Register a new remote agent"""
        agent_id = sha256(f"{name}:{address}".encode()).hexdigest()
        
        with self._lock:
            self.remote_agents[agent_id] = RemoteAgent(
                name=name,
                id=agent_id,
                address=address,
                subscriptions=subscriptions,
                last_heartbeat=time.time()
            )

            for subscription in subscriptions:
                self.message_queue[subscription].append(agent_id)
        
        self.logger.info(f"Registered new agent: {name} ({agent_id})")
        return agent_id

    def broadcast_message(self, message: Message) -> None:
        """Broadcast message to all active agents"""
        # Convert message to proper format
        message_data = {
            'name': message.name,
            'data': message.data
        }
        encoded_message = json.dumps(message_data).encode()
        
        self.logger.info(f"Broadcasting message: {message_data}")
        with self._lock:
            for agent_id, agent in self.remote_agents.items():
                if agent.status == "ACTIVE" and message.name in agent.subscriptions:
                    self.logger.info(f"Sending message to agent {agent_id}")
                    self.message_socket.send_multipart([
                        agent_id.encode(),
                        b"",
                        encoded_message
                    ])

    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of specific agent"""
        with self._lock:
            if agent_id not in self.remote_agents:
                return {"error": "Agent not found"}
            agent = self.remote_agents[agent_id]
            return {
                "name": agent.name,
                "id": agent.id,
                "address": agent.address,
                "status": agent.status,
                "subscriptions": agent.subscriptions,
                "last_heartbeat": agent.last_heartbeat
            }
