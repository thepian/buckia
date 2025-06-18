# Buckia PDF Analysis Extension

## 🎯 **Overview**

This document defines how to extend Buckia to support comprehensive PDF analysis capabilities, including design token extraction, quality assessment, and compliance validation for whitepaper generation workflows.

## 📋 **Extension Architecture**

### **Core Components**

```
buckia/
├── pdf/
│   ├── __init__.py
│   ├── analyzer.py          # Main analysis engine
│   ├── extractors/
│   │   ├── typography.py    # Font and text analysis
│   │   ├── colors.py        # Color extraction
│   │   ├── spacing.py       # Layout and spacing
│   │   ├── metadata.py      # Document metadata
│   │   └── images.py        # Image analysis
│   ├── validators/
│   │   ├── design_system.py # Design system compliance
│   │   ├── accessibility.py # WCAG compliance
│   │   └── quality.py       # Quality metrics
│   ├── reporters/
│   │   ├── json_reporter.py # JSON output
│   │   ├── markdown_reporter.py # Markdown reports
│   │   └── html_reporter.py # Interactive reports
│   └── cli.py               # Command-line interface
```

### **Command Structure**

```bash
# Primary analysis command
buckia pdf analyze <input.pdf> [options]

# Specialized extraction commands
buckia pdf extract-tokens <input.pdf> [options]
buckia pdf extract-metadata <input.pdf> [options]
buckia pdf extract-colors <input.pdf> [options]

# Validation commands
buckia pdf validate <input.pdf> --design-system <tokens.json>
buckia pdf validate-accessibility <input.pdf>
buckia pdf validate-brand <input.pdf> --brand-config <config.yaml>

# Reporting commands
buckia pdf report <input.pdf> --format [json|markdown|html]
buckia pdf compare <pdf1.pdf> <pdf2.pdf>
buckia pdf benchmark <input.pdf> --baseline <baseline.json>
```

## 🔧 **Implementation Specifications**

### **1. Core Analyzer Class**

```python
class PDFAnalyzer:
    """Main PDF analysis engine"""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.extractors = self._load_extractors()
        self.validators = self._load_validators()
        
    def analyze(self, pdf_path: str) -> AnalysisResult:
        """Perform comprehensive PDF analysis"""
        # Load PDF document
        doc = self._load_pdf(pdf_path)
        
        # Extract design tokens
        tokens = self._extract_tokens(doc)
        
        # Validate against standards
        validation = self._validate(tokens)
        
        # Generate quality metrics
        metrics = self._calculate_metrics(tokens, validation)
        
        return AnalysisResult(tokens, validation, metrics)
    
    def _extract_tokens(self, doc) -> DesignTokens:
        """Extract all design tokens from PDF"""
        tokens = DesignTokens()
        
        for extractor in self.extractors:
            extractor_tokens = extractor.extract(doc)
            tokens.merge(extractor_tokens)
            
        return tokens
```

### **2. Design Token Extraction**

```python
class TypographyExtractor:
    """Extract typography-related design tokens"""
    
    def extract(self, doc) -> Dict[str, Any]:
        """Extract typography tokens"""
        tokens = {}
        
        # Font families
        fonts = self._extract_fonts(doc)
        tokens['font-families'] = fonts
        
        # Font sizes
        sizes = self._extract_font_sizes(doc)
        tokens['font-sizes'] = sizes
        
        # Line heights
        line_heights = self._extract_line_heights(doc)
        tokens['line-heights'] = line_heights
        
        return tokens
    
    def _extract_fonts(self, doc) -> List[str]:
        """Extract unique font families used"""
        fonts = set()
        for page in doc:
            for text_block in page.get_text_blocks():
                font_info = text_block.get_font_info()
                fonts.add(font_info.family)
        return list(fonts)
```

### **3. Color Analysis**

```python
class ColorExtractor:
    """Extract color-related design tokens"""
    
    def extract(self, doc) -> Dict[str, Any]:
        """Extract color tokens"""
        tokens = {}
        
        # Text colors
        text_colors = self._extract_text_colors(doc)
        tokens['text-colors'] = text_colors
        
        # Background colors
        bg_colors = self._extract_background_colors(doc)
        tokens['background-colors'] = bg_colors
        
        # Border colors
        border_colors = self._extract_border_colors(doc)
        tokens['border-colors'] = border_colors
        
        return tokens
    
    def _extract_text_colors(self, doc) -> List[str]:
        """Extract unique text colors"""
        colors = set()
        for page in doc:
            for text_span in page.get_text_spans():
                color = text_span.get_color()
                colors.add(self._normalize_color(color))
        return list(colors)
```

### **4. Validation Framework**

```python
class DesignSystemValidator:
    """Validate PDF against design system standards"""
    
    def __init__(self, design_system: DesignSystem):
        self.design_system = design_system
        
    def validate(self, tokens: DesignTokens) -> ValidationResult:
        """Validate extracted tokens against design system"""
        results = ValidationResult()
        
        # Typography validation
        typo_result = self._validate_typography(tokens.typography)
        results.add_category('typography', typo_result)
        
        # Color validation
        color_result = self._validate_colors(tokens.colors)
        results.add_category('colors', color_result)
        
        # Spacing validation
        spacing_result = self._validate_spacing(tokens.spacing)
        results.add_category('spacing', spacing_result)
        
        return results
    
    def _validate_typography(self, typography: Dict) -> CategoryResult:
        """Validate typography tokens"""
        issues = []
        
        # Check font families
        allowed_fonts = self.design_system.typography.font_families
        for font in typography.get('font-families', []):
            if font not in allowed_fonts:
                issues.append(f"Unauthorized font: {font}")
        
        # Check font sizes
        allowed_sizes = self.design_system.typography.font_sizes
        for size in typography.get('font-sizes', []):
            if not self._is_size_allowed(size, allowed_sizes):
                issues.append(f"Non-standard font size: {size}")
        
        return CategoryResult('typography', issues)
```

## 📊 **Output Formats**

### **JSON Token Export**
```json
{
  "metadata": {
    "analyzed_at": "2024-06-16T20:00:00Z",
    "pdf_path": "whitepaper.pdf",
    "analyzer_version": "1.0.0"
  },
  "tokens": {
    "typography": {
      "font-family-primary": "Inter",
      "font-family-heading": "Playfair Display",
      "font-size-base": "11pt",
      "font-size-h1": "32pt",
      "line-height-base": "1.6"
    },
    "colors": {
      "color-primary": "#988aca",
      "color-text-primary": "#393939",
      "color-background": "#ffffff"
    },
    "spacing": {
      "margin-page": "2.5cm",
      "padding-container": "1cm",
      "spacing-section": "2cm"
    }
  },
  "validation": {
    "overall_score": 85,
    "categories": {
      "typography": {"score": 90, "issues": []},
      "colors": {"score": 95, "issues": []},
      "spacing": {"score": 70, "issues": ["Inconsistent margins"]}
    }
  }
}
```

### **Markdown Report**
```markdown
# PDF Analysis Report

## Executive Summary
- **Overall Quality Score:** 85/100
- **Design System Compliance:** 90%
- **Accessibility Score:** 95%
- **Critical Issues:** 2

## Typography Analysis
✅ **Font Consistency:** Excellent
✅ **Size Hierarchy:** Well-defined
⚠️ **Line Height:** Some inconsistencies

## Recommendations
1. Standardize line heights across sections
2. Reduce excessive spacing in executive summary
3. Ensure consistent color usage for callouts
```
