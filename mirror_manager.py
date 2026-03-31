import os
import json
import gradio as gr
from PIL import Image
from modules import script_callbacks, shared, images

# Path to store our persistent rules
RULES_FILE = os.path.join(os.path.dirname(__file__), "mirror_rules.json")

# Guard to prevent infinite recursion
is_mirroring = False

def load_rules():
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_rules(rules_list):
    with open(RULES_FILE, "w") as f:
        json.dump(rules_list, f, indent=4)

def on_image_saved(params: script_callbacks.ImageSaveParams):
    global is_mirroring
    
    # EXIT if we are already in the middle of a mirror operation
    if is_mirroring:
        return

    rules = load_rules()
    if not rules:
        return

    # Extract metadata safely
    gen_info = params.pnginfo.get("parameters", "") if params.pnginfo else ""
    if not gen_info and hasattr(params, 'p') and params.p:
        gen_info = getattr(params.p, "info", "")

    is_mirroring = True
    try:
        for rule in rules:
            if not rule.get("active", True):
                continue
                
            target_dir = rule.get("path", "").strip()
            target_ext = rule.get("ext", "png").lower()

            if not target_dir or not os.path.isdir(target_dir):
                continue

            # Get filename without extension
            base_name = os.path.basename(params.filename)
            file_no_ext = os.path.splitext(base_name)[0]

            # Save the mirror
            images.save_image(
                params.image, 
                target_dir, 
                "", 
                extension=target_ext, 
                forced_filename=file_no_ext,
                info=gen_info
            )
    except Exception as e:
        print(f"[Mirror Manager] Error during mirror: {e}")
    finally:
        is_mirroring = False

def update_config(data):
    """Parses the raw textbox data back into JSON for storage"""
    try:
        rules = json.loads(data)
        save_rules(rules)
        return "✅ Configuration saved and applied!"
    except Exception as e:
        return f"❌ Error: Invalid JSON format. {str(e)}"

def on_ui_tabs():
    # Load existing rules as a formatted string for the textbox
    current_rules = load_rules()
    if not current_rules:
        current_rules = [{"active": True, "path": "/path/to/folder", "ext": "png"}]
    
    initial_value = json.dumps(current_rules, indent=4)

    with gr.Blocks(analytics_enabled=False) as mirror_ui:
        gr.Markdown("### 📂 Image Mirror Manager (Stable)")
        gr.Markdown("Edit the JSON below to add or remove mirror paths. Format: `active`, `path`, `ext` (png, webp, jpg).")
        
        with gr.Column():
            config_input = gr.Code(
                value=initial_value,
                language="json",
                label="Mirror Rules Configuration"
            )
            save_btn = gr.Button("💾 Save Configuration", variant="primary")
            status_out = gr.Markdown("")

            save_btn.click(
                fn=update_config,
                inputs=[config_input],
                outputs=[status_out]
            )
            
    return [(mirror_ui, "Mirror Manager", "mirror_manager_tab")]

# Register callbacks
script_callbacks.on_ui_tabs(on_ui_tabs)
script_callbacks.on_image_saved(on_image_saved)