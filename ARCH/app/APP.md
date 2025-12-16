## Client-Server Architecture (Rich Client)

The application adheres to a three-tiered architecture. The `client.py` component acts as a Rich Client, handling all user interface and presentation logic, while relying on the FastAPI server `server.py` for all core business logic and analysis execution. Below is the UML Diagram of the architecture:

```
+-------------------+         +----------------------+        +-----------------------+
|      CLIENT       | <---->  |        SERVER        | <----> |     TOOLKIT ENGINE    |
|  (client.py GUI)  |         |   (FastAPI server)   |        |    (Core + Plugins)   |
+-------------------+         +----------------------+        +-----------------------+
```

### Architecture Components
The three main components are:

### CLIENT (client.py GUI)
- **Role**: Presentation & I/O

- **Description**: Handles user input (directory selection, configuration), manages file packaging/unpacking, and renders the final report.

Asset Injection: The client is responsible for reading local JavaScript libraries (e.g., D3.js) from the web/assets/ directory and injecting them directly into the HTML dashboards before rendering. This ensures the application works offline and bypasses QWebEngineView CORS restrictions.

Communicates with the server via HTTP (`http://127.0.0.1:8000`).

### SERVER (server.py FastAPI Server)

- **Role**: Orchestration & API Gateway

- **Description**: Receives and routes client requests, manages temporary file storage, invokes the Toolkit Engine, and packages the final results for return. It runs in `http://127.0.0.1:8000`.

### TOOLKIT ENGINE (Core + Plugins)

- **Role**: Business Logic & Processing

- **Description**: Loads configurations, executes analysis on the source code, and produces analysis artifacts (issues.json, dashboards, report.html).

### Asset Management & Offline Support
To ensure the application functions without an internet connection and adheres to strict browser security policies (CORS), the system uses a Bundled Asset strategy rather than relying on CDNs.

* **Fetching**: The script web/scripts/fetch_assets.py downloads required dependencies (e.g., d3.v7.min.js) from official sources during the project setup phase.

* **Storage**: Assets are stored locally in web/assets/.

* **Runtime Injection**: When the Client renders a dashboard, it intercepts the HTML content, reads the local asset file, and replaces the remote CDN <script> tags with inline JavaScript.