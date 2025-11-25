"""
FastAPI Backend for Code Quality Toolkit.
Handles file uploads, runs the analysis engine in a sandbox, and returns the report.
"""

import shutil
import uuid
import json
import zipfile
import tempfile
from pathlib import Path
from typing import List

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from toolkit.core.engine import run_analysis
from toolkit.core.aggregator import aggregate
from toolkit.core.loader import load_plugins, discover_plugins
from toolkit.utils.config import load_config, ToolkitConfig

app = FastAPI(title="Code Quality Toolkit API", version="0.2.0")


@app.get("/api/v1/plugins", summary="List all available plugins")
def list_available_plugins():
    """Returns a list of all plugins detected in the system by reading their metadata."""
    try:
        names = get_all_plugin_names()
        return {"plugins": names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover plugins: {e}")


@app.post("/api/v1/analyze", summary="Analyze a project zip archive")
async def analyze_project(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Project source code zipped"),
    plugins: str = Form("all", description="Comma-separated list of plugins to run or 'all'")
):
    """
    1. Receives a ZIP file.
    2. Extracts it to a temporary sandbox.
    3. Runs the toolkit analysis engine.
    4. Returns the report.json file.
    5. Cleans up the sandbox.
    """
    
    print(f"DEBUG: Received plugins value = '{plugins}'")

    # 1. Create a unique sandbox for this request
    session_id = str(uuid.uuid4())
    temp_dir = Path(tempfile.gettempdir()) / "toolkit_sessions" / session_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    source_dir = temp_dir / "source"
    source_dir.mkdir()
    
    zip_path = temp_dir / "upload.zip"
    report_path = temp_dir / "report.json"

    try:
        # 2. Save and Extract the Uploaded Zip
        content = await file.read()
        with open(zip_path, "wb") as f:
            f.write(content)
            
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(source_dir)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid zip file provided.")

        # 3. Load Configuration
        # Smart detection: check if the extraction resulted in a single nested folder
        # (common behavior when zipping a folder). If so, step into it.
        items = list(source_dir.iterdir())
        if len(items) == 1 and items[0].is_dir():
            analysis_target = items[0]
        else:
            analysis_target = source_dir

        # Check for config in the target directory
        project_config = analysis_target / "toolkit.toml"
        if project_config.exists():
            config = load_config(str(project_config))
        else:
            config = load_config(None) # Load default

        # 4. Resolve and Load Plugins
        plugin_names = resolve_plugins(plugins, config)
        loaded_plugins = load_plugins(plugin_names)
        print(f"DEBUG: Running plugins: {plugin_names}")

        if not loaded_plugins:
            raise HTTPException(status_code=400, detail="No valid plugins could be loaded.")

        # 5. Run Analysis Engine
        # The engine scans the analysis_target recursively
        analyzed_files, plugin_status = run_analysis(str(analysis_target), loaded_plugins, config)
        
        # 6. Aggregate Results
        report_data = aggregate(analyzed_files, plugin_status)

        # 7. Save Report to Disk
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        # 8. Return Response & Schedule Cleanup
        background_tasks.add_task(cleanup_sandbox, temp_dir)
        
        return FileResponse(
            path=report_path,
            filename="report.json",
            media_type="application/json"
        )

    except HTTPException:
        cleanup_sandbox(temp_dir)
        raise
    except Exception as e:
        cleanup_sandbox(temp_dir)
        print(f"Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
# Helper Functions

def cleanup_sandbox(path: Path):
    """Background task to remove the temporary sandbox folder."""
    try:
        if path.exists():
            shutil.rmtree(path)
            print(f"cleaned up sandbox: {path}")
    except Exception as e:
        print(f"Error cleaning up {path}: {e}")


def _to_pascal_case(snake_str: str) -> str:
    """
    Converts snake_case to PascalCase.
    Example: 'dead_code_detector' -> 'DeadCodeDetector'
    """
    return "".join(word.title() for word in snake_str.split("_"))

def get_all_plugin_names() -> List[str]:
    """
    Helper to discover and load all plugins to get their proper metadata names.
    Robustly handles broken/incomplete plugins by ignoring them.
    """
    real_names = []
    try:
        # Find all potential plugin folders/modules
        discovered = discover_plugins()
        
        # handle if it returns dict or list
        if isinstance(discovered, dict):
            plugin_folders = list(discovered.keys())
        else:
            plugin_folders = discovered

        # Try loading each plugin individually
        for folder_name in plugin_folders:
            try:
                # Convert folder names to PascalCase to try loading them
                potential_name = _to_pascal_case(folder_name)
                
                # Load specific plugin (List of 1) to isolate failures.
                # If this specific plugin is broken/incomplete, load_plugins will raise an error.
                loaded = load_plugins([potential_name])
                
                # Extract metadata from the loaded instance
                for plugin_instance in loaded.values():
                    try:
                        # This calls the get_metadata() method you showed in the snippet
                        meta = plugin_instance.get_metadata()
                        # We use the "name" field from the metadata (e.g. "DuplicationChecker")
                        real_names.append(meta.get("name", potential_name))
                    except Exception:
                        # Fallback if get_metadata crashes
                        real_names.append(potential_name)
            
            except Exception as e:
                # This block catches "Requested plugins not found" or syntax errors
                # and allows the loop to continue to the next plugin.
                print(f"Skipping broken/incomplete plugin '{folder_name}': {e}")
                continue
                
    except Exception as e:
        print(f"Error exploring plugins: {e}")
        
    return real_names

def resolve_plugins(requested: str, config: ToolkitConfig) -> List[str]:
    """Resolves the comma-separated string from the form into a list of plugin names."""
    if requested.lower() == "all":
        try:
            # Try to get all available plugins dynamically
            all_plugins = get_all_plugin_names()
            if all_plugins:
                return all_plugins
            return config.enabled_plugins
        except Exception as e:
            print(f"Discovery failed, falling back to config: {e}")
            return config.enabled_plugins
    
    # If specific plugins were requested
    plugins = [p.strip() for p in requested.split(",") if p.strip()]
    return plugins if plugins else config.enabled_plugins


if __name__ == "__main__":
    # Run the Server
    print("Starting Code Quality Server on http://127.0.0.1:8000")
    uvicorn.run("web.server:app", host="127.0.0.1", port=8000, reload=True)