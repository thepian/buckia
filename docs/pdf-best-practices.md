# PDF Best Practices

Guidelines for creating professional PDFs with Buckia, optimized for whitepapers and insights documents.

## HTML Structure

### Document Layout
```html
<!DOCTYPE html>
<html>
<head>
  <title>Document Title</title>
  <style>
    @page {
      size: A4;
      margin: 2.5cm;
      @top-center { content: "Document Title"; }
      @bottom-center { content: "Page " counter(page); }
    }
  </style>
</head>
<body>
  <header class="cover-page">
    <h1>Document Title</h1>
    <p>Author • Date</p>
  </header>
  
  <main>
    <section class="executive-summary">
      <h2>Executive Summary</h2>
      <p>Key insights...</p>
    </section>
    
    <section class="chapter">
      <h2>Chapter 1</h2>
      <p>Content...</p>
    </section>
  </main>
</body>
</html>
```

## CSS for Professional PDFs

### Page Setup
```css
@page {
  size: A4;
  margin: 2.5cm;
  @top-right {
    content: "© 2024 Company";
    font-size: 9pt;
    color: #999;
  }
  @bottom-center {
    content: "Page " counter(page) " of " counter(pages);
    font-size: 9pt;
  }
}
```

### Typography
```css
body {
  font-family: 'Times New Roman', serif;
  font-size: 12pt;
  line-height: 1.6;
  color: #333;
}

h1, h2, h3 {
  color: #2c3e50;
  page-break-after: avoid;
}

p {
  text-align: justify;
  margin-bottom: 1em;
}
```

### Page Control
```css
.cover-page { page-break-after: always; }
.chapter { page-break-before: always; }
.keep-together { page-break-inside: avoid; }
.no-print { display: none; }
```

## Whitepaper Styling

### Executive Summary
```css
.executive-summary {
  background: #f8f9fa;
  padding: 1cm;
  border-left: 4px solid #007acc;
  page-break-inside: avoid;
  margin-bottom: 2cm;
}
```

### Call-out Boxes
```css
.callout {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  padding: 1em;
  margin: 1em 0;
  page-break-inside: avoid;
}
```

### Tables
```css
table {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  page-break-inside: avoid;
}

th, td {
  border: 1px solid #ddd;
  padding: 8pt;
  text-align: left;
}

th {
  background: #f5f5f5;
  font-weight: bold;
}
```

## Common Patterns

### Multi-Column Layout
```css
.two-column {
  column-count: 2;
  column-gap: 1cm;
  column-rule: 1px solid #ddd;
}
```

### Image Placement
```css
.figure {
  text-align: center;
  margin: 1em 0;
  page-break-inside: avoid;
}

.figure img {
  max-width: 100%;
  height: auto;
}

.figure-caption {
  font-size: 10pt;
  color: #666;
  margin-top: 0.5em;
}
```

## WeasyPrint Limitations

### Avoid These CSS Features
- `flexbox` and `grid` layouts
- `transform` properties
- `position: sticky`
- Complex `calc()` expressions
- CSS variables in some contexts

### Use Instead
- `float` for layout
- `table` for structured data
- `position: relative/absolute`
- Fixed measurements
- Inline styles for dynamic values

## Testing Workflow

### Local Testing
```bash
# Test PDF generation locally
buckia pdf render document.html bucket-name unique-id doc-name --local-only

# Check output
open doc-name.pdf
```

### Optimization Checklist
- [ ] Page breaks work correctly
- [ ] Headers and footers appear
- [ ] Images load and scale properly
- [ ] Typography is readable
- [ ] No content is cut off
- [ ] File size is reasonable

## Integration Examples

### Static Site Generator
```bash
# Build site
npm run build

# Generate PDF
buckia pdf render dist/insights/report.html cdn report-id quarterly-report

# Result: https://cdn.example.com/insights/report-id/quarterly-report.pdf
```

### Batch Processing
```bash
# Process multiple documents
for file in dist/whitepapers/*.html; do
  name=$(basename "$file" .html)
  buckia pdf render "$file" cdn "$(date +%s)" "$name" --local-only
done
```

## Performance Tips

### Image Optimization
- Use WebP or optimized JPEG/PNG
- Set appropriate dimensions in HTML
- Enable `optimize_images: true` in WeasyPrint options

### CSS Optimization
- Minimize external stylesheets
- Inline critical CSS
- Remove unused styles

### File Size Management
```yaml
# .buckia configuration
pdf:
  weasyprint_options:
    optimize_images: true
    jpeg_quality: 85
    pdf_version: "1.7"
```

## Troubleshooting

### Common Issues
- **Missing styles**: Check CSS file paths
- **Large files**: Enable image optimization
- **Layout issues**: Avoid unsupported CSS features
- **Font problems**: Use web-safe fonts with fallbacks

### Debug Commands
```bash
# Verbose output
buckia pdf render file.html bucket id name --local-only --verbose

# Test with minimal CSS
buckia pdf render file.html bucket id name --local-only --debug
```
