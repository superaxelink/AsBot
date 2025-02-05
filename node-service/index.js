const { Client, LocalAuth } = require('whatsapp-web.js');
//const qrcode = require('qrcode-terminal');
const QRCode = require('qrcode');
const qrcode = require('qrcode-terminal');
//const express = require('express');
//const fs = require('fs');
const path = require('path');
//const { userInfo } = require('os');
const { appendFileSync, existsSync, statSync, renameSync } = require('fs');
const { connectWebSocket } = require('./websocket');
const { messageHandler } = require('./messageHandler');

// Tamaño máximo del archivo de log en bytes (5 MB)
const maxLogSize = 5 * 1024 * 1024;
//const app = express();
//const port = 3000;

// Define the WebSocket URL and optional retry interval
const websocketUrl = 'ws://python-service:8765';
const retryInterval = 5000;

let qrCodeData = null;
// Define pattern as a regular expression
const pattern = /^(https:\/\/)?(www\.)?(elements\.)?(freepik|envato)\.(com|es)(\/.*)?$/
//const patternUpdateCredits = /^!updateCredits( .*)?$/;
const patternsDict = {
    updateId: /^!updateId (\d+) (\d+)$/,
    updateNickname: /^!updateNickname (\d+) (\w+)$/,
    updateCreditos: /^!updateCreditos (\d+) ([0-9]{1,6})$/,
    updateRol: /^!updateRol (\d+) (\w+)$/,
    updatePlan: /^!updatePlan (\d+) (\w+)$/,
    updateSoporte: /^!updateSoporte (\d+) (\w+)$/,
    updateAntiSpamTimeout: /^!updateAntiSpamTimeout (\d+) (\d+)$/,
    //updateFullUser: /^!updateFullUser (\d+) (\w+) ([0-9]{1,6}) (\w+) (\w+) (\w+) (\d+)$/
};

// Verifies and rotates a logfile
//NOT CURRENTLY USED BUT IT MAY BE A GOOD IDEA
const rotateLogFile = (logFilePath) => {
    if (existsSync(logFilePath)) {
        const stats = statSync(logFilePath);
        if (stats.size >= maxLogSize) {
            const timestamp = new Date().toISOString().replace(/:/g, '-');
            const newLogFilePath = `${logFilePath}.${timestamp}`;
            renameSync(logFilePath, newLogFilePath);
        }
    }
};

//Initialze whatsapp-webs.js client, waiting for the websocket connection to be ready before proceeding
async function initializeClient() {
    //Here we wait for the websocket connection to be ready
    const ws = await connectWebSocket(websocketUrl, retryInterval);
    // after that we initialize the whatsapp-web.js client
    const client = new Client({
        webVersionCache: {type:'none'},
        authStrategy: new LocalAuth(),
        restartOnAuthFail: true,
        puppeteer: {
            headless: true,
            args: ['--no-sandbox', '--disable-gpu'],
        }
    });

    // We respond according to the expected event
    client.on('qr', (qr) => {
        qrcode.generate(qr, { small: true });
    });

    client.on('ready', () => {
        console.log('Client is ready!');
    });

    client.on('message_create', async (message) => {
        await messageHandler(client, ws, pattern, patternsDict, message);
    });

    await client.initialize(); 
}

// Run the initialization
initializeClient().catch(error => {
    console.error(`Initialization failed: ${error.message}`);
});
