# System Architecture: Code Quality Toolkit

This directory contains the architectural design artifacts for the **ES2025 Code Quality Toolkit**.

---

## Directory Structure

- **core/**: Diagrams and design documents specific to the Core System (CLI, Engine, Loader, Aggregator).
- **plugins/**: Specific design notes or contracts for the plugin system.
- **app/**: Web App Architecture. Check APP.md for further details.
- **dep/** *(Optional)*: Deployment diagrams or instructions if applicable.

---

## High-Level Overview

The Code Quality Toolkit follows a **Plugin-Based Architecture**.
The Core System acts as an orchestrator that loads dynamic modules (plugins) to perform analysis on source code.

---

## Key Design Principles

- **Modularity**: New features (checks) are added as plugins, not by modifying the core.
- **Interface-Driven**: All plugins must adhere to the `PluginProtocol` contract.
- **Fault Tolerance**: A failure in one plugin does not crash the entire analysis.

---

## Design Artifacts

### 1. Component Diagram
- **Location**: `core/component_diagram.txt`
- **Description**: Shows the high-level wiring of the system, including the Plugin Manager, Execution Engine, and the Plugin API boundary.  

---

### 2. Class Diagram
- **Location**: `core/class_diagram.txt`
- **Description**: Details the classes and relationships within the Core System, including the `ToolkitConfig`, custom Exceptions, and the `PluginProtocol` interface.
- **Visual Reference**: A rendered `.png` image of this diagram is available in the `core/` directory.

---

### 3. Sequence Diagrams
- **Location**: `core/sequence_diagram_failure.txt`
- **Description**: Visualizes key runtime scenarios, such as how the system handles a plugin crash (Error Handling Feature).
- **Visual Reference**: A rendered `.png` image of this diagram is available in the `core/` directory.

---

## How to View Diagrams

The diagrams in this folder are written in **PlantUML code**, saved with a `.txt` extension.

To view them in **VS Code**:
1. Install the *PlantUML* extension (by jebbs).
2. Open any `.txt` file containing the diagram code.
3. Press **Alt + D** (or **Option + D** on Mac) to toggle the preview.

---
