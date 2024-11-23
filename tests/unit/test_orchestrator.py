from collections import defaultdict
import pytest
import zmq
import json
import time
from unittest.mock import Mock, patch, MagicMock
from src.orchestrator import Orchestrator, RemoteAgent
from src.helpers.orchestrator import Message

@pytest.fixture
def mock_context():
    with patch('zmq.Context') as mock:
        yield mock

@pytest.fixture
def mock_sockets():
    with patch('zmq.Socket') as mock:
        yield mock

@pytest.fixture
def orchestrator():
    return Orchestrator("test_orchestrator")

def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initialization"""
    assert orchestrator.name == "test_orchestrator"
    assert orchestrator.message_port == 5555
    assert orchestrator.registration_port == 5556
    assert orchestrator._running is False
    assert isinstance(orchestrator.remote_agents, dict)
    assert isinstance(orchestrator.message_queue, defaultdict)

def test_start_orchestrator(orchestrator, mock_context):
    """Test starting the orchestrator"""
    # Mock the sockets
    mock_router = MagicMock()
    mock_rep = MagicMock()
    mock_context.return_value.socket.side_effect = [mock_router, mock_rep]
    
    orchestrator.start()
    
    assert orchestrator._running is True
    assert mock_router.bind.called
    assert mock_rep.bind.called

def test_register_remote_agent(orchestrator):
    """Test registering a remote agent"""
    name = "test_agent"
    address = "localhost:5555"
    subscriptions = ["test_message"]
    
    agent_id = orchestrator._register_remote_agent(name, address, subscriptions)
    
    assert agent_id in orchestrator.remote_agents
    assert orchestrator.remote_agents[agent_id].name == name
    assert orchestrator.remote_agents[agent_id].address == address
    assert orchestrator.remote_agents[agent_id].subscriptions == subscriptions
    assert orchestrator.message_queue["test_message"] == [agent_id]

def test_unregister_remote_agent(orchestrator):
    """Test unregistering a remote agent"""
    # First register an agent
    agent_id = orchestrator._register_remote_agent("test_agent", "localhost:5555", ["test_message"])
    
    # Then unregister it
    success = orchestrator._unregister_remote_agent(agent_id)
    
    assert success is True
    assert agent_id not in orchestrator.remote_agents

def test_update_agent_heartbeat(orchestrator):
    """Test updating agent heartbeat"""
    # Register an agent first
    agent_id = orchestrator._register_remote_agent("test_agent", "localhost:5555", ["test_message"])
    initial_heartbeat = orchestrator.remote_agents[agent_id].last_heartbeat
    
    # Wait a bit and update heartbeat
    time.sleep(0.1)
    orchestrator._update_agent_heartbeat(agent_id)
    
    assert orchestrator.remote_agents[agent_id].last_heartbeat > initial_heartbeat

def test_heartbeat_monitor(orchestrator):
    """Test heartbeat monitoring"""
    # Register an agent
    agent_id = orchestrator._register_remote_agent("test_agent", "localhost:5555", ["test_message"])
    
    # Manually set an old heartbeat
    orchestrator.remote_agents[agent_id].last_heartbeat = time.time() - 31
    
    # Start heartbeat monitor
    orchestrator._running = True
    orchestrator._start_heartbeat_monitor()
    
    # Wait for monitor to run
    time.sleep(6)
    
    assert orchestrator.remote_agents[agent_id].status == "INACTIVE"

@pytest.mark.asyncio
async def test_registration_handler(orchestrator):
    """Test registration handler"""
    orchestrator._running = True
    orchestrator.registration_socket = MagicMock()
    
    # Mock registration request
    request = {
        'action': 'register',
        'name': 'test_agent',
        'address': 'localhost:5555',
        'subscriptions': ['test_message']
    }
    orchestrator.registration_socket.recv_json.return_value = request
    
    # Start registration handler
    orchestrator._start_registration_handler()
    
    # Wait for handler to process
    time.sleep(0.1)
    
    # Verify response was sent
    orchestrator.registration_socket.send_json.assert_called()

def test_broadcast_message(orchestrator):
    """Test broadcasting messages"""
    # Register an agent
    agent_id = orchestrator._register_remote_agent("test_agent", "localhost:5555", ["test_message"])
    
    # Mock message socket
    orchestrator.message_socket = MagicMock()
    
    # Create and broadcast message
    message = Message(name="test_message", data={"test": "data"})
    orchestrator.broadcast_message(message)
    
    # Verify message was sent
    orchestrator.message_socket.send_multipart.assert_called_once()

def test_get_agent_status(orchestrator):
    """Test getting agent status"""
    # Register an agent
    agent_id = orchestrator._register_remote_agent("test_agent", "localhost:5555", ["test_message"])
    
    # Get status
    status = orchestrator.get_agent_status(agent_id)
    
    assert status["name"] == "test_agent"
    assert status["address"] == "localhost:5555"
    assert status["status"] == "ACTIVE"
    assert status["subscriptions"] == ["test_message"]

def test_get_nonexistent_agent_status(orchestrator):
    """Test getting status of non-existent agent"""
    status = orchestrator.get_agent_status("nonexistent_id")
    assert status == {"error": "Agent not found"}

def test_message_handling(orchestrator):
    """Test message handling"""
    # Register an agent
    agent_id = orchestrator._register_remote_agent("test_agent", "localhost:5555", ["test_message"])
    
    # Mock message socket
    orchestrator.message_socket = MagicMock()
    orchestrator._running = True
    
    # Mock receiving a message
    message_data = {
        'name': 'test_message',
        'data': {"test": "data"}
    }
    orchestrator.message_socket.recv_multipart.return_value = [
        agent_id.encode(),
        b"",
        json.dumps(message_data).encode()
    ]
    
    # Start message handler
    orchestrator._start_receive_message_handler()
    
    # Wait for handler to process
    time.sleep(0.1)
    
    # Verify message was forwarded
    orchestrator.message_socket.send_multipart.assert_called() 