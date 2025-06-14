# PDF Generation Configuration

Buckia converts HTML files to professional PDFs using WeasyPrint and uploads them to cloud storage with public URLs.

## How It Works

1. **Generate HTML** with any static site generator or framework
2. **Buckia processes** the HTML files and resolves asset paths
3. **WeasyPrint** converts HTML to professional PDFs
4. **Buckia uploads** PDFs to cloud storage (optional)

## Quick Start

Add PDF configuration to any bucket in your `.buckia` file:

```yaml
# Bucket name can be anything
cdn-storage:
  provider: bunny
  bucket_name: my-cdn
  token_context: cdn
  paths:
    - "whitepapers/"
  pdf:
    base_url: "https://cdn.example.com/insights"
    path_template: "{id}/{name}"
    weasyprint_options:
      presentational_hints: true
      optimize_images: true
```

## PDF Configuration Fields

### base_url

The base URL where PDFs will be accessible:

```yaml
pdf:
  base_url: "https://cdn.example.com/insights"
  # Results in URLs like: https://cdn.example.com/insights/abc123/my-document.pdf
```

### path_template

URL path template using placeholders:

```yaml
pdf:
  path_template: "{id}/{name}"
  # {id} = unguessable identifier
  # {name} = PDF filename (without .pdf extension)
```

**Template Examples:**

```yaml
# Simple: /abc123/document.pdf
path_template: "{id}/{name}"

# Dated: /2024/06/abc123/document.pdf
path_template: "{year}/{month}/{id}/{name}"

# Categorized: /whitepapers/abc123/document.pdf
path_template: "whitepapers/{id}/{name}"
```

### weasyprint_options

WeasyPrint rendering configuration:

```yaml
pdf:
  weasyprint_options:
    presentational_hints: true
    optimize_images: true
    pdf_version: "1.7"
    pdf_forms: false
```

## WeasyPrint Options

### Common Options

| Option                 | Type    | Default | Description                        |
| ---------------------- | ------- | ------- | ---------------------------------- |
| `presentational_hints` | boolean | `true`  | Use HTML presentational attributes |
| `optimize_images`      | boolean | `true`  | Compress embedded images           |
| `pdf_version`          | string  | `"1.7"` | PDF version (1.4, 1.5, 1.6, 1.7)   |
| `pdf_forms`            | boolean | `false` | Enable interactive PDF forms       |

### Advanced Options

```yaml
pdf:
  weasyprint_options:
    # Image optimization
    optimize_images: true
    jpeg_quality: 85

    # PDF features
    pdf_version: "1.7"
    pdf_forms: false
    pdf_identifier: true

    # Rendering behavior
    presentational_hints: true
    font_size: 12

    # Page settings (handled by CSS @page rules)
    # Use CSS instead of these options
```

## Complete Examples

### Marketing Website

```yaml
# Bucket name can be anything
marketing-cdn:
  provider: bunny
  bucket_name: marketing-assets
  token_context: marketing
  paths:
    - "whitepapers/"
    - "case-studies/"
  pdf:
    base_url: "https://cdn.marketing.com/resources"
    path_template: "{category}/{id}/{name}"
    weasyprint_options:
      presentational_hints: true
      optimize_images: true
      pdf_version: "1.7"
      jpeg_quality: 90
```

### Documentation Site

```yaml
# Bucket name can be anything
docs-cdn:
  provider: s3
  bucket_name: docs-storage
  token_context: docs
  region: us-east-1
  paths:
    - "docs/"
  pdf:
    base_url: "https://docs.example.com/pdf"
    path_template: "v{version}/{id}/{name}"
    weasyprint_options:
      presentational_hints: true
      optimize_images: true
      pdf_version: "1.6" # Better compatibility
```

### Report Generation

```yaml
# Bucket name can be anything
report-storage:
  provider: b2
  bucket_name: company-reports
  token_context: reports
  pdf:
    base_url: "https://reports.company.com/generated"
    path_template: "{year}/{month}/{id}/{name}"
    weasyprint_options:
      presentational_hints: true
      optimize_images: true
      pdf_version: "1.7"
      pdf_forms: true # Interactive reports
```

## CLI Usage

### Generate PDF with Upload

```bash
# Render HTML to PDF and upload
buckia pdf render index.html cdn unique-id my-document

# With custom output directory
buckia pdf render index.html cdn unique-id my-document --output-dir ./pdfs
```

### Local-Only Generation

```bash
# Generate PDF without uploading
buckia pdf render index.html cdn unique-id my-document --local-only

# Save to specific directory
buckia pdf render index.html cdn unique-id my-document --local-only --output-dir ./local-pdfs
```

### Batch Processing

```bash
# Process multiple HTML files
for file in whitepapers/*.html; do
  name=$(basename "$file" .html)
  buckia pdf render "$file" cdn "$(uuidgen)" "$name" --local-only
done
```

## HTML Optimization for PDF

### CSS Considerations

WeasyPrint supports a subset of CSS. Optimize your HTML:

```html
<!DOCTYPE html>
<html>
  <head>
    <style>
      /* Use print-specific styles */
      @media print {
        body {
          font-size: 12pt;
        }
        .no-print {
          display: none;
        }
      }

      /* Page settings */
      @page {
        size: A4;
        margin: 2cm;
      }

      /* Avoid unsupported CSS */
      /* ❌ Don't use: flexbox, grid, transforms */
      /* ✅ Use: floats, positioning, tables */
    </style>
  </head>
  <body>
    <h1>My Document</h1>
    <p>Content here...</p>
  </body>
</html>
```

### Image Handling

Buckia automatically processes image paths:

```html
<!-- These work automatically -->
<img src="/_astro/image.abc123.png" alt="Image" />
<img src="/assets/logo.svg" alt="Logo" />

<!-- Absolute URLs work too -->
<img src="https://example.com/image.jpg" alt="External" />
```

### Best Practices

1. **Use semantic HTML** - Better PDF structure
2. **Optimize images** - Smaller PDF files
3. **Test locally first** - Use `--local-only` flag
4. **Use print CSS** - `@media print` rules
5. **Avoid complex layouts** - WeasyPrint limitations
6. **Set page breaks** - `page-break-before/after`

## Professional PDF Styling

### Page Layout and Headers

Use CSS `@page` rules for professional document layout:

```html
<style>
  @page {
    size: A4;
    margin: 2cm;
    @top-center {
      content: "Document Title";
      font-size: 10pt;
      color: #666;
    }
    @bottom-center {
      content: "Page " counter(page) " of " counter(pages);
      font-size: 10pt;
      color: #666;
    }
  }

  /* Professional typography */
  body {
    font-family: "Times New Roman", serif;
    font-size: 12pt;
    line-height: 1.6;
    color: #333;
  }

  h1 {
    color: #2c3e50;
    page-break-after: avoid;
  }

  /* Page control */
  .page-break {
    page-break-before: always;
  }
  .no-print {
    display: none;
  }
  .keep-together {
    page-break-inside: avoid;
  }
</style>
```

### Whitepaper and Insights Optimization

For marketing whitepapers and insights documents:

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Whitepaper Title</title>
    <style>
      @page {
        size: A4;
        margin: 2.5cm;
        @top-right {
          content: "© 2024 Company Name";
          font-size: 9pt;
          color: #999;
        }
      }

      .cover-page {
        page-break-after: always;
        text-align: center;
        padding-top: 5cm;
      }

      .executive-summary {
        background: #f8f9fa;
        padding: 1cm;
        border-left: 4px solid #007acc;
        page-break-inside: avoid;
      }

      .chapter {
        page-break-before: always;
      }
    </style>
  </head>
  <body>
    <div class="cover-page">
      <h1>Whitepaper Title</h1>
      <p>Subtitle or description</p>
      <p>Author • Date</p>
    </div>

    <div class="executive-summary">
      <h2>Executive Summary</h2>
      <p>Key insights...</p>
    </div>

    <div class="chapter">
      <h2>Chapter 1</h2>
      <p>Content...</p>
    </div>
  </body>
</html>
```

### Workflow Integration

Works with any HTML generation method:

```bash
# Static site generators
hugo build && buckia pdf render public/insights/report.html cdn id report

# Astro
npm run build && buckia pdf render dist/whitepapers/doc.html cdn id doc

# Jekyll
bundle exec jekyll build && buckia pdf render _site/insights/doc.html cdn id doc

# Custom HTML
buckia pdf render my-document.html cdn unique-id document-name
```

## Integration Examples

### Node.js Script

```javascript
const { execSync } = require("child_process");

function generatePDF(htmlPath, documentName, uniqueId) {
  const command = [
    "buckia",
    "pdf",
    "render",
    htmlPath,
    "cdn",
    uniqueId,
    documentName,
    "--local-only",
  ].join(" ");

  execSync(command, { stdio: "inherit" });
  return `${documentName}.pdf`;
}

// Usage
const pdfPath = generatePDF("./report.html", "monthly-report", "abc123");
console.log(`PDF generated: ${pdfPath}`);
```

### Python Integration

```python
from buckia.pdf import render_pdf_command

result = render_pdf_command(
    html_file_path='./report.html',
    bucket_name='cdn',
    unguessable_id='abc123',
    pdf_filename='monthly-report',
    local_only=True
)

print(f"PDF generated: {result['local_path']}")
```

## Troubleshooting

### Common Issues

**CSS Not Applied**

- Check file paths in HTML
- Use absolute paths or ensure relative paths are correct
- Test with simple CSS first

**Images Missing**

- Verify image files exist
- Check image paths in HTML
- Use `--verbose` flag to see processing details

**Large PDF Files**

- Enable `optimize_images: true`
- Reduce `jpeg_quality` setting
- Optimize source images before rendering

**WeasyPrint Warnings**

- Normal for modern CSS features
- Focus on critical warnings only
- Use print-specific CSS to reduce warnings

### Getting Help

```bash
# Show PDF command help
buckia pdf --help

# Show render options
buckia pdf render --help

# Test with verbose output
buckia pdf render file.html cdn id name --local-only --verbose
```

## Next Steps

- **[Sync Configuration](sync.md)** - Advanced sync options
- **[Team Organization](teams.md)** - Multi-team PDF workflows
- **[Security](security.md)** - Secure PDF generation
- **[CLI Reference](../cli/pdf.md)** - Complete PDF command reference
