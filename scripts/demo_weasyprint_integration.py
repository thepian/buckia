#!/usr/bin/env python3
"""
WeasyPrint Integration Demo

This script demonstrates the WeasyPrint integration capabilities by:
1. Creating a sample HTML file that matches WeasyPrint structure
2. Generating a PDF using Buckia
3. Comparing with WeasyPrint reference samples
"""

import os
import sys
import tempfile
import requests
from pathlib import Path
from buckia.pdf import render_pdf_local_only


def create_demo_html() -> str:
    """Create demo HTML that matches WeasyPrint report structure"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WeasyPrint Integration Demo</title>
  <style>
    /* WeasyPrint-compatible CSS */
    @page { 
      @top-left { 
        background: #fbc847; 
        content: counter(page); 
        height: 1cm; 
        text-align: center; 
        width: 1cm; 
      } 
      @top-center { 
        background: #fbc847; 
        content: ''; 
        display: block; 
        height: .05cm; 
        opacity: .5; 
        width: 100%; 
      } 
      @top-right { 
        content: string(heading); 
        font-size: 9pt; 
        height: 1cm; 
        vertical-align: middle; 
        width: 100%; 
      } 
    }
    
    @page :first { 
      margin: 0; 
    }
    
    html { 
      color: #393939; 
      font-family: Arial, sans-serif; 
      font-size: 11pt; 
      font-weight: 300; 
      line-height: 1.5; 
    }
    
    body { 
      margin: 0; 
    }
    
    h1 { 
      color: #fbc847; 
      font-size: 38pt; 
      margin: 5cm 2cm 0 2cm; 
      width: 100%; 
    }
    
    h2 { 
      break-before: always; 
      font-size: 28pt; 
      string-set: heading content(); 
      color: black; 
      font-weight: 400; 
    }
    
    h3 { 
      font-weight: 300; 
      font-size: 15pt; 
      color: black; 
    }
    
    .cover { 
      height: 297mm; 
      display: flex; 
      flex-direction: column; 
      justify-content: center; 
      align-items: center; 
      background: linear-gradient(135deg, #fbc847 0%, #f39c12 100%);
      color: white;
      text-align: center;
    }
    
    .cover h1 {
      color: white;
      margin: 0;
      font-size: 48pt;
    }
    
    .cover p {
      font-size: 18pt;
      margin: 1cm 0;
    }
    
    .content {
      margin: 2cm;
    }
    
    .two-column {
      columns: 2;
      column-gap: 1cm;
      text-align: justify;
    }
    
    .feature-box {
      background: #f8f9fa;
      border-left: 4pt solid #fbc847;
      padding: 1cm;
      margin: 1cm 0;
      break-inside: avoid;
    }
    
    .feature-box h4 {
      color: #fbc847;
      margin-top: 0;
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 1cm 0;
    }
    
    th, td {
      border: 1pt solid #ddd;
      padding: 0.5cm;
      text-align: left;
    }
    
    th {
      background: #fbc847;
      color: white;
      font-weight: bold;
    }
    
    .footer {
      margin-top: 2cm;
      padding-top: 1cm;
      border-top: 2pt solid #fbc847;
      text-align: center;
      color: #666;
    }
  </style>
</head>
<body>
  <!-- Cover Page -->
  <div class="cover">
    <h1>WeasyPrint Integration Demo</h1>
    <p>Professional PDF Generation with Buckia</p>
    <p>Demonstrating WeasyPrint-level quality</p>
  </div>

  <!-- Content Pages -->
  <div class="content">
    <h2>Introduction</h2>
    <div class="two-column">
      <p>This document demonstrates the WeasyPrint integration capabilities of Buckia. 
      We can generate professional PDFs that match the quality and features of WeasyPrint 
      reference samples.</p>
      
      <p>The integration includes support for advanced CSS features like page headers, 
      footers, table of contents, multi-column layouts, and professional typography.</p>
      
      <p>This demo showcases various layout elements and CSS features that are essential 
      for creating business-quality documents.</p>
    </div>

    <h2>Key Features</h2>
    
    <div class="feature-box">
      <h4>Page Layout Control</h4>
      <p>Advanced page layout with headers, footers, and page numbering using CSS @page rules.</p>
    </div>
    
    <div class="feature-box">
      <h4>Multi-column Text</h4>
      <p>Professional text layout with CSS columns for improved readability and space utilization.</p>
    </div>
    
    <div class="feature-box">
      <h4>Typography Features</h4>
      <p>Support for advanced typography including font variants, ligatures, and proper text formatting.</p>
    </div>

    <h2>Comparison Table</h2>
    
    <table>
      <thead>
        <tr>
          <th>Feature</th>
          <th>WeasyPrint Reference</th>
          <th>Buckia Integration</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Page Headers/Footers</td>
          <td>✓ Full support</td>
          <td>✓ Implemented</td>
          <td>✅ Working</td>
        </tr>
        <tr>
          <td>Table of Contents</td>
          <td>✓ With page numbers</td>
          <td>✓ Implemented</td>
          <td>✅ Working</td>
        </tr>
        <tr>
          <td>Multi-column Layout</td>
          <td>✓ CSS columns</td>
          <td>✓ Implemented</td>
          <td>✅ Working</td>
        </tr>
        <tr>
          <td>Professional Typography</td>
          <td>✓ Font variants</td>
          <td>✓ Implemented</td>
          <td>✅ Working</td>
        </tr>
        <tr>
          <td>Image Embedding</td>
          <td>✓ SVG and raster</td>
          <td>✓ Implemented</td>
          <td>🔧 Enhanced</td>
        </tr>
      </tbody>
    </table>

    <h2>Technical Implementation</h2>
    
    <p>The integration leverages Buckia's PDF generation capabilities with WeasyPrint's 
    rendering engine to produce high-quality documents. Key technical features include:</p>
    
    <ul>
      <li><strong>URL Support:</strong> Direct rendering from dev server URLs</li>
      <li><strong>CSS Processing:</strong> Advanced CSS features for print media</li>
      <li><strong>Image Handling:</strong> Proper resolution of relative image paths</li>
      <li><strong>Error Monitoring:</strong> Enhanced logging for debugging</li>
      <li><strong>Quality Assurance:</strong> Automated testing against reference samples</li>
    </ul>

    <div class="footer">
      <p>Generated with Buckia WeasyPrint Integration</p>
      <p>Professional PDF Generation • Advanced Layout • Quality Assured</p>
    </div>
  </div>
</body>
</html>'''


def download_reference_pdf(output_dir: Path) -> Path:
    """Download WeasyPrint reference PDF for comparison"""
    reference_url = "https://github.com/CourtBouillon/weasyprint-samples/raw/main/report/report.pdf"
    reference_path = output_dir / "weasyprint-reference.pdf"
    
    if not reference_path.exists():
        print(f"📥 Downloading reference PDF from {reference_url}")
        response = requests.get(reference_url, timeout=30)
        response.raise_for_status()
        
        with open(reference_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Reference PDF downloaded: {reference_path}")
    else:
        print(f"✅ Reference PDF already exists: {reference_path}")
    
    return reference_path


def main():
    """Run the WeasyPrint integration demo"""
    print("🎯 WeasyPrint Integration Demo")
    print("=" * 40)
    
    # Create output directory
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Step 1: Create demo HTML
        print("\n📝 Step 1: Creating demo HTML...")
        html_content = create_demo_html()
        html_path = output_dir / "demo-report.html"
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Demo HTML created: {html_path}")
        
        # Step 2: Generate PDF with Buckia
        print("\n🔄 Step 2: Generating PDF with Buckia...")
        
        result = render_pdf_local_only(
            html_file_path=str(html_path),
            pdf_filename="demo-report.pdf",
            unguessable_id="demo-integration",
            output_dir=str(output_dir)
        )
        
        pdf_path = Path(result["local_path"])
        pdf_size = result["size_bytes"]
        
        print(f"✅ PDF generated successfully!")
        print(f"   📄 File: {pdf_path}")
        print(f"   📊 Size: {pdf_size:,} bytes ({pdf_size/1024:.1f} KB)")
        
        # Step 3: Download reference for comparison
        print("\n📥 Step 3: Downloading reference PDF...")
        reference_path = download_reference_pdf(output_dir)
        reference_size = reference_path.stat().st_size
        
        print(f"   📄 Reference: {reference_path}")
        print(f"   📊 Size: {reference_size:,} bytes ({reference_size/1024:.1f} KB)")
        
        # Step 4: Basic comparison
        print("\n📊 Step 4: Basic comparison...")
        size_ratio = pdf_size / reference_size
        
        print(f"   📈 Size ratio: {size_ratio:.2f}x reference")
        
        if 0.5 <= size_ratio <= 2.0:
            print("   ✅ Size within reasonable range")
        else:
            print("   ⚠️  Size difference significant")
        
        # Step 5: Summary
        print("\n🎉 Demo completed successfully!")
        print("\n📋 Generated files:")
        print(f"   • HTML: {html_path}")
        print(f"   • PDF:  {pdf_path}")
        print(f"   • Ref:  {reference_path}")
        
        print("\n🔍 Next steps:")
        print("   • Open the generated PDF to review quality")
        print("   • Compare with the reference PDF")
        print("   • Run full test suite: python scripts/run_weasyprint_tests.py")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
