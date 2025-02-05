//Check if there's some match between the message and the dictionary of patterns
function checkPatternMatch(message, patternsDict){
    //goes through every pattern checking if there is a match
    // here I may better use a searching algorithm
    for (const [patternName, pattern] of Object.entries(patternsDict)){
        if(pattern.test(message)){
            const parts = message.match(pattern);
            return [parts,patternName,pattern];
        }
    }
    return [];
}

//Get answer for user querie
function getResponse(ws, name, number=null, dataToUpdate=null, message, callback){
    // transform object to JSON
    dataToSend = {
        message: message.body,
        phoneNumber: number,
        name: name
    };
    //Add data to update given if exists
    if(dataToUpdate){
        dataToSend['updateData'] = dataToUpdate
    }
    //transform data to json
    jsonDataToSend = JSON.stringify(dataToSend);
    //verify websocket is open to send and receive information
    if (ws.readyState === ws.OPEN) {
        //send data to python through websockets
        ws.send(jsonDataToSend);
    } 
    //response answer from python
    ws.once('message', async function incoming(data) {
        const response = data.toString();
        await callback(response);
    });
}



// Handle incoming messages
async function messageHandler(client, ws, pattern, patternsDict, message) {
    const chat = await message.getChat();
    const contact = await message.getContact();
    const name = contact.pushname || contact.verifiedName || 'No Name';
    const number = contact.number;

    //check if the message matches with some of the patterns for user functions
    const checkedPattern = checkPatternMatch(message.body, patternsDict);

    //console.log(message);

    // User queries for information
    if (message.body === '!me' || message.body === '!buy') {
        getResponse(ws, name, number, null, message, async (response) => {
            message.reply(response);
        });
    // user queries for download
    } else if (pattern.test(message.body)) {
        getResponse(ws, name, number, null, message, async (response) => {
            if(chat.isGroup){
                const privateChat = await contact.getChat();
                await client.sendMessage(privateChat.id._serialized, response);
            }else{
                message.reply(response);
            }
        });
    //admin functions or invalid messages
    } else if (checkedPattern.length !== 0 && !chat.isGroup) {
        if (checkedPattern[1] !== "updateFullUser") {
            const userUpdateValue = checkedPattern[0][1];
            const userId = checkedPattern[0][2];
            const dataToUpdate = [userUpdateValue, userId];
            getResponse(ws, name, number, dataToUpdate, message, async (response) => {
                message.reply(response);
            });
        }
    }
}

module.exports = {
    messageHandler
};