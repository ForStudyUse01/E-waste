const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ port: 3000 });

// Serve static files
app.use(express.static(path.join(__dirname, 'static')));

// Store connected clients
const clients = new Set();

console.log('WebSocket server starting on port 3000...');

// WebSocket connection handler
wss.on('connection', (ws) => {
    console.log('New client connected');
    clients.add(ws);

    // Send initial state
    ws.send(JSON.stringify({
        type: 'modelUpdate',
        deviceType: 'placeholder'
    }));

    // Handle incoming messages
    ws.on('message', (message) => {
        try {
            // Broadcast to all clients
            wss.clients.forEach((client) => {
                if (client !== ws && client.readyState === WebSocket.OPEN) {
                    client.send(message);
                }
            });
        } catch (error) {
            console.error('Error processing message:', error);
        }
    });

    // Handle client disconnection
    ws.on('close', () => {
        console.log('Client disconnected');
        clients.delete(ws);
    });

    // Handle errors
    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        clients.delete(ws);
    });
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', connections: clients.size });
});

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`WebSocket server running on port ${PORT}`);
}); 