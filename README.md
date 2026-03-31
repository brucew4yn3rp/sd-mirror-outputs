## Mirror Manager for SD-WebUI Forge
An automation extension for SD-WebUI Forge Classic (and potentially other Forge/A1111-based UIs) that allows you to automatically "mirror" your generated images to multiple directories in different file formats simultaneously.

🌟 The Problem it Solves
If you save your primary generations in one drive, but frequently need the same or other file extension versions in other folder(s) for easy use, this extension automates that entire workflow.

🚀 Features
Multi-Path Mirroring: Add as many target directories as you want.

Format Conversion: Save the "mirror" copy as PNG, WebP, or JPG, regardless of your main UI settings.

Metadata Preservation: Uses Forge's internal saving engine to ensure Prompts, Seed, and Sampler data are embedded in the mirror copies.

Native Linux Support: Works perfectly with Linux file paths (e.g., /home/user/Downloads).

Persistent Rules: Configuration is saved to an automatically generated mirror_rules.json file (which is also saved in the Scripts folder), so your settings persist across restarts.

Modern UI: A dedicated tab with a reactive Gradio interface for adding, removing, and toggling rules.

🛠️ Installation
1. Navigate to your Forge installation folder.
2. Go to extensions/sd-webui-forge-classic/scripts/ (or your preferred extensions/scripts directory).
3. Download the file `mirror_manager.py` code into that directory and save.
4. Restart your Forge WebUI.

📖 How to Use
1. Configure your Rules
- Open the WebUI and look for the Mirror Manager tab at the top.
- Click ➕ Add New Mirror Path.
- Target Folder: Enter the absolute path to where you want the extra copy (e.g., /home/username/Downloads).
- Format: Select your desired extension for each filepath.
- Click 💾 Save Configuration.

2. Generate Images
- Proceed to use txt2img or img2img as normal.
- Your "Master" file will be saved to your default output folder (defined in Settings).
- A "Mirror" file will instantly appear in your specified folders as soon as the generation finishes.

📝 Configuration File
- The settings are stored in scripts/mirror_rules.json. If you ever need to bulk-edit your paths or back up your configuration, you can edit this file directly.
