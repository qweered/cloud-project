
# Script to render PlantUML diagrams to PNG

echo "Rendering PlantUML diagrams..."

# Create output directory
mkdir -p docs/diagrams/rendered

# Check if PlantUML is installed
if ! command -v plantuml &> /dev/null; then
    echo "PlantUML not found. Please install it first:"
    echo "  - Option 1: Install Java and download plantuml.jar"
    echo "  - Option 2: Use Docker: docker run --rm -v $(pwd):/workspace -w /workspace ghcr.io/plantuml/plantuml diagrams/*.puml"
    exit 1
fi

# Render each diagram
for diagram in docs/diagrams/*.puml; do
    echo "Rendering $diagram..."
    plantuml -tpng -o rendered "$diagram"
done

echo "Diagrams rendered successfully to docs/diagrams/rendered/" 