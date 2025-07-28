#!/bin/bash

# Navigate to project root
mkdir -p react-frontend/src/components/Chat
mkdir -p react-frontend/src/components/Layout
mkdir -p react-frontend/src/components/Panels

# Create files inside Chat
touch react-frontend/src/components/Chat/ChatInput.js
touch react-frontend/src/components/Chat/ChatWindow.js
touch react-frontend/src/components/Chat/Message.js

# Create files inside Layout
touch react-frontend/src/components/Layout/SidePanel.js
touch react-frontend/src/components/Layout/TickerSlider.js

# Create files inside Panels
touch react-frontend/src/components/Panels/IpoPanel.js
touch react-frontend/src/components/Panels/MarketMovers.js
touch react-frontend/src/components/Panels/NewsPanel.js

# Create root-level files
touch react-frontend/src/App.css
touch react-frontend/src/App.js
touch react-frontend/src/index.js

echo "Folder structure and files created successfully!"
