#!/bin/bash

# Documentation Cleanup Script
# Removes redundant documentation files as outlined in docs/DOCUMENTATION_CONSOLIDATION.md

set -e

echo "🧹 Starting documentation cleanup..."
echo "📋 See docs/DOCUMENTATION_CONSOLIDATION.md for details"

# Create archive directory
echo "📁 Creating archive directory..."
mkdir -p archive/docs/content/
mkdir -p archive/src/

# Phase 1: Remove redundant PDF documentation
echo "🗑️  Removing redundant PDF documentation..."
if [ -f "docs/pdf-generation.md" ]; then
    rm docs/pdf-generation.md
    echo "   ✅ Removed docs/pdf-generation.md"
fi

if [ -f "docs/pdf-generation-clean.md" ]; then
    rm docs/pdf-generation-clean.md
    echo "   ✅ Removed docs/pdf-generation-clean.md"
fi

if [ -f "docs/pdf-screen-print-consistency.md" ]; then
    rm docs/pdf-screen-print-consistency.md
    echo "   ✅ Removed docs/pdf-screen-print-consistency.md"
fi

# Phase 2: Remove outdated development guides
echo "🗑️  Removing outdated development guides..."
if [ -f "docs/local-api-development.md" ]; then
    rm docs/local-api-development.md
    echo "   ✅ Removed docs/local-api-development.md"
fi

if [ -f "docs/development-permission-issues.md" ]; then
    rm docs/development-permission-issues.md
    echo "   ✅ Removed docs/development-permission-issues.md"
fi

if [ -f "docs/network-development-setup.md" ]; then
    rm docs/network-development-setup.md
    echo "   ✅ Removed docs/network-development-setup.md"
fi

# Phase 3: Remove redundant testing documentation
echo "🗑️  Removing redundant testing documentation..."
if [ -f "tests/auth/README-live-integration.md" ]; then
    rm tests/auth/README-live-integration.md
    echo "   ✅ Removed tests/auth/README-live-integration.md"
fi

# Phase 4: Archive historical content
echo "📦 Archiving historical content..."
if [ -d "src/archive" ]; then
    mv src/archive/ archive/src/
    echo "   ✅ Archived src/archive/ to archive/src/"
fi

# Phase 5: Count remaining documentation
echo "📊 Documentation cleanup summary:"
total_md_files=$(find . -name "*.md" -not -path "./node_modules/*" -not -path "./archive/*" | wc -l)
echo "   📄 Total .md files remaining: $total_md_files"

archived_files=$(find archive/ -name "*.md" 2>/dev/null | wc -l || echo "0")
echo "   📦 Files archived: $archived_files"

echo ""
echo "🎉 Documentation cleanup completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Review the changes with: git status"
echo "   2. Test documentation links for broken references"
echo "   3. Update any remaining cross-references"
echo "   4. Commit the cleanup: git add . && git commit -m 'docs: consolidate documentation'"
echo ""
echo "📖 See docs/DOCUMENTATION_CONSOLIDATION.md for full details"
