import pytest
import zmq
import json
import time
from unittest.mock import Mock, patch, MagicMock
from src.agent_client import AgentClient
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
def agent_client():
    return AgentClient("test_agent", "localhost")

def test_agent_initialization(agent_client):
    """Test agent client initialization"""
    assert agent_client.name == "test_agent"
    assert agent_client.orchestrator_host == "localhost"
    assert agent_client.message_port == 5555
    assert agent_client.registration_port == 5556
    assert agent_client.agent_id is None
    assert agent_client._running is False

@pytest.mark.asyncio
async def test_registration_success(agent_client, mock_context):
    """Test successful agent registration"""
    # Mock the registration socket
    mock_reg_socket = MagicMock()
    mock_reg_socket.recv_json.return_value = {
        'status': 'success',
        'agent_id': 'test_id_123'
    }
    
    # Mock the message socket
    mock_msg_socket = MagicMock()
    
    # Setup context mock
    mock_context.return_value.socket.side_effect = [mock_reg_socket, mock_msg_socket]
    
    # Start the agent
    success = agent_client.start()
    
    assert success is True
    assert agent_client.agent_id == 'test_id_123'
    assert agent_client._running is True

def test_message_callback_registration(agent_client):
    """Test registering message callbacks"""
    @agent_client.on_receive_message(["test_message"])
    def handle_test(data):
        return data
    
    assert "test_message" in agent_client.ingress_messages_callbacks
    assert len(agent_client.ingress_messages_callbacks["test_message"]) == 1

def test_send_message(agent_client):
    """Test sending messages"""
    # Mock the message socket
    agent_client.message_socket = MagicMock()
    agent_client._running = True
    
    # Create and send a test message
    message = Message(name="test_message", data={"test": "data"})
    success = agent_client.send_message(message)
    
    assert success is True
    agent_client.message_socket.send_multipart.assert_called_once()

def test_receive_message(agent_client):
    """Test receiving messages"""
    # Mock the message socket
    agent_client.message_socket = MagicMock()
    agent_client._running = True
    
    # Setup mock callback
    callback_called = False
    def test_callback(data):
        nonlocal callback_called
        callback_called = True
        assert data == {"test": "data"}
    
    # Register callback
    agent_client.set_ingress_message_callback("test_message", test_callback)
    
    # Simulate receiving a message
    message_data = {
        'name': 'test_message',
        'data': {"test": "data"}
    }
    agent_client.message_socket.recv_multipart.return_value = [
        b"",
        json.dumps(message_data).encode()
    ]
    
    # Start message handler and wait briefly
    agent_client._start_receive_message_handler()
    time.sleep(0.1)
    
    assert callback_called is True

def test_heartbeat(agent_client):
    """Test heartbeat mechanism"""
    # Mock the registration socket
    agent_client.registration_socket = MagicMock()
    agent_client._running = True
    agent_client.agent_id = "test_id_123"
    
    # Start heartbeat and wait briefly
    agent_client._start_heartbeat()
    time.sleep(0.1)
    
    # Verify heartbeat was sent
    agent_client.registration_socket.send_json.assert_called_with({
        'action': 'heartbeat',
        'agent_id': 'test_id_123'
    })

def test_stop(agent_client):
    """Test stopping the agent"""
    # Mock sockets
    agent_client.registration_socket = MagicMock()
    agent_client.message_socket = MagicMock()
    agent_client.context = MagicMock()
    agent_client._running = True
    agent_client.agent_id = "test_id_123"
    
    # Stop the agent
    agent_client.stop()
    
    assert agent_client._running is False
    agent_client.registration_socket.send_json.assert_called_with({
        'action': 'unregister',
        'agent_id': 'test_id_123'
    })
    agent_client.message_socket.close.assert_called_once()
    agent_client.registration_socket.close.assert_called_once()
    agent_client.context.term.assert_called_once()

def test_emit_message_decorator(agent_client):
    """Test emit message decorator"""
    agent_client.send_message = MagicMock()
    
    @agent_client.emit_message(["response_message"])
    def process_data(data):
        return {"processed": data}
    
    # Call the decorated function
    process_data({"input": "test"})
    
    # Verify message was sent
    agent_client.send_message.assert_called_with(
        Message(name="response_message", data={"processed": {"input": "test"}})
    ) 