#import re
import json
import asyncio
import logging
import websockets
#import mysql.connector
from messageHandler import MessageHandler

mHandler = MessageHandler()

async def handle_client(websocket, path):
    try:
        async for message in websocket:
            #print(f"Received message from client: {message}")
            try:
                # Define a regex pattern to match numeric characters before the '@' 
                # symbol for phone number
                pattern = r'(\d+)(?=@)'
                #extract the json with message and the complete user data
                message_data = json.loads(message)
                #retrieve the message
                incoming_message = message_data.get("message")
                #get the user number extracting the first matched pattern
                from_number = message_data.get("phoneNumber") 
                #re.search(pattern, message_data.get("phoneNumber")).group(1)
                #Get the user nickname
                profile_name = message_data.get("name")
                print('a')
                logging.info('a')
                response_message = mHandler.process_message(
                    incoming_message, 
                    from_number, 
                    profile_name
                )
            except json.JSONDecodeError:
                #print("Error: Mensaje no es un JSON válido")
                response_message = "Ha ocurrido un error desconocido. Por favor intentelo de nuevo más tarde."
                continue
            except Exception as e:
                response_message = "Ha ocurrido un error desconocido. Por favor intentelo de nuevo más tarde."
            await websocket.send(response_message)
            
    except websockets.exceptions.ConnectionClosedError:
        logging.error("Failed websocket connection")

def start_websocket_server():
    start_server = websockets.serve(handle_client, "0.0.0.0", 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()