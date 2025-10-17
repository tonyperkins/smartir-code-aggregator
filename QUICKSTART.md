# Quick Start Guide

Get started with SmartIR Code Aggregator in 5 minutes.

## 🎯 TL;DR - One Command

```bash
python scripts/build_database.py
```

This builds the complete database from all sources!

## Installation

```bash
# Clone repository
git clone https://github.com/tonyperkins/smartir-code-aggregator.git
cd smartir-code-aggregator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

### Convert TV Codes from IRDB

```bash
python scripts/aggregate_all.py --source irdb --category TV
```

This will:
1. Clone IRDB repository to `~/.cache/smartir-aggregator/irdb/`
2. Convert all TV codes from Pronto to Broadlink format
3. Save SmartIR JSON files to `output/codes/irdb/tv/`

### Convert TV Codes from Flipper

```bash
python scripts/aggregate_all.py --source flipper --category TVs
```

This will:
1. Clone Flipper IRDB to `~/.cache/smartir-aggregator/flipper/`
2. Convert all TV codes from raw format to Broadlink
3. Save SmartIR JSON files to `output/codes/flipper/tvs/`

### Convert All Sources

```bash
python scripts/aggregate_all.py --all
```

This processes all categories from both IRDB and Flipper IRDB.

## Output Structure

```
output/
└── codes/
    ├── irdb/
    │   ├── tv/
    │   │   ├── Samsung_UE40F6500.json
    │   │   ├── LG_22MT47DC.json
    │   │   └── ...
    │   ├── air_conditioner/
    │   └── fan/
    └── flipper/
        ├── tvs/
        ├── acs/
        └── fans/
```

## Example Output

```json
{
  "manufacturer": "Samsung",
  "supportedModels": ["UE40F6500"],
  "supportedController": "Broadlink",
  "commandsEncoding": "Base64",
  "commands": {
    "power": "JgBQAAABJQAVABUA...",
    "volume_up": "JgBQAAABJQAVABUA...",
    "volume_down": "JgBQAAABJQAVABUA...",
    "mute": "JgBQAAABJQAVABUA..."
  }
}
```

## Next Steps

1. **Review converted files** in `output/codes/`
2. **Copy to your fork**: `cp output/codes/* ../smartir-device-database/codes/`
3. **Generate index**: `cd ../smartir-device-database && python scripts/generate_device_index.py`
4. **Commit and push** to your repository

## Available Categories

### IRDB
- TV
- DVD
- Blu-ray
- Receiver
- Amplifier
- Air_Conditioner
- Fan

### Flipper IRDB
- TVs
- ACs
- Fans
- Audio_Receivers
- Projectors

## Troubleshooting

### Git not found
Install Git: https://git-scm.com/downloads

### Conversion failures
Some codes may fail to convert due to:
- Invalid Pronto format
- Unsupported protocols
- Corrupted data

Check the console output for specific errors.

### Low success rate
This is normal! Not all codes in IRDB/Flipper are compatible with Broadlink.
Typical success rates:
- IRDB: 60-80%
- Flipper: 70-90%

## Advanced Usage

### Custom output directory
```bash
python scripts/aggregate_all.py --output /path/to/output
```

### Validate converted files
```python
from validators.validate_smartir import SmartIRValidator

validator = SmartIRValidator()
results = validator.batch_validate(Path("output/codes/irdb/tv"))
validator.print_results(results)
```

### Convert single device
```python
from converters.irdb import IRDBConverter

converter = IRDBConverter()
device = converter.convert_device(
    manufacturer="Samsung",
    model="UE40F6500",
    csv_path=Path("path/to/samsung.csv"),
    category="TV"
)
```

## Support

- **Issues**: https://github.com/tonyperkins/smartir-code-aggregator/issues
- **Discussions**: https://github.com/tonyperkins/smartir-code-aggregator/discussions
