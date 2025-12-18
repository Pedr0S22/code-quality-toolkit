# Developer Documentation — Web UI / Client–Server Architecture
## TECHNICAL DOCUMENTATION

### Description

This document outlines the technical architecture of the Web UI system, covering the Client-Server interaction, file processing, and the role of the FastAPI Controller in orchestrating the Toolkit Engine.

## 1. Purpose

The primary purpose of this architecture is to provide a robust, decoupled, and user-friendly interface for the static analysis engine. By separating the GUI (Client) from the heavy processing (Toolkit Engine) via an API gateway (Controller), we achieve better scalability, responsiveness, and platform independence.

## 2. Client-Server Architecture (Rich Client)

The application adheres to a three-tiered architecture. The `client.py` component acts as a Rich Client, handling all user interface and presentation logic, while relying on the FastAPI server `server.py` for all core business logic and analysis execution. For further architecture analysis, see [APP.md](/ARCH/app/APP.md).

## 3. Endpoints

The FastAPI Controller exposes the following key endpoints:

#### `GET /api/v1/plugins`

- Returns a list of all available and configured plugins.

#### `GET /api/v1/plugins/configs`

- Returns the default configuration settings for each available plugin.

#### `POST /api/v1/analyze`

- Initiates the complete analysis cycle.
  - Endpoint Flow:

     - Receives the ZIP archive containing the file(s) to be analyzed and the plugins with their respective configurations from the Client.

    - Extracts the contents into a temporary directory on the server.

    - Invokes the Toolkit Engine's primary analysis function: `run_analysis(path, configs)`.

    - The Engine generates analysis artifacts (`report.html`, D3 dashboards (`<plugin_name>_dashboard.html`), `report.json`).

    - The Controller creates a return ZIP archive containing all generated files.

    - Sends the results ZIP back to the Client.


## 4. File Transaction Flow

The complete cycle involves a robust file exchange process using ZIP archives to efficiently transfer potentially large source code and result sets.

```txt
sequenceDiagram
    participant C as CLIENT (client.py)
    participant S as SERVER (server.py)
    participant E as TOOLKIT ENGINE (core + plugins)

    C->>C: Create Source Code ZIP
    C->>S: POST /api/v1/analyze (Send ZIP)
    S->>S: Extract ZIP to Temp Directory
    S->>E: run_analysis(path, configs)
    E->>E: Execute Analysis & Generate Artifacts (report.html, dashboards)
    E->>S: Return Analysis Results
    S->>S: Create Results ZIP
    S->>C: Return Results ZIP
    C->>C: Extract Results ZIP
    C->>C: Load local assets (d3.js) from web/assets
    C->>C: Inject Assets & Auto-open report.html
    C->>C: Possibility to visualize each plugins dashboard
```

## 5. Asynchronous Communication (Signal/Slot Equivalent)

The application uses asynchronous mechanisms to ensure responsiveness, which serves as the equivalent of a Signal/Slot pattern for network I/O.

### Client Side

- **User Actions**: User interactions trigger GUI events.

- **HTTP Calls**: Network requests are executed asynchronously (e.g., using threads or non-blocking I/O) to prevent the graphical user interface from freezing during the potentially long analysis process.

- **Callbacks**: Upon receiving an HTTP response from the server, callbacks are used to safely update the interface with the results or status indicators.

### Server Side

- **Requests**: All incoming requests are handled asynchronously.

- **Handlers**: FastAPI uses async def for its route handlers, allowing the server to efficiently manage multiple concurrent client connections.

- **Event Loop**: This design ensures the server's event loop is not blocked by a single analysis task, maximizing throughput and stability.

## 6. Project Structure

The Web UI components are logically separated from the core toolkit components:

```txt
DEV/
 └─ code_quality_toolkit/
     ├─ web/
     │   ├─ assets/                 # Stores downloaded JS libraries (e.g., D3.js)
     │   ├─ scripts/
     │   │   └─ fetch_assets.py     # Script to download external dependencies
     │   ├─ server.py
     │   ├─ client.py
     │   └─ SPEC.md (DEV Docs)
     └─ src/
         └─ toolkit/
             ├─ core/
             ├─ plugins/
             │   └─ DASHBOARD.md
             └─ ...
```

## 7. Running the App
To run the Code Quality Toolkit App, you must follow these steps:

1. Setup Environment & Assets: Run the setup command to install dependencies and download necessary static assets (D3.js).

```
make setup
```

(Or manually run python web/scripts/fetch_assets.py if not using Make)

2. Start the Server: Run server.py on `http://127.0.0.1:8000`:

```
make run_server
```

3. Start the Client: Run client.py in a separate terminal:

```
make run_client
```

## Authors
Pedro Silva, 2023235452, @Pedr0S22

André Silva, 2023212648, @andresilva219

Oleksandra Grymalyuk, 2023218767, @my3007sunshine

Rabia Saygin, 2024187186, @rferyals

Isaque Capra, 2023221892, @Isaque_capra

Tiago Alves, 2023207875, @tiagoalves.21

Mathias Welz, 2025167903,@mathiasgwelz

#### Disclaimer: This web application component was build using AI.

