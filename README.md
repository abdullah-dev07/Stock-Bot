# StockBot: AI-Powered Financial Assistant

StockBot is a full-stack web application that acts as an AI-powered financial assistant. It provides users with real-time stock data, market news, and intelligent analysis through a conversational chat interface. The application leverages a Python FastAPI backend for robust API services and a React frontend for a dynamic user experience, with Google's Gemini API powering its core AI capabilities.

---

##  Features

* **Conversational AI Chat:** Interact with an intelligent chatbot to get financial information in a natural way.
* **Real-time Stock Quotes:** Fetch up-to-the-minute stock prices and key metrics for any ticker symbol.
* **Dynamic Intent Recognition:** The AI can understand user intent, whether they're asking for specific data, qualitative analysis, or general knowledge.
* **Ticker Clarification:** If a company name has multiple possible stock tickers, the bot asks for clarification.
* **Market Overview:** Access curated lists of top market movers (gainers and losers), the latest financial news, and upcoming IPOs.
* **Secure User Authentication:** User registration and login system to provide a personalized experience.
* **Efficient Caching:** The backend caches API responses for market data to ensure fast response times and minimize redundant API calls.

---

## Architecture

The project is built with a modern web stack, separating the backend API from the frontend client for scalability and maintainability.

* **Backend:**
    * **Framework:** **FastAPI** - A high-performance Python web framework for building APIs.
    * **AI Engine:** **Google Gemini API** (Gemini 2.5 Pro & Flash) - Used for intent recognition, natural language understanding, and generating grounded, intelligent responses.
    * **Financial Data:** **Alpha Vantage API** - Used as the primary source for real-time and historical stock data, market news, and IPO calendars.
    * **Authentication:** **Firebase Authentication** - Manages user sign-up, login, and secure session handling.

* **Frontend:**
    * **Library:** **React** - A popular JavaScript library for building user interfaces.
    * **Build Tool:** **Vite** - A next-generation frontend tool that provides an extremely fast development experience.
    * **Routing:** **React Router** - For handling client-side page navigation.
    * **Styling:** Custom CSS for a clean and responsive chat interface.

---

## Getting Started

Follow these instructions to get a local copy of the project up and running for development and testing purposes.

### Prerequisites

Ensure you have the following installed on your local machine:
* [Python 3.8+](https://www.python.org/downloads/)
* [Node.js and npm](https://nodejs.org/en/)
* A code editor like [VS Code](https://code.visualstudio.com/)

### API Keys

Before you begin, you will need to obtain API keys from the following services:
* **Google AI Studio:** For your `GEMINI_API_KEY`.
* **Alpha Vantage:** For your `ALPHA_VANTAGE_API_KEY`.
* **Firebase:** Create a new project and get your web app's configuration credentials.

### Backend Setup

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/abdullah-dev07/Stock-Bot](https://github.com/abdullah-dev07/Stock-Bot)
    cd stockbot
    ```

2.  **Create a Virtual Environment:**
    (Assuming the virtual environment is in the project root)
    ```bash
    python -m venv stockbot_env
    source stockbot_env/bin/activate  # On Windows, use `stockbot_env\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r backend/requirements.txt
    ```

4.  **Create an Environment File:**
    Create a file named `.env` in the `backend` directory and add your API keys and Firebase configuration.

    **.env**
    ```env
    # Gemini API Key
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

    # Alpha Vantage API Key
    ALPHA_VANTAGE_API_KEY="YOUR_ALPHA_VANTAGE_API_KEY"

    # Firebase Configuration (as a JSON string)
    FIREBASE_CONFIG='{"apiKey": "AIza...", "authDomain": "...", "projectId": "...", "storageBucket": "...", "messagingSenderId": "...", "appId": "..."}'
    ```

### 🖥️ Frontend Setup (Vite)

1.  **Navigate to the Frontend Directory:**
    ```bash
    cd react-frontend
    ```

2.  **Install Dependencies:**
    ```bash
    npm install
    ```
    This will install React, Vite, and other necessary packages listed in `package.json`.

3.  **File Structure Note:**
    Vite requires files containing JSX to use the `.jsx` extension. Ensure all your component files (e.g., `App.js`, `ChatWindow.js`) have been renamed to `.jsx`. Also, ensure your `index.html` points to `/src/index.jsx`.

### ⚡ Running Both Servers Concurrently

The best way to run the project is to use the custom script that starts both the backend and frontend servers with a single command.

1.  **Navigate to the Frontend Directory:**
    ```bash
    cd react-frontend
    ```

2.  **Run the Full-Stack Command:**
    ```bash
    npm run dev:fullstack
    ```
    This command uses `concurrently` to launch both the FastAPI backend (running on `http://localhost:8000`) and the Vite frontend (running on `http://localhost:5173`).

---

## ↔️ API Endpoints

The FastAPI backend provides the following key endpoints:

* `POST /register`: Creates a new user account.
* `POST /token`: Authenticates a user and provides a JWT token.
* `GET /users/me`: Retrieves the current authenticated user's data.
* `POST /chat`: The main endpoint for interacting with the chatbot. It handles both streaming and JSON responses.
* `GET /ticker-data`: Gets cached price data for a predefined list of major stocks.
* `GET /market-movers`: Gets the day's top gainers and losers.
* `GET /market-news`: Gets the latest financial news.
* `GET /ipo-calendar`: Gets a list of recent and upcoming IPOs.

---

## 🔮 Future Improvements

* **Real-time Data Dashboard:** Create a separate dashboard page to visualize the market data fetched from the API endpoints.
* **User Watchlists:** Allow authenticated users to create and save their own personal stock watchlists.
* **Advanced Charting:** Integrate a charting library (e.g., Chart.js or D3.js) to display historical price data for stocks.
* **Database Integration:** Persist chat history for users in a database like Firestore or PostgreSQL.
* **WebSocket for Chat:** Upgrade the chat from HTTP streaming to WebSockets for a more robust real-time connection.
