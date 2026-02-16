import asyncio
import websockets
import json

async def test_streaming():
    uri = "ws://localhost:8000/ws/omni"
    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")
        
        # Simulate text input
        msg = {
            "type": "text_input",
            "text": "Calculate 25 * 4 using python code"
        }
        await websocket.send(json.dumps(msg))
        print(f"Sent: {msg}")
        
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                
                if data['type'] == 'agent_token':
                    print(f"Token: {repr(data['text'])}")
                elif data['type'] == 'agent_response_end':
                    print("Stream finished.")
                    break
                else:
                    print(f"Message: {data['type']}")
                    
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break

if __name__ == "__main__":
    asyncio.run(test_streaming())
