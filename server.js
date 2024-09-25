const express = require('express');
const path = require('path');

const PORT = process.env.PORT || 3000;
const app = express();

// Serve static files from the "public" directory
app.use(express.static(path.join(__dirname)));

// Set up routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'MicrometryManual','index.html'));
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}/`);
});

