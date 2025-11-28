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
import os
import re
from pathlib import Path
from typing import List, Dict, Any

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from toolkit.core.engine import run_analysis
from toolkit.core.aggregator import aggregate
from toolkit.core.loader import load_plugins, discover_plugins
from toolkit.utils.config import load_config, ToolkitConfig

app = FastAPI(title="Code Quality Toolkit API", version="0.3.0")

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
    # Simple regex for Camel/Pascal to snake
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def get_discovered_plugins() -> Dict[str, Any]:
    """Helper to discover and instantiate all available plugins."""
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

# --- Endpoints ---

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
        default_config = ToolkitConfig()
        plugins_map = get_discovered_plugins()
        configs_response = {}

        for name, plugin in plugins_map.items():
            plugin_config = {}
            if hasattr(plugin, "configure"):
                try:
                    plugin.configure(default_config)
                    for key, value in vars(plugin).items():
                        if not key.startswith("_") and not callable(value) and not key=="config":
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

        # 4. Load Base Configuration
        project_toml = analysis_target / "toolkit.toml"
        if project_toml.exists():
            base_config = load_config(str(project_toml))
        else:
            base_config = load_config(None)
            
        # 5. Parse User Configs & Apply Overrides
        # Strategy: Export config to dict -> Update dict -> Re-instantiate ToolkitConfig
        
        # Determine how to export based on config object type (Pydantic vs Dataclass vs Class)
        if hasattr(base_config, "model_dump"):
            config_dict = base_config.model_dump() # Pydantic v2
        elif hasattr(base_config, "dict"):
            config_dict = base_config.dict() # Pydantic v1
        else:
            # Simple object -> dict fallback
            # We assume a structure similar to what load_config produces
            # Warning: vars() might not capture everything if using __slots__
            try:
                config_dict = vars(base_config)
            except TypeError:
                # If base_config doesn't have __dict__, it might be a frozen dataclass or specialized object
                # Try explicit copying if it's a known structure or fallback to empty dict if we can't inspect
                print("Warning: Could not convert config to dict via vars(). Using fallback inspection.")
                config_dict = {} # Should be populated manually or via other inspection methods if vars fails

        requested_plugins = []
        try:
            user_overrides = json.loads(configs)
            
            if isinstance(user_overrides, dict) and user_overrides:
                requested_plugins = list(user_overrides.keys())
                
                for plugin_name, plugin_settings in user_overrides.items():
                    if not isinstance(plugin_settings, dict): continue
                    
                    # A. Map to Global Rules (e.g., [rules] section)
                    # We check if 'rules' key exists in the exported dictionary
                    if "rules" in config_dict:
                        # Depending on structure, config_dict['rules'] might be a dict or object
                        # We need it to be a dict for updating
                        if hasattr(config_dict["rules"], "__dict__"):
                             rules_dict = vars(config_dict["rules"])
                        elif isinstance(config_dict["rules"], dict):
                             rules_dict = config_dict["rules"]
                        else:
                             # If it's an object but vars() fails, skip or try direct attr access
                             rules_dict = {} 

                        for key, value in plugin_settings.items():
                            if key in rules_dict:
                                rules_dict[key] = value
                        
                        # If we modified a detached dict (from vars), we might need to put it back
                        # But since we are re-instantiating, we need the structure to be right for the constructor
                        # If ToolkitConfig(rules=RulesConfig(...)), we need to pass a dict or object?
                        # Usually Pydantic accepts nested dicts.
                        config_dict["rules"] = rules_dict

                    # B. Map to Specific Plugin Section (e.g., [plugins.dead_code])
                    if "plugins" in config_dict:
                        plugins_section = config_dict["plugins"]
                        # Normalize plugins_section to dict if needed
                        if hasattr(plugins_section, "__dict__"):
                            plugins_dict = vars(plugins_section)
                        elif isinstance(plugins_section, dict):
                            plugins_dict = plugins_section
                        else:
                            plugins_dict = {}

                        # Try exact match or snake_case conversion
                        potential_keys = [plugin_name, _to_snake_case(plugin_name)]
                        # Also handle "DeadCodeDetector" -> "dead_code" (common pattern removing 'Detector'/'Checker')
                        short_name = _to_snake_case(plugin_name).replace("_detector", "").replace("_checker", "")
                        potential_keys.append(short_name)

                        target_key = None
                        for pk in potential_keys:
                            if pk in plugins_dict:
                                target_key = pk
                                break
                        
                        if target_key:
                            target_plugin_config = plugins_dict[target_key]
                            # Convert target config to dict to update it
                            if hasattr(target_plugin_config, "__dict__"):
                                target_conf_dict = vars(target_plugin_config)
                            elif isinstance(target_plugin_config, dict):
                                target_conf_dict = target_plugin_config
                            else:
                                target_conf_dict = {}
                            
                            target_conf_dict.update(plugin_settings)
                            plugins_dict[target_key] = target_conf_dict
                        
                        config_dict["plugins"] = plugins_dict

            else:
                requested_plugins = get_all_plugin_names()

            # RE-CREATE THE CONFIG OBJECT
            # This bypasses the "read-only" error by creating a fresh instance with new values
            try:
                # We assume ToolkitConfig can be instantiated with kwargs matching its structure
                # If it's a Pydantic model, it handles nested dicts automatically.
                config = ToolkitConfig(**config_dict)
            except Exception as e:
                print(f"Warning: Failed to re-instantiate config from dict: {e}")
                # Fallback: use base config if patch fails
                config = base_config 

        except json.JSONDecodeError:
            print("Warning: Invalid JSON in configs. Using defaults.")
            try:
                requested_plugins = get_all_plugin_names()
            except:
                requested_plugins = base_config.enabled_plugins
            config = base_config

        # 6. Run Analysis
        if not requested_plugins:
             requested_plugins = config.enabled_plugins

        print(f"DEBUG: Running plugins: {requested_plugins}")
        loaded_plugins = load_plugins(requested_plugins)
        
        if not loaded_plugins:
             raise HTTPException(status_code=400, detail="No valid plugins could be loaded.")

        analyzed_files, plugin_status = run_analysis(str(analysis_target), loaded_plugins, config)
        report_data = aggregate(analyzed_files, plugin_status)

        # 7. Generate Files
        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        with open(report_html_path, "w", encoding="utf-8") as f:
            f.write("<html><body><h1>Analysis Report</h1><p>Generated by Code Quality Toolkit</p></body></html>")

        # 8. Zip Response
        with zipfile.ZipFile(results_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(report_json_path, arcname="report.json")
            zf.write(report_html_path, arcname="report.html")
            for html_file in analysis_target.glob("*_dashboard.html"):
                plugin_name = html_file.name.replace("_dashboard.html", "")
                zf.write(html_file, arcname=f"{plugin_name}/dashboard.html")

        # 9. Return
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