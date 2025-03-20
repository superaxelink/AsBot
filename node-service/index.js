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

//////////////////////////
// Variable para almacenar el ID del bot
let botId = null;
let cooldowns = new Map();
const cooldownTime = 5000; // 5 segundos de espera entre respuestas 
const DEBUG_MODE = true; // Activa o desactiva el modo debug
/////////////////////////

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

        ////////////////////
        // Obtener el ID del bot
        botId = client.info.wid._serialized;
        console.log(`ID bot: ${botId}`);
        /////////////////////
    });

    client.on('message_create', async (message) => {

        /////////////////////////
        const senderId = message.from;

        console.log(senderId)
        console.log(botId)

        const now = Date.now();
        const lastMessageTime = cooldowns.get(message.from) || 0;

        console.log(`Tiempos`);
        console.log(now);
        console.log(lastMessageTime);
        console.log(cooldownTime);


        if (now - lastMessageTime < cooldownTime) {
            console.log(`Mensaje ignorado de ${message.from} para evitar spam.`);
            return; // Ignorar mensajes si están dentro del tiempo de cooldown
        }

        cooldowns.set(message.from, now);

        // Ignorar mensajes enviados por el bot
        if (!DEBUG_MODE && senderId === botId) {
            console.log("Mensaje ignorado: proviene del bot.");
            return;
        }
        ////////////////////////

        console.log(message.body);
        console.log("its from me")
        console.log(!message.fromMe)
        console.log("Goes to me")
        console.log(!message.to === botId)

        //////////////////////////////
        //if (DEBUG_MODE && !message.fromMe && message.to !== botId) {
        if (DEBUG_MODE && (message.from !== botId || message.to !== botId)) {
            console.log("Mensaje ignorado para no molestar");
            return;
        }

        await messageHandler(client, ws, pattern, patternsDict, message);
    });

    await client.initialize(); 
}

// Run the initialization
initializeClient().catch(error => {
    console.error(`Initialization failed: ${error.message}`);
});
