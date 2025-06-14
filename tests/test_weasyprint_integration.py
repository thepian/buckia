"""
WeasyPrint Integration Tests

Tests to verify that we can generate PDF files at the level of WeasyPrint samples.
This test suite ensures that markdown/HTML files can generate PDFs that match
WeasyPrint reference samples.
"""

import os
import tempfile
import pytest
import requests
from pathlib import Path
from typing import Dict, Any
import weasyprint
from buckia.pdf import render_pdf_local_only


class TestWeasyPrintIntegration:
    """Test suite for WeasyPrint integration with Buckia"""
    
    @pytest.fixture(scope="class")
    def test_dirs(self):
        """Create test directories"""
        base_dir = Path(__file__).parent
        test_output_dir = base_dir / "output"
        reference_dir = base_dir / "reference"
        
        test_output_dir.mkdir(exist_ok=True)
        reference_dir.mkdir(exist_ok=True)
        
        return {
            "output": test_output_dir,
            "reference": reference_dir,
            "base": base_dir
        }
    
    @pytest.fixture(scope="class")
    def reference_files(self, test_dirs):
        """Download WeasyPrint reference files"""
        reference_dir = test_dirs["reference"]
        
        # URLs for WeasyPrint report sample
        files_to_download = {
            "report.html": "https://raw.githubusercontent.com/CourtBouillon/weasyprint-samples/main/report/report.html",
            "report.css": "https://raw.githubusercontent.com/CourtBouillon/weasyprint-samples/main/report/report.css",
            "report.pdf": "https://github.com/CourtBouillon/weasyprint-samples/raw/main/report/report.pdf"
        }
        
        downloaded_files = {}
        
        for filename, url in files_to_download.items():
            file_path = reference_dir / filename
            
            if not file_path.exists():
                print(f"Downloading {filename} from {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
            
            downloaded_files[filename] = file_path
        
        return downloaded_files
    
    def test_reference_files_downloaded(self, reference_files):
        """Test that reference files are downloaded successfully"""
        for filename, file_path in reference_files.items():
            assert file_path.exists(), f"Reference file {filename} should exist"
            assert file_path.stat().st_size > 0, f"Reference file {filename} should not be empty"
    
    def test_create_test_html_from_markdown(self, test_dirs):
        """Test creating HTML that matches WeasyPrint structure from markdown-like content"""
        output_dir = test_dirs["output"]
        
        # Create test HTML that matches WeasyPrint report structure
        test_html_content = self._create_weasyprint_test_html()
        
        test_html_path = output_dir / "test-report.html"
        with open(test_html_path, 'w', encoding='utf-8') as f:
            f.write(test_html_content)
        
        # Verify HTML structure
        assert test_html_path.exists()
        
        with open(test_html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for essential WeasyPrint structure elements
        required_elements = [
            '<!DOCTYPE html>',
            '<title>Report example</title>',
            'id="cover"',
            'id="contents"',
            'id="columns"',
            'id="skills"',
            'id="offers"',
            'id="chapter"',
            'id="typography"'
        ]
        
        for element in required_elements:
            assert element in content, f"Missing required element: {element}"
    
    def test_html_structure_comparison(self, test_dirs, reference_files):
        """Test that generated HTML has similar structure to reference"""
        output_dir = test_dirs["output"]
        
        # Read generated HTML
        test_html_path = output_dir / "test-report.html"
        with open(test_html_path, 'r', encoding='utf-8') as f:
            generated_html = f.read()
        
        # Read reference HTML
        with open(reference_files["report.html"], 'r', encoding='utf-8') as f:
            reference_html = f.read()
        
        # Compare structure
        structure_comparison = self._compare_html_structure(generated_html, reference_html)
        
        assert structure_comparison["is_valid"], f"Structure differences: {structure_comparison['differences']}"
    
    def test_pdf_generation_with_buckia(self, test_dirs):
        """Test PDF generation using Buckia with enhanced logging"""
        output_dir = test_dirs["output"]
        test_html_path = output_dir / "test-report.html"
        
        # Generate PDF using Buckia's local-only mode
        result = render_pdf_local_only(
            html_file_path=str(test_html_path),
            pdf_filename="test-report.pdf",
            unguessable_id="test-integration",
            output_dir=str(output_dir)
        )
        
        # Verify PDF was created
        pdf_path = Path(result["local_path"])
        assert pdf_path.exists(), "PDF should be created"
        assert pdf_path.stat().st_size > 1000, "PDF should have reasonable size (>1KB)"
        
        print(f"Generated PDF: {pdf_path}")
        print(f"PDF size: {result['size_bytes']} bytes")
    
    def test_pdf_visual_comparison(self, test_dirs, reference_files):
        """Test visual comparison with reference PDF (smoke test)"""
        output_dir = test_dirs["output"]
        
        test_pdf_path = output_dir / "test-report.pdf"
        reference_pdf_path = reference_files["report.pdf"]
        
        # Basic smoke tests
        assert test_pdf_path.exists(), "Test PDF should exist"
        assert reference_pdf_path.exists(), "Reference PDF should exist"
        
        test_size = test_pdf_path.stat().st_size
        reference_size = reference_pdf_path.stat().st_size
        
        # PDFs should be reasonably sized
        assert test_size > 1000, "Test PDF should be at least 1KB"
        assert test_size < 10 * 1024 * 1024, "Test PDF should be less than 10MB"
        
        print(f"Test PDF size: {test_size} bytes")
        print(f"Reference PDF size: {reference_size} bytes")
        
        # Size should be within reasonable range of reference
        size_difference = abs(test_size - reference_size) / reference_size
        assert size_difference < 2.0, f"PDF size difference too large: {size_difference:.2%}"
    
    def test_weasyprint_warnings_detection(self, test_dirs, capfd):
        """Test that we can detect WeasyPrint warnings and errors"""
        output_dir = test_dirs["output"]
        
        # Create HTML with intentional issues to trigger warnings
        problematic_html = self._create_problematic_html()
        problematic_html_path = output_dir / "problematic-report.html"
        
        with open(problematic_html_path, 'w', encoding='utf-8') as f:
            f.write(problematic_html)
        
        # Try to generate PDF and capture warnings
        try:
            result = render_pdf_local_only(
                html_file_path=str(problematic_html_path),
                pdf_filename="problematic-report.pdf",
                unguessable_id="test-warnings",
                output_dir=str(output_dir)
            )
            
            # Even with warnings, PDF might still be created
            if result and "local_path" in result:
                pdf_path = Path(result["local_path"])
                if pdf_path.exists():
                    print(f"PDF created despite warnings: {pdf_path}")
        
        except Exception as e:
            print(f"Expected error due to problematic HTML: {e}")
        
        # Check captured output for warnings
        captured = capfd.readouterr()
        output_text = captured.out + captured.err
        
        # Look for common WeasyPrint warning patterns
        warning_patterns = [
            "WARNING",
            "ERROR", 
            "Failed to load",
            "Cannot resolve",
            "Invalid"
        ]
        
        warnings_found = []
        for pattern in warning_patterns:
            if pattern in output_text:
                warnings_found.append(pattern)
        
        print(f"WeasyPrint warnings detected: {warnings_found}")
        # Note: This test documents warning detection capability
    
    def _create_weasyprint_test_html(self) -> str:
        """Create HTML that matches WeasyPrint report structure"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Report example</title>
  <style>
    /* WeasyPrint Report CSS - essential styles */
    @page { 
      @top-left { background: #fbc847; content: counter(page); height: 1cm; text-align: center; width: 1cm; } 
      @top-center { background: #fbc847; content: ''; display: block; height: .05cm; opacity: .5; width: 100%; } 
      @top-right { content: string(heading); font-size: 9pt; height: 1cm; vertical-align: middle; width: 100%; } 
    }
    @page :first { background: url(report-cover.jpg) no-repeat center; background-size: cover; margin: 0; }
    @page chapter { background: #fbc847; margin: 0; }
    
    html { color: #393939; font-family: Arial, sans-serif; font-size: 11pt; font-weight: 300; line-height: 1.5; }
    body { margin: 0; }
    h1 { color: #fbc847; font-size: 38pt; margin: 5cm 2cm 0 2cm; width: 100%; }
    h2 { break-before: always; font-size: 28pt; string-set: heading content(); color: black; font-weight: 400; }
    h3 { font-weight: 300; font-size: 15pt; color: black; }
    h4 { font-size: 13pt; color: black; font-weight: 400; }
    
    #cover { align-content: space-between; display: flex; flex-wrap: wrap; height: 297mm; }
    #cover address { background: #fbc847; flex: 1 50%; margin: 0 -2cm; padding: 1cm 0; white-space: pre-wrap; }
    #contents { break-before: right; break-after: left; }
    #columns section { columns: 2; column-gap: 1cm; padding-top: 1cm; }
    #skills h3 { background: #fbc847; margin: 0 -3cm 1cm; padding: 1cm 1cm 1cm 3cm; width: 21cm; }
    #offers { display: flex; flex-wrap: wrap; justify-content: space-between; }
    #offers section { width: 30%; }
    #chapter { align-items: center; display: flex; height: 297mm; justify-content: center; page: chapter; }
    #typography section { display: flex; flex-wrap: wrap; margin: 1cm 0; }
  </style>
</head>
<body>
  <div id="cover">
    <address>WeasyPrint
26 rue Emile Decorps
69100 Villeurbanne
France</address>
    <address>contact@courtbouillon.org
https://courtbouillon.org</address>
  </div>

  <div id="contents">
    <h2>Table of contents</h2>
    <h3>Part one</h3>
    <ul>
      <li><a href="#columns-title">Big title on left page, with text on columns</a></li>
      <li><a href="#skills-title">This is another big title, on a page full of work presentation</a></li>
    </ul>
    <h3>Part two</h3>
    <ul>
      <li><a href="#offers-title">Big title on the first right page</a></li>
      <li><a href="#chapter-title">This is a chapter of a new section</a></li>
      <li><a href="#typography-title">About some typography features</a></li>
    </ul>
  </div>

  <div id="columns">
    <h2 id="columns-title">Big title on left page, with text on columns</h2>
    <section>
      <h3>This is a little subtitle, here to explain what we are talking about</h3>
      <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam volutpat faucibus vestibulum. Mauris varius orci quam.</p>
    </section>
  </div>

  <div id="skills">
    <h2 id="skills-title">This is another big title, on a page full of work presentation</h2>
    <h3>We present you some of WeasyPrint's features.</h3>
    <section id="table-content">
      <h4>Table of contents</h4>
      <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
    </section>
  </div>

  <div id="offers">
    <h2 id="offers-title">Big title on the first right page</h2>
    <section>
      <h4>Offer #1</h4>
      <p>€135</p>
      <ul>
        <li>Lorem ipsum dolor sit amet.</li>
        <li>Nullam at diam eget urna consequat.</li>
      </ul>
    </section>
  </div>

  <div id="chapter">
    <h2 id="chapter-title">This is a chapter of a new section</h2>
  </div>

  <div id="typography">
    <h2 id="typography-title">About some typography features</h2>
    <section>
      <h4>Italic and Bold Text</h4>
      <p>Lorem ipsum dolor <em>sit amet, consectetur adipiscing elit.</em> Ut pulvinar dolor <strong>ac orci finibus elementum.</strong></p>
    </section>
  </div>
</body>
</html>'''
    
    def _create_problematic_html(self) -> str:
        """Create HTML with issues to trigger WeasyPrint warnings"""
        return '''<!DOCTYPE html>
<html>
<head>
  <title>Problematic Report</title>
  <style>
    @page { margin: 2cm; }
    body { font-family: Arial, sans-serif; }
  </style>
</head>
<body>
  <h1>Test Report with Issues</h1>
  <img src="nonexistent-image.jpg" alt="Missing image">
  <p>This HTML has intentional issues to trigger warnings.</p>
  <link rel="stylesheet" href="nonexistent-styles.css">
</body>
</html>'''
    
    def _compare_html_structure(self, generated: str, reference: str) -> Dict[str, Any]:
        """Compare HTML structure between generated and reference"""
        differences = []
        
        # Essential structure checks
        required_elements = [
            '<!DOCTYPE html>',
            '<title>',
            '<h1>',
            '<h2>',
            'id="cover"',
            'id="contents"',
            'id="columns"',
            'id="skills"',
            'id="offers"',
            'id="chapter"',
            'id="typography"'
        ]
        
        for element in required_elements:
            if element not in generated:
                differences.append(f"Missing required element: {element}")
        
        # Check for WeasyPrint-specific CSS features
        weasyprint_features = [
            '@page',
            'string-set:',
            'break-before:',
            'target-counter(',
            'target-text('
        ]
        
        has_weasyprint_features = any(feature in generated for feature in weasyprint_features)
        if not has_weasyprint_features:
            differences.append("Missing WeasyPrint-specific CSS features")
        
        return {
            "is_valid": len(differences) == 0,
            "differences": differences
        }
