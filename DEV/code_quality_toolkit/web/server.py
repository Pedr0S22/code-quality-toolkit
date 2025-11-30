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
import re
from pathlib import Path
from typing import List, Dict, Any

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from toolkit.core.engine import run_analysis
from toolkit.core.aggregator import aggregate
from toolkit.core.exporters import generate_html
from toolkit.core.loader import load_plugins, discover_plugins
from toolkit.utils.config import load_config, ToolkitConfig

TOOLKIT_ROOT = Path("/es2025-pl8/DEV/code_quality_toolkit")

app = FastAPI(title="Code Quality Toolkit API", version="0.3.0")


@app.get("/api/v1/plugins", summary="List all available plugins")
def list_available_plugins():
    try:
        names = get_all_plugin_names()
        return {"plugins": names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover plugins: {e}")

@app.get("/api/v1/plugins/configs", summary="List all plugin configurations")
def list_plugin_configs():
    try:
        # Get fresh defaults from our new Config structure
        default_config = ToolkitConfig()
        plugins_map = get_discovered_plugins()
        configs_response = {}

        for name, plugin in plugins_map.items():
            plugin_config = {}
            if hasattr(plugin, "configure"):
                try:
                    plugin.configure(default_config)
                    
                    # Extract public attributes
                    if hasattr(plugin, "__dict__"):
                        source = vars(plugin)
                    else:
                        # Fallback for plugins without __dict__
                        source = {k: getattr(plugin, k) for k in dir(plugin) if not k.startswith("_")}

                    for key, value in source.items():
                        if not key.startswith("_") and not callable(value) and key != "config":
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
    configs: str = Form("{}", description="JSON object mapping PluginName -> ConfigOverrides")
):
    print(f"DEBUG: Configs Payload: {configs}")

    # 1. Sandbox Setup
    session_id = str(uuid.uuid4())
    temp_dir = Path(tempfile.gettempdir()) / "toolkit_sessions" / session_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    source_dir = temp_dir / "source"
    source_dir.mkdir()
    
    upload_zip_path = temp_dir / "upload.zip"
    results_zip_path = temp_dir / "analysis_results.zip"
    report_json_path = temp_dir / "report.json"
    report_html_path = temp_dir / "report.html"

    try:
        # 2. Save and Extract
        content = await file.read()
        with open(upload_zip_path, "wb") as f:
            f.write(content)
        try:
            with zipfile.ZipFile(upload_zip_path, 'r') as zip_ref:
                zip_ref.extractall(source_dir)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid zip file provided.")

        # 3. Determine Target
        items = list(source_dir.iterdir())
        if len(items) == 1 and items[0].is_dir():
            analysis_target = items[0]
        else:
            analysis_target = source_dir

        # 4. Load Config (with our fixes, this object is now fully mutable where needed)
        project_toml = analysis_target / "toolkit.toml"
        if project_toml.exists():
            config = load_config(str(project_toml))
        else:
            config = load_config(None)

        # 5. Apply JSON Overrides
        requested_plugins = []
        try:
            user_overrides = json.loads(configs)
            if isinstance(user_overrides, dict) and user_overrides:
                requested_plugins = list(user_overrides.keys())
                
                for plugin_name, plugin_settings in user_overrides.items():
                    if not isinstance(plugin_settings, dict): continue
                    
                    # Update Global Rules (config.rules is now a mutable dataclass)
                    for key, value in plugin_settings.items():
                        if hasattr(config.rules, key):
                            # Simple type conversion if needed, or trust input
                            try:
                                setattr(config.rules, key, value)
                            except Exception:
                                pass
                    
                    # Update Plugin Specifics (config.plugins.dead_code is now a SimpleNamespace)
                    # Map "DeadCodeDetector" -> "dead_code"
                    if plugin_name == "DeadCodeDetector":
                        target = config.plugins.dead_code
                        for key, value in plugin_settings.items():
                            setattr(target, key, value)
                    
                    # Add other plugin mappings here as needed

                    # Generic Logic to replace hardcoded "if plugin_name == ..."
                    # Updated Generic Logic to handle suffixes like 'Detector'
                    #potential_attrs = [
                    #    _to_snake_case(plugin_name),                                                 # dead_code_detector
                    #    _to_snake_case(plugin_name).replace("_detector", "").replace("_checker", "") # dead_code
                    #]

                    #target_found = False
                    #for attr in potential_attrs:
                    #    if hasattr(config.plugins, attr):
                    #        target = getattr(config.plugins, attr)
                    #        for key, value in plugin_settings.items():
                    #            setattr(target, key, value)
                    #        target_found = True
                    #        break

                    # OR

                    # B. Update Specific Plugin Configs (Generic)
                    #if "plugins" in final_config_dict:
                    #    # Ensure plugins section is a dict
                    #    if not isinstance(final_config_dict["plugins"], dict):
                    #         final_config_dict["plugins"] = _safe_export_config(final_config_dict["plugins"])
                    #    
                    #    plugins_section = final_config_dict["plugins"]
                    #    
                    #    # Generate potential keys (e.g., 'dead_code_detector', 'dead_code')
                    #    snake_name = _to_snake_case(plugin_name)
                    #    potential_keys = [
                    #        snake_name, 
                    #        snake_name.replace("_detector", "").replace("_checker", "")
                    #    ]
                    #    
                    #    for pk in potential_keys:
                    #        if pk in plugins_section:
                    #            # We found the target config section!
                    #            target_conf = plugins_section[pk]
                    #            
                    #            # Ensure target is a dict before updating
                    #            if not isinstance(target_conf, dict):
                    #                target_conf = _safe_export_config(target_conf)
                    #                plugins_section[pk] = target_conf
                    #            
                    #            # Apply the user settings
                    #            target_conf.update(plugin_settings)
                    #            break # Stop looking after finding the match

            else:
                requested_plugins = get_all_plugin_names()

        except json.JSONDecodeError:
            print("Warning: Invalid JSON in configs. Using defaults.")
            requested_plugins = config.enabled_plugins

        if not requested_plugins:
            requested_plugins = config.enabled_plugins

        print(f"DEBUG: Running plugins: {requested_plugins}")
        loaded_plugins = load_plugins(requested_plugins)
        
        if not loaded_plugins:
            raise HTTPException(status_code=400, detail="No valid plugins could be loaded.")

        # 6. Run Analysis
        analyzed_files, plugin_status = run_analysis(str(analysis_target), loaded_plugins, config)
        report_data_json = aggregate(analyzed_files, plugin_status)
        report_data_html = generate_html(report_data_json)

        # 7. Generate Output
        
        # A. Save JSON Report
        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(report_data_json, f, indent=2, ensure_ascii=False)

        with open(report_html_path, "w", encoding="utf-8") as f:
            f.write(report_data_html)
            
        # B. Create the ZIP Response
        with zipfile.ZipFile(results_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Add report.json
            zf.write(report_json_path, arcname="report.json")
            
            # 2. Add report.html (From Project Root)
            zf.write(report_html_path, arcname="report.html")

            # 3. Add Plugin Dashboards (From src/toolkit/plugins/<name>/dashboard.html)
            # We iterate over the plugins that were actually loaded/requested
            for plugin_name in loaded_plugins.keys():
                # Convert PascalCase to folder_name (assuming folder is snake_case or similar)
                # If your folder names match the plugin names exactly, use plugin_name.
                # If your folders are snake_case (e.g. DeadCodeDetector -> dead_code_finder), 
                # you might need the helper _to_snake_case(plugin_name).
                # Assuming folders match the keys from get_discovered_plugins (usually folder names):
                
                # NOTE: In your loader, the keys are usually PascalCase names. 
                # We need to find the file. Let's try constructing the path.
                
                # Construct path: src/toolkit/plugins/<PluginName>/dashboard.html
                # You might need to adjust if folder names differ from Class names.
                snake_name = _to_snake_case(plugin_name)
                dashboard_path = TOOLKIT_ROOT / "src/toolkit/plugins" / snake_name / f"{snake_name}_dashboard.html"

                if dashboard_path.exists():
                    # Archive structure: <PluginName>/dashboard.html
                    zf.write(dashboard_path, arcname=f"{snake_name}_dashboard.html")
                
                else:
                    print(f"WARNING: Could not find {dashboard_path}")
                    zf.writestr(f"{snake_name}_dashboard.html", "<html><body><h1>Dashboard Not Found on Server</h1></body></html>")

        background_tasks.add_task(cleanup_sandbox, temp_dir)
        return FileResponse(path=results_zip_path, filename="analysis_results.zip", media_type="application/zip")
    except HTTPException:
        cleanup_sandbox(temp_dir)
        raise
    except Exception as e:
        cleanup_sandbox(temp_dir)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
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

def _to_snake_case(name: str) -> str:
    """Converts PascalCase to snake_case (e.g. 'DeadCodeDetector' -> 'dead_code')."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def get_discovered_plugins() -> Dict[str, Any]:
    """Helper to discover and instantiate all available plugins."""
    plugins_map = {}
    try:
        discovered = discover_plugins()
        # Normalize return type (list or dict)
        plugin_folders = list(discovered.keys()) if isinstance(discovered, dict) else discovered

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

                # Strategy B: Look for PascalCase class
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
                
                if instance:
                    plugins_map[name] = instance

            except Exception as e:
                print(f"Warning: Could not inspect plugin '{folder_name}': {e}")
                
    except Exception as e:
        print(f"Error exploring plugins: {e}")
        
    return plugins_map

def get_all_plugin_names() -> List[str]:
    return sorted(list(get_discovered_plugins().keys()))

if __name__ == "__main__":
    print("Starting Code Quality Server on http://127.0.0.1:8000")
    uvicorn.run("web.server:app", host="127.0.0.1", port=8000, reload=True)