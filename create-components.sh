#!/bin/bash

# Define base path
BASE_DIR="react-frontend/src/components"

# Create directories
mkdir -p $BASE_DIR/Chat
mkdir -p $BASE_DIR/Layout
mkdir -p $BASE_DIR/Panels

# Chat components
touch $BASE_DIR/Chat/ChatInput.js
touch $BASE_DIR/Chat/ChatWindow.js
touch $BASE_DIR/Chat/Message.js

# Layout components
touch $BASE_DIR/Layout/SidePanel.js
touch $BASE_DIR/Layout/TickerSlider.js

# Panel components
touch $BASE_DIR/Panels/IpoPanel.js
touch $BASE_DIR/Panels/MarketMovers.js
touch $BASE_DIR/Panels/NewsPanel.js

echo "All empty JavaScript component files have been created inside react-frontend/src/components/"
