from pathlib import Path
import re
source=Path('compact_ui.py').read_text()
assert not re.search(r'[^{}]*google_drive_auth[^{}]*\{[^{}]*display\s*:\s*none',source)
bridge=Path('drive_authorization/index.html').read_text()
assert "a.mode==='login'" in bridge and "height:66" in bridge
assert "height:0" in bridge
print('PASS Google login iframe is not hidden; silent auth keeps zero-height frame')
