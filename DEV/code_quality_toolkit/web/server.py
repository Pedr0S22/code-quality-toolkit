"""
FastAPI Backend for Code Quality Toolkit.
Handles file uploads, runs the analysis engine in a sandbox, and returns the report.
"""

import shutil
import uuid
import json
import zipfile
import tempfile
import importlib
from pathlib import Path
from typing import List, Dict, Any

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from toolkit.core.engine import run_analysis
from toolkit.core.aggregator import aggregate
from toolkit.core.loader import load_plugins, discover_plugins
from toolkit.utils.config import load_config, ToolkitConfig

app = FastAPI(title="Code Quality Toolkit API", version="0.3.1")

# --- Helper Functions ---

def cleanup_sandbox(path: Path):
    """Background task to remove the temporary sandbox folder."""
    try:
        if path.exists():
            shutil.rmtree(path)
            print(f"Cleaned up sandbox: {path}")
    except Exception as e:
        print(f"Error cleaning up {path}: {e}")

def _to_pascal_case(snake_str: str) -> str:
    """Converts snake_case to PascalCase (e.g. 'dead_code' -> 'DeadCode')."""
    return "".join(word.title() for word in snake_str.split("_"))

def get_discovered_plugins() -> Dict[str, Any]:
    """
    Helper to discover and instantiate all available plugins.
    Returns a dictionary: {'PluginName': plugin_instance}
    """
    plugins_map = {}
    try:
        discovered = discover_plugins()
        if isinstance(discovered, dict):
            plugin_folders = list(discovered.keys())
        else:
            plugin_folders = discovered

        for folder_name in plugin_folders:
            try:
                module_path = f"toolkit.plugins.{folder_name}.plugin"
                module = importlib.import_module(module_path)
                instance = None
                name = _to_pascal_case(folder_name)

                # Strategy A: Look for 'class Plugin'
                if hasattr(module, "Plugin"):
                    plugin_cls = getattr(module, "Plugin")
                    try:
                        instance = plugin_cls()
                        meta = instance.get_metadata()
                        name = meta.get("name", name)
                    except Exception:
                        pass

                # Strategy B: Look for PascalCase class if Strategy A failed or yielded generic name
                if not instance:
                    pascal_name = _to_pascal_case(folder_name)
                    if hasattr(module, pascal_name):
                        plugin_cls = getattr(module, pascal_name)
                        try:
                            instance = plugin_cls()
                            meta = instance.get_metadata()
                            name = meta.get("name", pascal_name)
                        except Exception:
                            pass
                
                # If we successfully created an instance, add it
                if instance:
                    plugins_map[name] = instance
                else:
                    # Fallback: We know the name but couldn't instantiate it
                    # We can't really configure it without an instance, so we skip adding it to map
                    # or we could add a placeholder if strictness varies.
                    print(f"Warning: Could not instantiate plugin from '{folder_name}'")

            except Exception as e:
                print(f"Warning: Could not inspect plugin '{folder_name}': {e}")
                
    except Exception as e:
        print(f"Error exploring plugins: {e}")
        
    return plugins_map

def get_all_plugin_names() -> List[str]:
    """Wrapper to get just names for the simple list endpoint."""
    return sorted(list(get_discovered_plugins().keys()))

def resolve_plugins(requested: str, config: ToolkitConfig) -> List[str]:
    if requested.lower() == "all":
        try:
            all_names = get_all_plugin_names()
            if all_names:
                return all_names
            return config.enabled_plugins
        except Exception as e:
            print(f"Discovery failed, falling back to config: {e}")
            return config.enabled_plugins
    
    plugins = [p.strip() for p in requested.split(",") if p.strip()]
    return plugins if plugins else config.enabled_plugins

# --- Endpoints ---

@app.get("/api/v1/plugins", summary="List all available plugins")
def list_available_plugins():
    """Returns a list of all plugins detected in the system."""
    try:
        names = get_all_plugin_names()
        return {"plugins": names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover plugins: {e}")

@app.get("/api/v1/plugins/configs", summary="List all plugin configurations")
def list_plugin_configs():
    """
    Returns the configuration structure for each plugin dynamically.
    It instantiates each plugin, calls its `configure(defaults)` method,
    and extracts the resulting attributes.
    """
    try:
        # 1. Load system defaults (or toolkit.toml if present in CWD)
        # Note: In a server context, this usually loads the repo's default values
        default_config = load_config(None)
        
        plugins_map = get_discovered_plugins()
        configs_response = {}

        for name, plugin in plugins_map.items():
            plugin_config = {}
            
            # 2. Inject configuration if the plugin supports it
            if hasattr(plugin, "configure"):
                try:
                    # Pass the global config object to the plugin
                    plugin.configure(default_config)
                    
                    # 3. Extract attributes set on the plugin instance
                    # We filter out private attributes (starting with _) and methods
                    # This captures "self.ignore_patterns", "self.severity", etc.
                    for key, value in vars(plugin).items():
                        if not key.startswith("_") and not callable(value) and not key == "config":
                            plugin_config[key] = value
                            
                except Exception as e:
                    print(f"Error configuring plugin {name}: {e}")
                    plugin_config["error"] = "Configuration extraction failed"
            
            configs_response[name] = plugin_config

        return configs_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load configs: {e}")

@app.post("/api/v1/analyze", summary="Analyze a project zip archive")
async def analyze_project(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Project source code zipped"),
    plugins: str = Form("all", description="Comma-separated list of plugins to run"),
    configs: str = Form("{}", description="JSON string of configuration overrides")
):
    """
    1. Receives ZIP, plugins list, and config overrides.
    2. Extracts ZIP to sandbox.
    3. Runs analysis with applied configs.
    4. Zips results (report.json, report.html, dashboard.html) into a response file.
    """
    
    print(f"DEBUG: Plugins: {plugins}")
    print(f"DEBUG: Configs: {configs}")

    # 1. Sandbox Setup
    session_id = str(uuid.uuid4())
    temp_dir = Path(tempfile.gettempdir()) / "toolkit_sessions" / session_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    source_dir = temp_dir / "source"
    source_dir.mkdir()
    
    upload_zip_path = temp_dir / "upload.zip"
    results_zip_path = temp_dir / "results.zip"
    
    report_json_path = temp_dir / "report.json"

    try:
        # 2. Save and Extract Upload
        content = await file.read()
        with open(upload_zip_path, "wb") as f:
            f.write(content)
            
        try:
            with zipfile.ZipFile(upload_zip_path, 'r') as zip_ref:
                zip_ref.extractall(source_dir)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid zip file provided.")

        # 3. Determine Analysis Target
        items = list(source_dir.iterdir())
        if len(items) == 1 and items[0].is_dir():
            analysis_target = items[0]
        else:
            analysis_target = source_dir

        # 4. Load & Update Configuration
        project_toml = analysis_target / "toolkit.toml"
        if project_toml.exists():
            config = load_config(str(project_toml))
        else:
            config = load_config(None)
            
        # Apply User Overrides from Form Data
        try:
            user_configs = json.loads(configs)
            # This is a basic mapping. In a real scenario, you'd map specific 
            # plugin config keys (like "DeadCodeDetector.ignore_patterns") 
            # back to the ToolkitConfig object structure.
            
            # Example mapping for Global Rules
            if "max_line_length" in user_configs:
                config.rules.max_line_length = int(user_configs["max_line_length"])
            # ... add robust mapping logic here based on your frontend structure ...
            
        except json.JSONDecodeError:
            print("Warning: Invalid JSON in configs form data. Using defaults.")

        # 5. Resolve Plugins
        plugin_names = resolve_plugins(plugins, config)
        loaded_plugins = load_plugins(plugin_names)
        
        if not loaded_plugins:
            raise HTTPException(status_code=400, detail="No valid plugins could be loaded.")

        # 6. Run Analysis
        analyzed_files, plugin_status = run_analysis(str(analysis_target), loaded_plugins, config)
        report_data = aggregate(analyzed_files, plugin_status)

        # 7. Generate Reports
        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        generated_htmls = list(analysis_target.glob("*.html"))
        
        # 8. Create Response Zip
        with zipfile.ZipFile(results_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(report_json_path, arcname="report.json")
            for html_file in generated_htmls:
                zf.write(html_file, arcname=html_file.name)

        # 9. Return Response
        background_tasks.add_task(cleanup_sandbox, temp_dir)
        
        return FileResponse(
            path=results_zip_path,
            filename="analysis_results.zip",
            media_type="application/zip"
        )

    except HTTPException:
        cleanup_sandbox(temp_dir)
        raise
    except Exception as e:
        cleanup_sandbox(temp_dir)
        print(f"Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    print("Starting Code Quality Server on http://127.0.0.1:8000")
    uvicorn.run("web.server:app", host="127.0.0.1", port=8000, reload=True)