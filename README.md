# SmartIR Code Aggregator

**The single source of truth for IR/RF device codes.**

Aggregates and converts IR codes from multiple sources (SmartIR, IRDB, Flipper) into a unified SmartIR-compatible database.

## 🎯 Purpose

This repository serves as the **definitive IR/RF code database** for Broadlink Manager and Home Assistant. It aggregates codes from multiple open-source databases, converts them to SmartIR JSON format, and provides a unified index for fast lookups.

## 📊 Supported Sources

| Source | Devices | Format | License | Status |
|--------|---------|--------|---------|--------|
| [SmartIR](https://github.com/smartHomeHub/SmartIR) | 435 | SmartIR JSON | MIT | ✅ Supported |
| [Flipper IRDB](https://github.com/Lucaslhm/Flipper-IRDB) | 252 | Raw IR | CC0 | ✅ Supported |
| **Total** | **687** | **Mixed** | **Open Source** | **✅ Working** |
| [IRDB](https://github.com/probonopd/irdb) | 10,000+ | Protocol Defs | Public Domain | ⏸️ Future (requires protocol encoder) |
| LIRC | 2,500+ | LIRC | GPL | 🔜 Planned |

## 🚀 Quick Start

### One-Command Build

```bash
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

# Build complete database (all sources)
python scripts/build_database.py
```

That's it! This single command will:
1. ✅ Fetch SmartIR codes (435 devices)
2. ✅ Convert Flipper codes (252 devices)
3. ✅ Organize into unified structure
4. ✅ Generate device index
5. ✅ **Total: 687 devices ready to use!**

### Installation Only

```bash
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

### Aggregate SmartIR Codes

```bash
python scripts/aggregate_all.py --source smartir
```


### Aggregate Flipper Codes

```bash
python scripts/aggregate_all.py --source flipper --category TVs
```

### Aggregate All Sources

```bash
python scripts/aggregate_all.py --all
```

### Generate Index

```bash
python scripts/generate_index.py
```

## ⚙️ Advanced Options

### Build with Options

```bash
# Clean build (remove previous output)
python scripts/build_database.py --clean

# Skip specific sources
python scripts/build_database.py --skip-flipper
python scripts/build_database.py --skip-smartir

# Combine options
python scripts/build_database.py --clean --skip-flipper
```

### Individual Source Aggregation

```bash
# SmartIR only
python scripts/aggregate_all.py --source smartir

# Flipper only (specific category)
python scripts/aggregate_all.py --source flipper --category TVs
```

## 📝 Output Format

All codes are converted to SmartIR JSON format:

```json
{
  "manufacturer": "Samsung",
  "supportedModels": ["UE40F6500"],
  "supportedController": "Broadlink",
  "commandsEncoding": "Base64",
  "commands": {
    "power": "JgBQAAA...",
    "volumeUp": "JgBQAAA...",
    "volumeDown": "JgBQAAA..."
  }
}
```

## ⚠️ IRDB Status

**IRDB is not currently supported** because it uses protocol definitions (NEC, RC5, Sony, etc.) rather than raw IR codes. Supporting IRDB would require:
- Protocol encoder (like IrpTransmogrifier)
- Understanding 100+ IR protocols
- Complex encoding logic

This is planned for future development. For now, we have **687 working devices** from SmartIR + Flipper!

## 📚 Documentation

- [Flipper Converter](docs/FLIPPER_CONVERTER.md) - Flipper .ir file processing
- [SmartIR Format](docs/SMARTIR_FORMAT.md) - Output format specification

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT License - See LICENSE file

## 🙏 Attribution

This project aggregates codes from:
- **SmartIR**: MIT License (original 435 devices)
- **Flipper IRDB**: CC0 (Public Domain) (252 converted devices), Copyright (c) 2019 Vassilis Panos
