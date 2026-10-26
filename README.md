### ffmpeg qt6 wrapper

**wrapper for ffmpeg written in qt6**

simple wrapper(a program wrapper, for easier use of ffmpeg) for converting media and changing codecs

## dependencies:

python3  
pyqt6  
ffmpeg (needs to be in PATH)

### **small warning**

tested on nixos using "shell.nix" and offscreen qt, nowhere else, haven't checked windows

## running:

.venv(install ffmpeg separately, on nixos use nix-shell below):

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pyqt6
python main.py
```

fish: `source .venv/bin/activate.fish`

nix-shell(no .venv needed):

```sh
nix-shell --run 'python3 main.py'
```

