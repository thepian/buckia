"""
PDF Design System Analysis Module

This module provides comprehensive analysis of PDF documents to extract design tokens,
validate design system compliance, and generate quality reports.

Based on the framework defined in docs/pdf-design-system-analysis.md
"""

import json
import logging
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger("buckia.pdf_analysis")

# Optional dependencies for enhanced analysis
try:
    import PyPDF2

    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


@dataclass
class DesignToken:
    """Represents a single design token"""

    name: str
    value: str
    category: str
    description: str = ""
    unit: str = ""
    source: str = ""


@dataclass
class DesignTokens:
    """Collection of design tokens organized by category"""

    typography: Dict[str, DesignToken] = field(default_factory=dict)
    colors: Dict[str, DesignToken] = field(default_factory=dict)
    spacing: Dict[str, DesignToken] = field(default_factory=dict)
    layout: Dict[str, DesignToken] = field(default_factory=dict)
    components: Dict[str, DesignToken] = field(default_factory=dict)

    def merge(self, other: "DesignTokens") -> None:
        """Merge another DesignTokens instance into this one"""
        self.typography.update(other.typography)
        self.colors.update(other.colors)
        self.spacing.update(other.spacing)
        self.layout.update(other.layout)
        self.components.update(other.components)

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert to dictionary format"""
        return {
            "typography": {
                k: {"value": v.value, "description": v.description, "unit": v.unit}
                for k, v in self.typography.items()
            },
            "colors": {
                k: {"value": v.value, "description": v.description} for k, v in self.colors.items()
            },
            "spacing": {
                k: {"value": v.value, "description": v.description, "unit": v.unit}
                for k, v in self.spacing.items()
            },
            "layout": {
                k: {"value": v.value, "description": v.description, "unit": v.unit}
                for k, v in self.layout.items()
            },
            "components": {
                k: {"value": v.value, "description": v.description}
                for k, v in self.components.items()
            },
        }


@dataclass
class ValidationIssue:
    """Represents a validation issue"""

    category: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    token_name: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None


@dataclass
class ValidationResult:
    """Results of design system validation"""

    overall_score: float
    category_scores: Dict[str, float] = field(default_factory=dict)
    issues: List[ValidationIssue] = field(default_factory=list)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue"""
        self.issues.append(issue)

    def get_issues_by_severity(self, severity: str) -> List[ValidationIssue]:
        """Get issues filtered by severity"""
        return [issue for issue in self.issues if issue.severity == severity]


@dataclass
class AnalysisResult:
    """Complete analysis result"""

    tokens: DesignTokens
    validation: ValidationResult
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)


class TypographyExtractor:
    """Extract typography-related design tokens"""

    def extract(self, html_content: str) -> DesignTokens:
        """Extract typography tokens from HTML/CSS content"""
        tokens = DesignTokens()

        # Extract font families
        font_families = self._extract_font_families(html_content)
        for i, font in enumerate(font_families):
            token_name = f"font-family-{i+1}" if i > 0 else "font-family-primary"
            tokens.typography[token_name] = DesignToken(
                name=token_name,
                value=font,
                category="typography",
                description=f"Font family {i+1}",
                source="CSS analysis",
            )

        # Extract font sizes
        font_sizes = self._extract_font_sizes(html_content)
        for size_name, size_value in font_sizes.items():
            tokens.typography[size_name] = DesignToken(
                name=size_name,
                value=size_value,
                category="typography",
                description=f"Font size for {size_name}",
                unit=self._extract_unit(size_value),
                source="CSS analysis",
            )

        # Extract line heights
        line_heights = self._extract_line_heights(html_content)
        for lh_name, lh_value in line_heights.items():
            tokens.typography[lh_name] = DesignToken(
                name=lh_name,
                value=lh_value,
                category="typography",
                description=f"Line height for {lh_name}",
                unit=self._extract_unit(lh_value),
                source="CSS analysis",
            )

        return tokens

    def _extract_font_families(self, html_content: str) -> List[str]:
        """Extract unique font families"""
        pattern = r"font-family[^:]*:\s*([^;}]+)"
        matches = re.findall(pattern, html_content, re.IGNORECASE)

        # Clean and deduplicate
        families = []
        for match in matches:
            clean_family = match.strip().strip("\"'").split(",")[0].strip()
            if clean_family and clean_family not in families:
                families.append(clean_family)

        return families

    def _extract_font_sizes(self, html_content: str) -> Dict[str, str]:
        """Extract font sizes with semantic names"""
        pattern = r"--font-size-([^:]+):\s*([^;}]+)"
        matches = re.findall(pattern, html_content, re.IGNORECASE)

        sizes = {}
        for name, value in matches:
            clean_name = f"font-size-{name.strip()}"
            clean_value = value.strip()
            sizes[clean_name] = clean_value

        # Also extract direct font-size declarations
        direct_pattern = r"font-size[^:]*:\s*([^;}]+)"
        direct_matches = re.findall(direct_pattern, html_content, re.IGNORECASE)

        # Categorize common sizes
        common_sizes = {}
        for value in direct_matches:
            clean_value = value.strip()
            if "pt" in clean_value:
                try:
                    size_num = float(clean_value.replace("pt", ""))
                    if size_num <= 10:
                        common_sizes["font-size-small"] = clean_value
                    elif size_num <= 12:
                        common_sizes["font-size-base"] = clean_value
                    elif size_num <= 16:
                        common_sizes["font-size-medium"] = clean_value
                    elif size_num <= 24:
                        common_sizes["font-size-large"] = clean_value
                    else:
                        common_sizes["font-size-xlarge"] = clean_value
                except ValueError:
                    pass

        sizes.update(common_sizes)
        return sizes

    def _extract_line_heights(self, html_content: str) -> Dict[str, str]:
        """Extract line heights with semantic names"""
        pattern = r"--line-height-([^:]+):\s*([^;}]+)"
        matches = re.findall(pattern, html_content, re.IGNORECASE)

        line_heights = {}
        for name, value in matches:
            clean_name = f"line-height-{name.strip()}"
            clean_value = value.strip()
            line_heights[clean_name] = clean_value

        return line_heights

    def _extract_unit(self, value: str) -> str:
        """Extract unit from a CSS value"""
        units = ["px", "pt", "em", "rem", "cm", "mm", "in", "%"]
        for unit in units:
            if unit in value:
                return unit
        return ""


class ColorExtractor:
    """Extract color-related design tokens"""

    def extract(self, html_content: str) -> DesignTokens:
        """Extract color tokens from HTML/CSS content"""
        tokens = DesignTokens()

        # Extract CSS custom properties for colors
        color_vars = self._extract_color_variables(html_content)
        for var_name, color_value in color_vars.items():
            tokens.colors[var_name] = DesignToken(
                name=var_name,
                value=color_value,
                category="colors",
                description=f"Color variable {var_name}",
                source="CSS custom properties",
            )

        # Extract direct color values
        direct_colors = self._extract_direct_colors(html_content)
        for color_name, color_value in direct_colors.items():
            if color_name not in tokens.colors:
                tokens.colors[color_name] = DesignToken(
                    name=color_name,
                    value=color_value,
                    category="colors",
                    description=f"Direct color usage",
                    source="CSS analysis",
                )

        return tokens

    def _extract_color_variables(self, html_content: str) -> Dict[str, str]:
        """Extract CSS custom properties for colors"""
        pattern = r"--([^:]*color[^:]*|accent[^:]*|primary[^:]*|secondary[^:]*):\s*(#[0-9a-fA-F]{3,6}|rgb\([^)]+\)|rgba\([^)]+\))"
        matches = re.findall(pattern, html_content, re.IGNORECASE)

        colors = {}
        for name, value in matches:
            clean_name = name.strip().replace("-", "_")
            colors[f"color_{clean_name}"] = value.strip()

        return colors

    def _extract_direct_colors(self, html_content: str) -> Dict[str, str]:
        """Extract direct color values and categorize them"""
        hex_pattern = r"#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}"
        rgb_pattern = r"rgb\([^)]+\)"
        rgba_pattern = r"rgba\([^)]+\)"

        all_colors = set()
        all_colors.update(re.findall(hex_pattern, html_content))
        all_colors.update(re.findall(rgb_pattern, html_content))
        all_colors.update(re.findall(rgba_pattern, html_content))

        # Categorize common colors
        categorized = {}
        for color in all_colors:
            if self._is_primary_color(color):
                categorized["color_primary"] = color
            elif self._is_text_color(color):
                categorized["color_text"] = color
            elif self._is_background_color(color):
                categorized["color_background"] = color

        return categorized

    def _is_primary_color(self, color: str) -> bool:
        """Check if color appears to be a primary brand color"""
        # Simple heuristic - could be enhanced
        return color.lower() in ["#988aca", "#3182ce"] or "rgb(152, 138, 202)" in color

    def _is_text_color(self, color: str) -> bool:
        """Check if color appears to be a text color"""
        dark_colors = ["#000", "#333", "#2d2d2d", "#393939"]
        return any(dark in color.lower() for dark in dark_colors)

    def _is_background_color(self, color: str) -> bool:
        """Check if color appears to be a background color"""
        light_colors = ["#fff", "#ffffff", "#f8f", "#f0f"]
        return any(light in color.lower() for light in light_colors)


class SpacingExtractor:
    """Extract spacing-related design tokens"""

    def extract(self, html_content: str) -> DesignTokens:
        """Extract spacing tokens from HTML/CSS content"""
        tokens = DesignTokens()

        # Extract spacing variables
        spacing_vars = self._extract_spacing_variables(html_content)
        for var_name, spacing_value in spacing_vars.items():
            tokens.spacing[var_name] = DesignToken(
                name=var_name,
                value=spacing_value,
                category="spacing",
                description=f"Spacing variable {var_name}",
                unit=self._extract_unit(spacing_value),
                source="CSS custom properties",
            )

        # Extract margin and padding patterns
        margin_padding = self._extract_margin_padding(html_content)
        for prop_name, prop_value in margin_padding.items():
            if prop_name not in tokens.spacing:
                tokens.spacing[prop_name] = DesignToken(
                    name=prop_name,
                    value=prop_value,
                    category="spacing",
                    description=f"Common {prop_name} value",
                    unit=self._extract_unit(prop_value),
                    source="CSS analysis",
                )

        return tokens

    def _extract_spacing_variables(self, html_content: str) -> Dict[str, str]:
        """Extract CSS custom properties for spacing"""
        pattern = r"--([^:]*(?:space|spacing|margin|padding|gap)[^:]*):\s*([^;}]+)"
        matches = re.findall(pattern, html_content, re.IGNORECASE)

        spacing = {}
        for name, value in matches:
            clean_name = name.strip().replace("-", "_")
            spacing[f"spacing_{clean_name}"] = value.strip()

        return spacing

    def _extract_margin_padding(self, html_content: str) -> Dict[str, str]:
        """Extract common margin and padding values"""
        patterns = [
            (r"margin[^:]*:\s*([^;}]+)", "margin"),
            (r"padding[^:]*:\s*([^;}]+)", "padding"),
            (r"gap[^:]*:\s*([^;}]+)", "gap"),
        ]

        spacing_values = {}
        for pattern, prop_type in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)

            # Count frequency and pick most common
            value_counts = {}
            for match in matches:
                clean_value = match.strip()
                value_counts[clean_value] = value_counts.get(clean_value, 0) + 1

            if value_counts:
                most_common = max(value_counts.items(), key=lambda x: x[1])
                spacing_values[f"{prop_type}_common"] = most_common[0]

        return spacing_values

    def _extract_unit(self, value: str) -> str:
        """Extract unit from a CSS value"""
        units = ["px", "pt", "em", "rem", "cm", "mm", "in", "%"]
        for unit in units:
            if unit in value:
                return unit
        return ""


class LayoutExtractor:
    """Extract layout-related design tokens"""

    def extract(self, html_content: str) -> DesignTokens:
        """Extract layout tokens from HTML/CSS content"""
        tokens = DesignTokens()

        # Extract page dimensions
        page_info = self._extract_page_info(html_content)
        for prop_name, prop_value in page_info.items():
            tokens.layout[prop_name] = DesignToken(
                name=prop_name,
                value=prop_value,
                category="layout",
                description=f"Page {prop_name}",
                unit=self._extract_unit(prop_value),
                source="@page rules",
            )

        # Extract border and radius values
        border_info = self._extract_border_info(html_content)
        for prop_name, prop_value in border_info.items():
            tokens.layout[prop_name] = DesignToken(
                name=prop_name,
                value=prop_value,
                category="layout",
                description=f"Border {prop_name}",
                unit=self._extract_unit(prop_value),
                source="CSS analysis",
            )

        return tokens

    def _extract_page_info(self, html_content: str) -> Dict[str, str]:
        """Extract page size and margin information"""
        page_info = {}

        # Extract page size
        size_pattern = r"@page[^{]*{[^}]*size:\s*([^;}]+)"
        size_matches = re.findall(size_pattern, html_content, re.IGNORECASE | re.DOTALL)
        if size_matches:
            page_info["page_size"] = size_matches[0].strip()

        # Extract page margins
        margin_pattern = r"@page[^{]*{[^}]*margin:\s*([^;}]+)"
        margin_matches = re.findall(margin_pattern, html_content, re.IGNORECASE | re.DOTALL)
        if margin_matches:
            page_info["page_margin"] = margin_matches[0].strip()

        return page_info

    def _extract_border_info(self, html_content: str) -> Dict[str, str]:
        """Extract border and border-radius information"""
        border_info = {}

        # Extract border-radius values
        radius_pattern = r"border-radius[^:]*:\s*([^;}]+)"
        radius_matches = re.findall(radius_pattern, html_content, re.IGNORECASE)
        if radius_matches:
            # Get most common border-radius
            radius_counts = {}
            for match in radius_matches:
                clean_value = match.strip()
                radius_counts[clean_value] = radius_counts.get(clean_value, 0) + 1

            if radius_counts:
                most_common = max(radius_counts.items(), key=lambda x: x[1])
                border_info["border_radius"] = most_common[0]

        # Extract border-width values
        width_pattern = r"border(?:-width)?[^:]*:\s*([0-9]+(?:\.[0-9]+)?(?:px|pt|em|rem))"
        width_matches = re.findall(width_pattern, html_content, re.IGNORECASE)
        if width_matches:
            # Get most common border width
            width_counts = {}
            for match in width_matches:
                width_counts[match] = width_counts.get(match, 0) + 1

            if width_counts:
                most_common = max(width_counts.items(), key=lambda x: x[1])
                border_info["border_width"] = most_common[0]

        return border_info

    def _extract_unit(self, value: str) -> str:
        """Extract unit from a CSS value"""
        units = ["px", "pt", "em", "rem", "cm", "mm", "in", "%"]
        for unit in units:
            if unit in value:
                return unit
        return ""


class ComponentExtractor:
    """Extract component-related design tokens"""

    def extract(self, html_content: str) -> DesignTokens:
        """Extract component tokens from HTML/CSS content"""
        tokens = DesignTokens()

        # Extract component-specific styling
        components = self._extract_component_styles(html_content)
        for comp_name, comp_value in components.items():
            tokens.components[comp_name] = DesignToken(
                name=comp_name,
                value=comp_value,
                category="components",
                description=f"Component style for {comp_name}",
                source="CSS component analysis",
            )

        return tokens

    def _extract_component_styles(self, html_content: str) -> Dict[str, str]:
        """Extract component-specific styles"""
        components = {}

        # Executive summary styles
        exec_pattern = r"\.executive-summary[^{]*{[^}]*([^}]+)}"
        exec_matches = re.findall(exec_pattern, html_content, re.IGNORECASE | re.DOTALL)
        if exec_matches:
            components["executive_summary_style"] = "defined"

        # Cover page styles
        cover_pattern = r"\.cover-page[^{]*{[^}]*([^}]+)}"
        cover_matches = re.findall(cover_pattern, html_content, re.IGNORECASE | re.DOTALL)
        if cover_matches:
            components["cover_page_style"] = "defined"

        # Table of contents styles
        toc_pattern = r"\.table-of-contents[^{]*{[^}]*([^}]+)}"
        toc_matches = re.findall(toc_pattern, html_content, re.IGNORECASE | re.DOTALL)
        if toc_matches:
            components["table_of_contents_style"] = "defined"

        return components


class PDFAnalyzer:
    """Main PDF analysis engine"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize PDF analyzer with configuration"""
        self.config = config or {}
        self.extractors = [
            TypographyExtractor(),
            ColorExtractor(),
            SpacingExtractor(),
            LayoutExtractor(),
            ComponentExtractor(),
        ]

        logger.debug("Initialized PDF analyzer")

    def analyze_html(self, html_content: str) -> AnalysisResult:
        """Analyze HTML content for design tokens"""
        logger.info("Starting HTML analysis for design tokens")

        # Extract design tokens
        tokens = self._extract_tokens(html_content)

        # Validate tokens (basic validation for now)
        validation = self._validate_tokens(tokens)

        # Calculate quality metrics
        metrics = self._calculate_metrics(tokens, validation)

        # Extract metadata
        metadata = self._extract_metadata(html_content)

        result = AnalysisResult(
            tokens=tokens, validation=validation, metadata=metadata, quality_metrics=metrics
        )

        logger.info(f"Analysis complete. Found {self._count_tokens(tokens)} design tokens")
        return result

    def analyze_pdf_from_url(self, url: str) -> AnalysisResult:
        """Analyze PDF by fetching HTML from URL"""
        import requests

        logger.info(f"Fetching HTML from URL: {url}")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            html_content = response.text

            return self.analyze_html(html_content)

        except requests.RequestException as e:
            logger.error(f"Failed to fetch HTML from URL: {e}")
            raise

    def _extract_tokens(self, html_content: str) -> DesignTokens:
        """Extract all design tokens using available extractors"""
        tokens = DesignTokens()

        for extractor in self.extractors:
            try:
                extractor_tokens = extractor.extract(html_content)
                tokens.merge(extractor_tokens)
                logger.debug(f"Extracted tokens from {extractor.__class__.__name__}")
            except Exception as e:
                logger.warning(f"Failed to extract tokens from {extractor.__class__.__name__}: {e}")

        return tokens

    def _validate_tokens(self, tokens: DesignTokens) -> ValidationResult:
        """Basic validation of extracted tokens"""
        validation = ValidationResult(overall_score=0.0)

        # Count tokens by category
        category_counts = {
            "typography": len(tokens.typography),
            "colors": len(tokens.colors),
            "spacing": len(tokens.spacing),
            "layout": len(tokens.layout),
            "components": len(tokens.components),
        }

        # Calculate scores based on token presence
        total_possible = 52  # Based on our framework
        total_found = sum(category_counts.values())

        validation.overall_score = min(100.0, (total_found / total_possible) * 100)

        # Category-specific scores
        expected_counts = {
            "typography": 12,
            "colors": 8,
            "spacing": 12,
            "layout": 8,
            "components": 12,
        }

        for category, found_count in category_counts.items():
            expected = expected_counts.get(category, 10)
            score = min(100.0, (found_count / expected) * 100)
            validation.category_scores[category] = score

            # Add issues for missing tokens
            if found_count < expected:
                validation.add_issue(
                    ValidationIssue(
                        category=category,
                        severity="warning",
                        message=f"Only {found_count}/{expected} {category} tokens found",
                    )
                )

        return validation

    def _calculate_metrics(
        self, tokens: DesignTokens, validation: ValidationResult
    ) -> Dict[str, float]:
        """Calculate quality metrics"""
        metrics = {}

        # Token completeness
        total_tokens = sum(
            [
                len(tokens.typography),
                len(tokens.colors),
                len(tokens.spacing),
                len(tokens.layout),
                len(tokens.components),
            ]
        )

        metrics["token_completeness"] = min(100.0, (total_tokens / 52) * 100)
        metrics["validation_score"] = validation.overall_score

        # Consistency metrics (simplified)
        metrics["typography_consistency"] = validation.category_scores.get("typography", 0)
        metrics["color_consistency"] = validation.category_scores.get("colors", 0)
        metrics["spacing_consistency"] = validation.category_scores.get("spacing", 0)

        return metrics

    def _extract_metadata(self, html_content: str) -> Dict[str, Any]:
        """Extract document metadata from HTML"""
        metadata = {}

        # Extract title
        title_match = re.search(r"<title>([^<]+)</title>", html_content, re.IGNORECASE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # Extract meta tags
        meta_pattern = r'<meta\s+name="([^"]+)"\s+content="([^"]+)"'
        meta_matches = re.findall(meta_pattern, html_content, re.IGNORECASE)

        for name, content in meta_matches:
            metadata[name.lower().replace("-", "_")] = content

        return metadata

    def _count_tokens(self, tokens: DesignTokens) -> int:
        """Count total number of tokens"""
        return sum(
            [
                len(tokens.typography),
                len(tokens.colors),
                len(tokens.spacing),
                len(tokens.layout),
                len(tokens.components),
            ]
        )


def analyze_pdf_design_tokens(
    html_content: Optional[str] = None,
    url: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> AnalysisResult:
    """
    Convenience function to analyze PDF design tokens

    Args:
        html_content: HTML content to analyze (if provided)
        url: URL to fetch HTML from (if html_content not provided)
        config: Optional configuration for analysis

    Returns:
        AnalysisResult with extracted tokens and validation
    """
    analyzer = PDFAnalyzer(config)

    if html_content:
        return analyzer.analyze_html(html_content)
    elif url:
        return analyzer.analyze_pdf_from_url(url)
    else:
        raise ValueError("Either html_content or url must be provided")
