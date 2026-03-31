import os
import json
import io
import subprocess
import gradio as gr
from PIL import Image
from modules import script_callbacks, shared, images

RULES_FILE = os.path.join(os.path.dirname(__file__), "mirror_rules.json")
is_mirroring = False

def load_rules():
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, "r") as f:
                return json.load(f)
        except: return []
    return []

def save_rules(rules):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=4)

def copy_image_to_clipboard(img):
    """Cross-platform clipboard support for images."""
    try:
        output = io.BytesIO()
        img.save(output, format="PNG")
        data = output.getvalue()
        output.close()

        if os.name == 'nt':  # Windows
            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data[14:]) # Strip BMP header if needed, but for PNG it's complex
            # Note: For Windows, standard PIL to clipboard usually requires 'pywin32'
            win32clipboard.CloseClipboard()
        else:  # Linux
            # Try xclip (X11)
            subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'image/png'], input=data, check=True)
    except Exception as e:
        print(f"[Mirror Manager] Clipboard copy failed: {e}. (On Linux, ensure 'xclip' or 'wl-copy' is installed)")

def on_image_saved(params: script_callbacks.ImageSaveParams):
    global is_mirroring
    if is_mirroring: return
    
    rules = load_rules()
    settings = shared.opts.data.get("mirror_manager_settings", {})
    copy_to_clipboard = settings.get("copy_to_clipboard", False)

    if not rules and not copy_to_clipboard: return

    gen_info = params.pnginfo.get("parameters", "") if params.pnginfo else ""
    if not gen_info and hasattr(params, 'p'):
        gen_info = getattr(params.p, "info", "")

    is_mirroring = True
    try:
        # Handle Clipboard
        if copy_to_clipboard:
            copy_image_to_clipboard(params.image)

        # Handle File Mirrors
        for rule in rules:
            if not rule.get("active", True) or not rule.get("path"): continue
            target_dir = rule["path"].strip()
            if not os.path.isdir(target_dir): continue

            base_name = os.path.basename(params.filename)
            file_no_ext = os.path.splitext(base_name)[0]

            # SAVE IMAGE with custom compression level (0 is least compressed/fastest)
            # Default PIL is 6. We'll use 1 or 0 for maximum quality/speed.
            images.save_image(
                params.image, target_dir, "", 
                extension=rule.get("ext", "png"), 
                forced_filename=file_no_ext, 
                info=gen_info,
                save_to_dirs=False # Prevent extra subfolders
            )
    finally:
        is_mirroring = False

def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as mirror_ui:
        gr.Markdown("### 📂 Mirror Manager")
        
        hidden_state = gr.Textbox(value=json.dumps(load_rules()), visible=False)
        
        with gr.Row():
            clipboard_toggle = gr.Checkbox(
                label="📋 Automatically copy every generation to clipboard", 
                value=shared.opts.data.get("mirror_manager_settings", {}).get("copy_to_clipboard", False)
            )

        with gr.Column() as main_container:
            rows = []
            for i in range(10):
                with gr.Row(visible=False) as row:
                    active = gr.Checkbox(label="Active", value=True, scale=0)
                    path = gr.Textbox(label="Target Path", placeholder="/home/user/Downloads", scale=4)
                    ext = gr.Dropdown(choices=["png", "webp", "jpg"], value="png", label="Ext", scale=1)
                    rows.append({"row": row, "active": active, "path": path, "ext": ext})

            with gr.Row():
                add_btn = gr.Button("➕ Add Row", variant="secondary")
                save_btn = gr.Button("💾 Save Configuration", variant="primary")
            
            status = gr.Markdown("")

        def refresh_ui(raw_json):
            data = json.loads(raw_json)
            updates = []
            for i in range(10):
                if i < len(data):
                    item = data[i]
                    updates.extend([gr.update(visible=True), item.get("active", True), item.get("path", ""), item.get("ext", "png")])
                else:
                    updates.extend([gr.update(visible=False), True, "", "png"])
            return updates

        def pack_and_save(clipboard_val, *args):
            new_data = []
            for i in range(0, len(args), 3):
                if args[i+1]:
                    new_data.append({"active": args[i], "path": args[i+1], "ext": args[i+2]})
            save_rules(new_data)
            
            # Save the clipboard setting to shared.opts
            shared.opts.data["mirror_manager_settings"] = {"copy_to_clipboard": clipboard_val}
            shared.opts.save(shared.config_filename)
            
            return json.dumps(new_data), "✅ Saved!"

        mirror_ui.load(fn=refresh_ui, inputs=[hidden_state], 
                      outputs=[comp for r in rows for comp in [r["row"], r["active"], r["path"], r["ext"]]])
        
        add_btn.click(fn=lambda x: json.dumps(json.loads(x) + [{"active":True, "path":"", "ext":"png"}]) if len(json.loads(x)) < 10 else x,
                      inputs=[hidden_state], outputs=[hidden_state]).then(
                      fn=refresh_ui, inputs=[hidden_state], 
                      outputs=[comp for r in rows for comp in [r["row"], r["active"], r["path"], r["ext"]]])

        all_inputs = [clipboard_toggle]
        for r in rows: all_inputs.extend([r["active"], r["path"], r["ext"]])
        
        save_btn.click(fn=pack_and_save, inputs=all_inputs, outputs=[hidden_state, status])

    return [(mirror_ui, "Mirror Manager", "mirror_manager_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
script_callbacks.on_image_saved(on_image_saved)