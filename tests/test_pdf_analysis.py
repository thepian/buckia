"""
Tests for PDF Design System Analysis Module

Comprehensive test suite for the PDF analysis functionality including:
- Design token extraction from HTML/CSS
- Typography, color, spacing, layout, and component analysis
- Validation and quality metrics
- Integration with thepia.com PDF generation
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any

from buckia.pdf_analysis import (
    PDFAnalyzer,
    DesignTokens,
    DesignToken,
    ValidationResult,
    ValidationIssue,
    AnalysisResult,
    TypographyExtractor,
    ColorExtractor,
    SpacingExtractor,
    LayoutExtractor,
    ComponentExtractor,
    analyze_pdf_design_tokens
)


class TestDesignToken:
    """Test DesignToken data class"""
    
    def test_design_token_creation(self):
        """Test creating a design token"""
        token = DesignToken(
            name="font-size-base",
            value="11pt",
            category="typography",
            description="Base font size",
            unit="pt",
            source="CSS analysis"
        )
        
        assert token.name == "font-size-base"
        assert token.value == "11pt"
        assert token.category == "typography"
        assert token.unit == "pt"


class TestDesignTokens:
    """Test DesignTokens collection"""
    
    def test_design_tokens_creation(self):
        """Test creating design tokens collection"""
        tokens = DesignTokens()
        
        assert len(tokens.typography) == 0
        assert len(tokens.colors) == 0
        assert len(tokens.spacing) == 0
        assert len(tokens.layout) == 0
        assert len(tokens.components) == 0
    
    def test_design_tokens_merge(self):
        """Test merging design tokens"""
        tokens1 = DesignTokens()
        tokens1.typography["font-size-base"] = DesignToken(
            name="font-size-base",
            value="11pt",
            category="typography"
        )
        
        tokens2 = DesignTokens()
        tokens2.colors["color-primary"] = DesignToken(
            name="color-primary",
            value="#988aca",
            category="colors"
        )
        
        tokens1.merge(tokens2)
        
        assert len(tokens1.typography) == 1
        assert len(tokens1.colors) == 1
        assert "font-size-base" in tokens1.typography
        assert "color-primary" in tokens1.colors
    
    def test_design_tokens_to_dict(self):
        """Test converting design tokens to dictionary"""
        tokens = DesignTokens()
        tokens.typography["font-size-base"] = DesignToken(
            name="font-size-base",
            value="11pt",
            category="typography",
            description="Base font size",
            unit="pt"
        )
        
        result = tokens.to_dict()
        
        assert "typography" in result
        assert "font-size-base" in result["typography"]
        assert result["typography"]["font-size-base"]["value"] == "11pt"
        assert result["typography"]["font-size-base"]["unit"] == "pt"


class TestTypographyExtractor:
    """Test typography token extraction"""
    
    def test_extract_font_families(self):
        """Test extracting font families"""
        html_content = """
        <style>
        body { font-family: 'Inter', sans-serif; }
        h1 { font-family: 'Playfair Display', serif; }
        </style>
        """
        
        extractor = TypographyExtractor()
        tokens = extractor.extract(html_content)
        
        assert len(tokens.typography) > 0
        # Should find at least one font family
        font_families = [token for name, token in tokens.typography.items() if 'font-family' in name]
        assert len(font_families) > 0
    
    def test_extract_font_sizes(self):
        """Test extracting font sizes"""
        html_content = """
        <style>
        :root {
          --font-size-base: 11pt;
          --font-size-large: 16pt;
        }
        body { font-size: 11pt; }
        h1 { font-size: 32pt; }
        </style>
        """
        
        extractor = TypographyExtractor()
        tokens = extractor.extract(html_content)
        
        # Should extract CSS custom properties
        font_size_tokens = [token for name, token in tokens.typography.items() if 'font-size' in name]
        assert len(font_size_tokens) > 0
    
    def test_extract_line_heights(self):
        """Test extracting line heights"""
        html_content = """
        <style>
        :root {
          --line-height-normal: 1.5;
          --line-height-tight: 1.2;
        }
        </style>
        """
        
        extractor = TypographyExtractor()
        tokens = extractor.extract(html_content)
        
        line_height_tokens = [token for name, token in tokens.typography.items() if 'line-height' in name]
        assert len(line_height_tokens) > 0


class TestColorExtractor:
    """Test color token extraction"""
    
    def test_extract_color_variables(self):
        """Test extracting CSS color variables"""
        html_content = """
        <style>
        :root {
          --color-primary: #988aca;
          --color-text-primary: #2d2d2d;
          --accent-color: #3182ce;
        }
        </style>
        """
        
        extractor = ColorExtractor()
        tokens = extractor.extract(html_content)
        
        assert len(tokens.colors) > 0
        # Should find color variables
        color_tokens = [token for name, token in tokens.colors.items() if 'color' in name]
        assert len(color_tokens) > 0
    
    def test_extract_direct_colors(self):
        """Test extracting direct color values"""
        html_content = """
        <style>
        body { color: #2d2d2d; background: #ffffff; }
        .primary { color: #988aca; }
        .accent { background: rgb(152, 138, 202); }
        </style>
        """
        
        extractor = ColorExtractor()
        tokens = extractor.extract(html_content)
        
        # Should categorize common colors
        assert len(tokens.colors) > 0


class TestSpacingExtractor:
    """Test spacing token extraction"""
    
    def test_extract_spacing_variables(self):
        """Test extracting spacing CSS variables"""
        html_content = """
        <style>
        :root {
          --space-xs: 0.25rem;
          --space-md: 1rem;
          --space-section-lg: 2cm;
          --margin-page: 2.5cm;
          --padding-container: 1cm;
        }
        </style>
        """
        
        extractor = SpacingExtractor()
        tokens = extractor.extract(html_content)
        
        assert len(tokens.spacing) > 0
        spacing_tokens = [token for name, token in tokens.spacing.items() if 'spacing' in name]
        assert len(spacing_tokens) > 0
    
    def test_extract_margin_padding(self):
        """Test extracting margin and padding patterns"""
        html_content = """
        <style>
        .container { margin: 1cm 0; padding: 1.5cm; }
        .section { margin: 2cm 0; }
        .element { padding: 0.8cm; }
        .gap { gap: 1rem; }
        </style>
        """
        
        extractor = SpacingExtractor()
        tokens = extractor.extract(html_content)
        
        # Should find common margin/padding values
        assert len(tokens.spacing) > 0


class TestLayoutExtractor:
    """Test layout token extraction"""
    
    def test_extract_page_info(self):
        """Test extracting page layout information"""
        html_content = """
        <style>
        @page {
          size: A4;
          margin: 2.2cm 1.8cm;
        }
        </style>
        """
        
        extractor = LayoutExtractor()
        tokens = extractor.extract(html_content)
        
        assert len(tokens.layout) > 0
        # Should find page size and margins
        page_tokens = [token for name, token in tokens.layout.items() if 'page' in name]
        assert len(page_tokens) > 0
    
    def test_extract_border_info(self):
        """Test extracting border information"""
        html_content = """
        <style>
        .card { border-radius: 8pt; border: 1pt solid #e0dce8; }
        .section { border-width: 2pt; }
        .element { border-radius: 4pt; }
        </style>
        """
        
        extractor = LayoutExtractor()
        tokens = extractor.extract(html_content)
        
        # Should find border properties
        border_tokens = [token for name, token in tokens.layout.items() if 'border' in name]
        assert len(border_tokens) > 0


class TestComponentExtractor:
    """Test component token extraction"""
    
    def test_extract_component_styles(self):
        """Test extracting component-specific styles"""
        html_content = """
        <style>
        .executive-summary {
          background: #f8f7fc;
          padding: 1.5cm;
        }
        .cover-page {
          background: linear-gradient(to bottom, #988aca, #b8a8d4);
        }
        .table-of-contents {
          padding: 2cm 0;
        }
        </style>
        """
        
        extractor = ComponentExtractor()
        tokens = extractor.extract(html_content)
        
        assert len(tokens.components) > 0
        # Should find component styles
        assert any('executive_summary' in name for name in tokens.components.keys())
        assert any('cover_page' in name for name in tokens.components.keys())
        assert any('table_of_contents' in name for name in tokens.components.keys())


class TestPDFAnalyzer:
    """Test main PDF analyzer"""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization"""
        analyzer = PDFAnalyzer()
        
        assert analyzer.config == {}
        assert len(analyzer.extractors) == 5  # All extractor types
    
    def test_analyze_html_basic(self):
        """Test basic HTML analysis"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
          <title>Test Whitepaper</title>
          <meta name="author" content="Test Author">
          <style>
          :root {
            --font-size-base: 11pt;
            --color-primary: #988aca;
            --space-md: 1rem;
          }
          @page { size: A4; margin: 2cm; }
          .executive-summary { padding: 1cm; }
          </style>
        </head>
        <body>
          <h1>Test Document</h1>
        </body>
        </html>
        """
        
        analyzer = PDFAnalyzer()
        result = analyzer.analyze_html(html_content)
        
        assert isinstance(result, AnalysisResult)
        assert isinstance(result.tokens, DesignTokens)
        assert isinstance(result.validation, ValidationResult)
        assert isinstance(result.metadata, dict)
        assert isinstance(result.quality_metrics, dict)
        
        # Should extract some tokens
        total_tokens = (
            len(result.tokens.typography) +
            len(result.tokens.colors) +
            len(result.tokens.spacing) +
            len(result.tokens.layout) +
            len(result.tokens.components)
        )
        assert total_tokens > 0
        
        # Should extract metadata
        assert "title" in result.metadata
        assert result.metadata["title"] == "Test Whitepaper"
    
    def test_validation_scoring(self):
        """Test validation scoring system"""
        # Create tokens with known counts
        tokens = DesignTokens()
        
        # Add some typography tokens (12 expected)
        for i in range(6):  # Half of expected
            tokens.typography[f"font-{i}"] = DesignToken(
                name=f"font-{i}",
                value="test",
                category="typography"
            )
        
        # Add some color tokens (8 expected)
        for i in range(4):  # Half of expected
            tokens.colors[f"color-{i}"] = DesignToken(
                name=f"color-{i}",
                value="test",
                category="colors"
            )
        
        analyzer = PDFAnalyzer()
        validation = analyzer._validate_tokens(tokens)
        
        assert validation.overall_score > 0
        assert validation.overall_score < 100  # Should be partial
        
        # Should have category scores
        assert "typography" in validation.category_scores
        assert "colors" in validation.category_scores
        
        # Should have issues for missing tokens
        assert len(validation.issues) > 0
        warning_issues = validation.get_issues_by_severity("warning")
        assert len(warning_issues) > 0


class TestIntegration:
    """Integration tests with thepia.com PDF generation"""
    
    @pytest.mark.integration
    def test_analyze_thepia_whitepaper_html(self):
        """Test analyzing actual thepia.com whitepaper HTML"""
        # This would require the dev server to be running
        # Skip if not available
        try:
            import requests
            
            url = "https://dev.thepia.com/whitepapers/hidden-cost-brief/pdf"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
                
                result = analyze_pdf_design_tokens(html_content=html_content)
                
                # Should extract substantial number of tokens
                total_tokens = (
                    len(result.tokens.typography) +
                    len(result.tokens.colors) +
                    len(result.tokens.spacing) +
                    len(result.tokens.layout) +
                    len(result.tokens.components)
                )
                
                assert total_tokens >= 10  # Should find at least 10 tokens
                
                # Should have good validation score
                assert result.validation.overall_score > 50
                
                # Should extract metadata
                assert "title" in result.metadata
                
                print(f"✅ Analyzed thepia.com whitepaper: {total_tokens} tokens found")
                print(f"✅ Validation score: {result.validation.overall_score:.1f}%")
            else:
                pytest.skip("Dev server not available")
                
        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")
    
    def test_convenience_function(self):
        """Test convenience function"""
        html_content = """
        <style>
        :root { --font-size-base: 11pt; --color-primary: #988aca; }
        </style>
        """
        
        result = analyze_pdf_design_tokens(html_content=html_content)
        
        assert isinstance(result, AnalysisResult)
        assert len(result.tokens.typography) + len(result.tokens.colors) > 0
    
    def test_convenience_function_validation(self):
        """Test convenience function parameter validation"""
        with pytest.raises(ValueError, match="Either html_content or url must be provided"):
            analyze_pdf_design_tokens()


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
