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
from toolkit.core.loader import load_plugins
from toolkit.utils.config import load_config, ToolkitConfig

app = FastAPI(title="Code Quality Toolkit API", version="0.2.0")

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


def resolve_plugins(requested: str, config: ToolkitConfig) -> List[str]:
    """Resolves the comma-separated string from the form into a list of plugin names."""
    if requested.lower() == "all":
        return config.enabled_plugins
    
    plugins = [p.strip() for p in requested.split(",") if p.strip()]
    return plugins if plugins else config.enabled_plugins


if __name__ == "__main__":
    # Allows running this script directly with the VS Code "Play" button
    print("Starting Code Quality Server on http://127.0.0.1:8000")
    uvicorn.run("toolkit.web.server:app", host="127.0.0.1", port=8000, reload=True)