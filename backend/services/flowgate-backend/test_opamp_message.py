#!/usr/bin/env python3
"""Test OpAMP message parsing with known-good messages"""

import sys
import json
from app.protobufs import opamp_pb2

def test_minimal_message():
    """Test with a minimal valid AgentToServer message"""
    print("=== Test 1: Minimal AgentToServer Message ===")
    
    # Create a minimal message
    msg = opamp_pb2.AgentToServer()
    msg.instance_uid = b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10'
    msg.sequence_num = 1
    msg.capabilities = 0x4805  # ReportsStatus + ReportsEffectiveConfig + ReportsHealth + ReportsAvailableComponents
    
    # Serialize
    data = msg.SerializeToString()
    print(f"Serialized message: {len(data)} bytes")
    print(f"Hex: {data.hex()}")
    
    # Try to parse it back
    try:
        parsed = opamp_pb2.AgentToServer()
        parsed.ParseFromString(data)
        print(f"✓ Successfully parsed back")
        print(f"  instance_uid: {parsed.instance_uid.hex()}")
        print(f"  sequence_num: {parsed.sequence_num}")
        print(f"  capabilities: 0x{parsed.capabilities:X}")
        return True
    except Exception as e:
        print(f"✗ Failed to parse: {e}")
        return False

def test_parse_actual_message(hex_data):
    """Test parsing an actual message from logs"""
    print(f"\n=== Test 2: Parse Actual Message from Logs ===")
    print(f"Hex data: {hex_data[:100]}...")
    
    try:
        data = bytes.fromhex(hex_data)
        print(f"Message size: {len(data)} bytes")
        
        # Try Python parser
        msg = opamp_pb2.AgentToServer()
        msg.ParseFromString(data)
        print(f"✓ Python parser succeeded")
        print(f"  instance_uid: {msg.instance_uid.hex() if msg.instance_uid else 'None'}")
        print(f"  sequence_num: {msg.sequence_num}")
        print(f"  capabilities: 0x{msg.capabilities:X}")
        return True
    except Exception as e:
        print(f"✗ Python parser failed: {e}")
        
        # Try to manually parse wire format
        print("\nAttempting manual wire format parsing...")
        try:
            pos = 0
            while pos < len(data) and pos < 50:
                tag = data[pos]
                field_num = tag >> 3
                wire_type = tag & 0x07
                pos += 1
                print(f"  Field {field_num}, wire type {wire_type} at position {pos-1}")
                
                if wire_type == 0:  # Varint
                    val = 0
                    shift = 0
                    while pos < len(data):
                        byte = data[pos]
                        pos += 1
                        val |= (byte & 0x7F) << shift
                        if not (byte & 0x80):
                            break
                        shift += 7
                    print(f"    Varint value: {val}")
                elif wire_type == 2:  # Length-delimited
                    length = 0
                    shift = 0
                    while pos < len(data):
                        byte = data[pos]
                        pos += 1
                        length |= (byte & 0x7F) << shift
                        if not (byte & 0x80):
                            break
                        shift += 7
                    if pos + length <= len(data):
                        value = data[pos:pos+length]
                        print(f"    Length-delimited: {length} bytes, value: {value.hex()[:40]}...")
                        pos += length
                    else:
                        break
                else:
                    break
        except Exception as e2:
            print(f"  Manual parsing also failed: {e2}")
        
        return False

def test_go_parser_compatibility():
    """Test if Go parser can parse Python-generated messages"""
    print(f"\n=== Test 3: Go Parser Compatibility ===")
    
    # Create a message in Python
    msg = opamp_pb2.AgentToServer()
    msg.instance_uid = b'\x01' * 16
    msg.sequence_num = 1
    msg.capabilities = 0x4805
    
    data = msg.SerializeToString()
    print(f"Python-generated message: {len(data)} bytes")
    
    # Try Go parser
    try:
        from app.services.opamp_go_parser import get_go_parser
        parser = get_go_parser()
        if parser:
            result = parser.parse_agent_message(data)
            if result:
                print(f"✓ Go parser succeeded")
                print(f"  Result: {json.dumps(result, indent=2, default=str)}")
                return True
            else:
                print(f"✗ Go parser returned None")
        else:
            print(f"✗ Go parser not available")
    except Exception as e:
        print(f"✗ Go parser failed: {e}")
    
    return False

if __name__ == "__main__":
    print("OpAMP Message Parsing Tests\n")
    
    # Test 1: Minimal message
    test1 = test_minimal_message()
    
    # Test 2: Actual message from logs (if provided)
    if len(sys.argv) > 1:
        test2 = test_parse_actual_message(sys.argv[1])
    else:
        # Use a sample from logs
        sample_hex = "000a10019a86892e6d7d2089ffe01046135f26101220e7fb01"
        test2 = test_parse_actual_message(sample_hex)
    
    # Test 3: Go parser compatibility
    test3 = test_go_parser_compatibility()
    
    print(f"\n=== Summary ===")
    print(f"Test 1 (Minimal): {'✓' if test1 else '✗'}")
    print(f"Test 2 (Actual): {'✓' if test2 else '✗'}")
    print(f"Test 3 (Go Parser): {'✓' if test3 else '✗'}")

