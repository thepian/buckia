# WeasyPrint Integration Tests

## Overview

This test suite verifies that we can generate PDF files at the level of WeasyPrint samples. The tests ensure that markdown/HTML files can generate PDFs that match WeasyPrint reference samples in terms of structure, layout, and professional quality.

## Test Objectives

1. **Reference Validation**: Download and validate WeasyPrint reference samples
2. **HTML Structure**: Generate HTML that matches WeasyPrint report structure
3. **PDF Generation**: Use Buckia to generate PDFs with proper WeasyPrint features
4. **Visual Comparison**: Perform smoke tests comparing generated vs reference PDFs
5. **Error Detection**: Monitor WeasyPrint warnings and errors for debugging

## Test Files

### Core Test File
- `tests/test_weasyprint_integration.py` - Main test suite

### Supporting Files
- `scripts/run_weasyprint_tests.py` - Test runner script
- `tests/output/` - Generated test files (created during test run)
- `tests/reference/` - Downloaded WeasyPrint reference files

## Running the Tests

### Quick Start
```bash
# Run all WeasyPrint integration tests
python scripts/run_weasyprint_tests.py
```

### Manual Execution
```bash
# Install dependencies if needed
pip install pytest requests weasyprint

# Run tests with pytest directly
pytest tests/test_weasyprint_integration.py -v -s
```

## Test Cases

### 1. Reference File Download
**Test**: `test_reference_files_downloaded`
- Downloads WeasyPrint report sample files (HTML, CSS, PDF)
- Validates files are downloaded and not empty
- Creates reference baseline for comparison

### 2. HTML Structure Generation
**Test**: `test_create_test_html_from_markdown`
- Creates HTML that matches WeasyPrint report structure
- Validates presence of essential elements (`#cover`, `#contents`, etc.)
- Ensures proper heading hierarchy and CSS structure

### 3. HTML Structure Comparison
**Test**: `test_html_structure_comparison`
- Compares generated HTML with WeasyPrint reference
- Validates WeasyPrint-specific CSS features
- Checks for proper page layout elements

### 4. PDF Generation with Buckia
**Test**: `test_pdf_generation_with_buckia`
- Uses Buckia's `render_pdf_local_only` function
- Generates PDF from test HTML
- Validates PDF creation and reasonable file size

### 5. Visual PDF Comparison
**Test**: `test_pdf_visual_comparison`
- Compares generated PDF with reference PDF
- Performs smoke tests (file size, existence)
- Validates PDF is within reasonable size range

### 6. WeasyPrint Warnings Detection
**Test**: `test_weasyprint_warnings_detection`
- Creates HTML with intentional issues
- Tests warning/error detection capabilities
- Documents debugging workflow

## Expected Outputs

### Successful Test Run
```
✅ All tests passed!

📋 Test Summary:
- ✅ Reference files downloaded
- ✅ HTML structure validation  
- ✅ PDF generation with Buckia
- ✅ Visual comparison (smoke test)
- ✅ WeasyPrint warnings detection
```

### Generated Files
- `tests/output/test-report.html` - Generated HTML matching WeasyPrint structure
- `tests/output/test-report.pdf` - Generated PDF using Buckia
- `tests/reference/report.html` - WeasyPrint reference HTML
- `tests/reference/report.css` - WeasyPrint reference CSS
- `tests/reference/report.pdf` - WeasyPrint reference PDF

## Key Features Tested

### WeasyPrint CSS Features
- `@page` rules with headers/footers
- `string-set` and `target-counter` for table of contents
- `break-before` and `page` properties for layout
- Multi-column layouts
- Typography features (ligatures, small-caps, etc.)

### HTML Structure Elements
- Cover page with contact information
- Table of contents with page references
- Multi-column text sections
- Skills/features showcase with icons
- Offers section with pricing cards
- Chapter pages with special layouts
- Typography demonstration sections

### PDF Quality Metrics
- File size within reasonable range (1KB - 10MB)
- Professional layout with proper page breaks
- Embedded fonts and styling
- Table of contents functionality
- Page headers and numbering

## Troubleshooting

### Common Issues

**Missing Dependencies**
```bash
pip install weasyprint pytest requests
```

**Font Issues**
- WeasyPrint may warn about missing fonts
- Tests use fallback fonts (Arial) for compatibility
- Production should use proper font files

**Image Loading Issues**
- Test HTML uses placeholder images
- WeasyPrint warnings about missing images are expected
- Production should have proper image paths

**PDF Size Variations**
- Generated PDFs may vary in size due to font differences
- Tests allow up to 200% size difference from reference
- Large variations may indicate layout issues

### Debug Mode
```bash
# Run with more verbose output
pytest tests/test_weasyprint_integration.py -v -s --tb=long

# Run specific test
pytest tests/test_weasyprint_integration.py::TestWeasyPrintIntegration::test_pdf_generation_with_buckia -v -s
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run WeasyPrint Integration Tests
  run: |
    pip install -e .[pdf,dev]
    python scripts/run_weasyprint_tests.py
```

### Test Artifacts
- Generated PDFs can be saved as CI artifacts
- Reference files are downloaded automatically
- Test outputs provide debugging information

## Future Enhancements

1. **Visual Diff Testing**: Compare PDF content pixel-by-pixel
2. **Performance Benchmarks**: Measure PDF generation speed
3. **Font Testing**: Test with actual WeasyPrint fonts
4. **Template Variations**: Test different document types
5. **Accessibility Testing**: Validate PDF accessibility features

## Related Documentation

- [WeasyPrint Samples](https://github.com/CourtBouillon/weasyprint-samples)
- [Buckia PDF Documentation](./configuration/pdf.md)
- [PDF Best Practices](./pdf-best-practices.md)
- [WeasyPrint Documentation](https://doc.courtbouillon.org/weasyprint/)

## Success Criteria

The test suite is successful when:
1. All reference files download correctly
2. Generated HTML matches WeasyPrint structure
3. PDF generation completes without critical errors
4. Generated PDF is within reasonable size range
5. WeasyPrint warnings are properly detected and logged

This ensures that our PDF generation system can produce professional-quality documents comparable to WeasyPrint reference samples.
