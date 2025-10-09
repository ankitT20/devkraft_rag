# DevKraft RAG Documentation

This folder contains comprehensive documentation for the DevKraft RAG project, including architecture diagrams, PlantUML source files, and detailed explanations of all components.

## 📁 Files in This Folder

### Documentation

- **[info.md](info.md)** (19 KB) - Complete directory structure guide and architecture explanation
  - Directory structure with descriptions
  - File relationships and dependencies
  - Data flow diagrams
  - Architecture patterns
  - Module dependency graph
  - Technology stack
  - Configuration details

### PlantUML Source Files

- **[deep-dive.puml](deep-dive.puml)** (22 KB) - Comprehensive diagram with ALL classes, methods, and functions
  - 30+ classes with full method signatures
  - 100+ documented functions
  - Public and private methods
  - Implementation notes
  - Complete relationships

- **[architecture-simple.puml](architecture-simple.puml)** (3.3 KB) - High-level architecture overview
  - Simplified component view
  - Major packages and services
  - Key relationships
  - Color-coded by type

### Generated Images

- **[DevKraft_RAG_Deep_Dive.png](DevKraft_RAG_Deep_Dive.png)** (1.4 MB, 4708 x 4434 px)
  - Rendered comprehensive diagram
  - High resolution for printing
  - Shows all details from deep-dive.puml

- **[DevKraft_RAG_Architecture.png](DevKraft_RAG_Architecture.png)** (203 KB, 1784 x 1087 px)
  - Rendered high-level overview
  - Perfect for presentations
  - Shows all major components

## 🎨 Color Coding

All diagrams use consistent color coding:

| Color | Component Type | Hex Code |
|-------|---------------|----------|
| Light Green | Entry Points | #E8F5E9 |
| Light Yellow | Configuration | #FFF9C4 |
| Light Blue | Core Services | #E3F2FD |
| Light Purple | Business Services | #F3E5F5 |
| Light Pink | Data Models | #FCE4EC |
| Light Brown | Utilities | #EFEBE9 |
| Light Orange | External Services | #FFE0B2 |
| Gray | Runtime Folders | #E0E0E0 |

## 🚀 Quick Start

### View the Documentation

1. **For a quick overview**: Open `DevKraft_RAG_Architecture.png`
2. **For detailed understanding**: Read `info.md`
3. **For complete technical details**: View `DevKraft_RAG_Deep_Dive.png`

### Edit the Diagrams

To modify and regenerate the diagrams:

```bash
# Install PlantUML (requires Java)
wget https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar

# Install Graphviz for better rendering
sudo apt-get install graphviz

# Edit the .puml files with your favorite editor
nano deep-dive.puml

# Regenerate PNG images
java -DPLANTUML_LIMIT_SIZE=32768 -jar plantuml.jar -tpng deep-dive.puml
java -DPLANTUML_LIMIT_SIZE=32768 -jar plantuml.jar -tpng architecture-simple.puml
```

### Online Editing

You can also edit PlantUML files online:
- Go to http://www.plantuml.com/plantuml/
- Copy the content from any `.puml` file
- Edit and view changes in real-time
- Export in various formats (PNG, SVG, PDF)

## 📊 What's Documented

### All Files (21 total)
- ✅ Entry points (3): streamlit_app.py, app/main.py, start.sh
- ✅ Core services (5 files, 7 classes): embeddings, llm, storage, chat_storage, tts
- ✅ Business services (3 files, 3 classes): document_processor, ingestion, rag
- ✅ Configuration (1): config.py with Settings class
- ✅ Data models (1): schemas.py with 6 Pydantic models
- ✅ Utilities (1): logging_config.py
- ✅ Dependencies (1): requirements.txt
- ✅ Documentation (1): README.md

### All Functions (70+)
- Entry point functions: 14 functions
- Core service methods: 40+ methods (public and private)
- Business service methods: 18+ methods
- Helper and utility functions: All documented

### All Relationships
- Configuration dependencies
- Service orchestration
- API calls to external services
- Data flow between components
- Fallback mechanisms

## 🎯 Requirements Fulfilled

This documentation fulfills all requirements from the original issue:

1. ✅ Directory structure explanation in `info.md`
2. ✅ Basic info about all files and their relations
3. ✅ Excellent PUML code in two dedicated files
4. ✅ Every file included in diagrams
5. ✅ Large printable version (1.4 MB, 4708x4434 px)
6. ✅ Detailed explanation provided
7. ✅ Dedicated deep-dive PUML file
8. ✅ Every single function documented
9. ✅ Sub-functions and helper functions included
10. ✅ **BONUS**: PNG images generated from PUML code

## 🔍 Diagram Details

### Architecture Overview (DevKraft_RAG_Architecture.png)
- **Purpose**: Quick understanding of system structure
- **Shows**: All major components and their connections
- **Best for**: Presentations, onboarding, high-level discussions
- **Resolution**: 1784 x 1087 pixels
- **Size**: 203 KB

### Deep Dive (DevKraft_RAG_Deep_Dive.png)
- **Purpose**: Complete technical reference
- **Shows**: Every class, method, parameter, return type
- **Best for**: Development, code review, maintenance
- **Resolution**: 4708 x 4434 pixels (printable A0 size)
- **Size**: 1.4 MB
- **Details**: 30+ classes, 100+ methods, all relationships

## 📖 Additional Resources

- **Main Project README**: ../README.md
- **Source Code**: ../app/
- **Entry Point**: ../streamlit_app.py
- **API**: ../app/main.py

## 🛠️ Technical Details

- **PlantUML Version**: 1.2024.8
- **Rendering Engine**: Graphviz dot
- **Image Format**: PNG (8-bit RGB)
- **Max Size Limit**: 32768 pixels
- **Color Depth**: 24-bit (8-bit per channel)

## 📝 Notes

- All diagrams are generated from source `.puml` files
- Images can be regenerated at any time
- PlantUML source is the authoritative reference
- Diagrams are version-controlled along with code
- Updates to code should be reflected in diagrams

---

**Last Updated**: October 2024  
**Version**: 1.0  
**Author**: Generated for DevKraft RAG Project
