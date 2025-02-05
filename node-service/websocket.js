//get whatsapp-web.js object
const WebSocket = require('ws');
//async function to get the connection to websockets, retrying if there's an error connectiong
async function connectWebSocket(url, retryInterval = 5000) {
//return the promise only when we get the connection
    return new Promise((resolve, reject) => {
        const attemptConnection = () => {

            //initialize websocket object.
            const ws = new WebSocket(url);
            //when the connection is open resolve the promise
            ws.on('open', () => {
                console.log('WebSocket connection established');
                resolve(ws);
            });
            //otherwise wait milisecond stablished in retryInterval and try again
            ws.on('error', (err) => {
                console.log(`WebSocket connection failed: ${err.message}`);
                setTimeout(attemptConnection, retryInterval);
            });
            // If connection is closed inform it.
            ws.on('close', () => {
                console.log('WebSocket connection closed');
            });
        };

        attemptConnection();
    });
}
//export module functino
module.exports = {
    connectWebSocket
};
