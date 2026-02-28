# WBS

This project captures the secure clinical communication platform implementation as a mind map and exports it as a PDF artifact.

## Repository Layout

- `data/outline.json` — canonical representation of the implementation workstreams.
- `scripts/generate_diagram.py` — utility that converts the outline into a visual diagram.
- `output/` — destination for rendered diagrams (e.g., PDF).

## Getting Started

1. Create (optional) and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.

## Generate the Diagram

Run the helper script to build the mind map and export it as a PDF:

```bash
python scripts/generate_diagram.py
```

The default export path is `output/secure-clinical-communication.pdf`. Use `--output` to override the destination or `--dpi` to change the resolution.

## Data Source

The hierarchical definition of the program is stored in `data/outline.json`. Update that file if the work breakdown structure changes, then rerun the generator script.
