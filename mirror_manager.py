import os
import json
import gradio as gr
from PIL import Image
from modules import script_callbacks, shared, images

# Path to store our persistent rules
RULES_FILE = os.path.join(os.path.dirname(__file__), "mirror_rules.json")

def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    return []

def save_rules(rules):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f)

def on_image_saved(params: script_callbacks.ImageSaveParams):
    rules = load_rules()
    if not rules:
        return

    # Try to grab the metadata (generation info) safely
    # params.pnginfo usually contains the metadata dictionary in newer Forge versions
    gen_info = params.pnginfo.get("parameters", "") if params.pnginfo else ""
    
    # Fallback: Check if it's available in the processing object 'p'
    if not gen_info and hasattr(params, 'p') and params.p:
        gen_info = getattr(params.p, "info", "")

    for rule in rules:
        if not rule.get("active", True):
            continue
            
        target_dir = rule.get("path", "")
        target_ext = rule.get("ext", "png").lower()

        if not target_dir or not os.path.isdir(target_dir):
            continue

        try:
            # Extract original filename without extension
            base_name = os.path.basename(params.filename)
            file_no_ext = os.path.splitext(base_name)[0]

            # Use Forge's internal save_image to ensure metadata is injected
            images.save_image(
                params.image, 
                target_dir, 
                "", 
                extension=target_ext, 
                forced_filename=file_no_ext,
                info=gen_info  # Now using our safely retrieved gen_info
            )
        except Exception as e:
            print(f"[Mirror Manager] Failed to mirror to {target_dir}: {e}")
def on_ui_tabs():
    with gr.Blocks() as mirror_ui:
        gr.Markdown("### 📂 Image Mirror Manager")
        gr.Markdown("Configure additional locations to save your generations automatically.")
        
        rules_state = gr.State(load_rules())

        with gr.Column() as list_container:
            @gr.render(inputs=rules_state)
            def render_rules(current_rules):
                new_rules = []
                for i, rule in enumerate(current_rules):
                    with gr.Row(variant="compact"):
                        active = gr.Checkbox(value=rule.get("active", True), label="Active", scale=0)
                        path = gr.Textbox(
                            value=rule.get("path", ""), 
                            label="Target Folder", 
                            placeholder="/home/user/Downloads",
                            scale=3
                        )
                        ext = gr.Dropdown(
                            choices=["png", "webp", "jpg", "jpeg"], 
                            value=rule.get("ext", "png"), 
                            label="Format",
                            scale=1
                        )
                        remove_btn = gr.Button("🗑️", variant="tool", scale=0)
                        
                        # Pack them into a dict for the state
                        rule_data = {"active": active, "path": path, "ext": ext, "id": i}
                        new_rules.append(rule_data)

                        def make_remove(idx):
                            def remove():
                                curr = load_rules()
                                curr.pop(idx)
                                save_rules(curr)
                                return curr
                            return remove
                        
                        remove_btn.click(fn=make_remove(i), outputs=rules_state)

                with gr.Row():
                    add_btn = gr.Button("➕ Add New Mirror Path", variant="secondary")
                    save_btn = gr.Button("💾 Save Configuration", variant="primary")

                def add_rule(curr):
                    curr.append({"active": True, "path": "", "ext": "png"})
                    save_rules(curr)
                    return curr

                def bulk_save(*args):
                    # args will be [active1, path1, ext1, active2, path2, ext2...]
                    formatted_rules = []
                    for i in range(0, len(args), 3):
                        formatted_rules.append({
                            "active": args[i],
                            "path": args[i+1],
                            "ext": args[i+2]
                        })
                    save_rules(formatted_rules)
                    gr.Info("Mirror rules saved successfully!")
                    return formatted_rules

                add_btn.click(fn=add_rule, inputs=[rules_state], outputs=rules_state)
                
                # Dynamic binding for the Save button
                save_inputs = []
                for r in new_rules:
                    save_inputs.extend([r["active"], r["path"], r["ext"]])
                
                if save_inputs:
                    save_btn.click(fn=bulk_save, inputs=save_inputs, outputs=rules_state)

    return [(mirror_ui, "Mirror Manager", "mirror_manager_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
script_callbacks.on_image_saved(on_image_saved)