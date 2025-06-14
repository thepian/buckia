# WeasyPrint HTML Evaluation Framework

## Research Summary: How to Evaluate HTML for PDF Generation

Based on WeasyPrint documentation and CSS print best practices, here's a comprehensive framework for evaluating HTML files intended for PDF generation.

## 1. Browser Developer Tools Evaluation

### Print Media Simulation
```javascript
// In browser console, simulate print media
document.querySelector('html').style.media = 'print';

// Or use Chrome DevTools:
// 1. Open DevTools (F12)
// 2. Click "..." menu → More tools → Rendering
// 3. Set "Emulate CSS media type" to "print"
```

### Font Hierarchy Inspection
```css
/* Check computed font sizes in DevTools */
h1 { font-size: ? }  /* Should be largest */
h2 { font-size: ? }  /* Should be smaller than h1 */
h3 { font-size: ? }  /* Should be smaller than h2 */
p  { font-size: ? }  /* Base text size */
```

### Layout Analysis
- **Box model**: Check margins, padding, borders in computed styles
- **Positioning**: Verify no absolute/fixed positioning that breaks in print
- **Overflow**: Ensure no hidden content that won't appear in PDF
- **Z-index**: Check stacking order for overlapping elements

## 2. CSS Print Media Evaluation

### Required Print Styles
```css
@media print {
  /* Page setup */
  @page {
    size: A4;
    margin: 2cm;
  }
  
  /* Font hierarchy */
  h1 { font-size: 24pt; }
  h2 { font-size: 20pt; }
  h3 { font-size: 16pt; }
  p  { font-size: 12pt; }
  
  /* Hide screen-only elements */
  .no-print { display: none; }
  
  /* Ensure images fit */
  img { max-width: 100%; height: auto; }
}
```

### Common Issues to Check
1. **Font sizes in pixels vs points**: Use `pt` for print, not `px`
2. **Missing print styles**: Screen styles may not work for PDF
3. **Page breaks**: Check `page-break-before`, `page-break-after`
4. **Color vs grayscale**: Ensure readability in both

## 3. WeasyPrint-Specific Evaluation

### Supported Features Checklist
- ✅ **CSS 2.1**: Most features supported
- ✅ **Flexbox**: Basic support
- ✅ **Grid**: Limited support
- ✅ **Transforms**: 2D only
- ❌ **CSS animations**: Not supported
- ❌ **JavaScript**: Not executed

### Image Evaluation
```html
<!-- Check image formats -->
<img src="image.svg" />  <!-- ✅ SVG supported -->
<img src="image.png" />  <!-- ✅ PNG supported -->
<img src="image.jpg" />  <!-- ✅ JPEG supported -->
<img src="image.webp" /> <!-- ❌ WebP not supported -->
```

### Font Evaluation
```css
/* Check font loading */
@font-face {
  font-family: 'CustomFont';
  src: url('font.woff2') format('woff2'); /* ✅ Supported */
}

/* System fonts */
font-family: 'Arial', sans-serif; /* ✅ Works with fontconfig */
```

## 4. Layout Issues Identification

### Font Hierarchy Problems
```css
/* BAD: No clear hierarchy */
h1, h2, h3 { font-size: 16px; }

/* GOOD: Clear hierarchy */
h1 { font-size: 24pt; font-weight: bold; }
h2 { font-size: 20pt; font-weight: bold; }
h3 { font-size: 16pt; font-weight: bold; }
```

### Overlapping Elements
```css
/* Check for overlapping content */
.element {
  position: absolute; /* ⚠️ May cause overlaps */
  z-index: 999;      /* ⚠️ Check stacking */
}
```

### Page Title Issues
```html
<!-- Check document title -->
<title>Proper Document Title</title> <!-- ✅ Good -->
<title>Table of contents</title>     <!-- ❌ Generic title -->
```

## 5. Debugging Techniques

### WeasyPrint Debug Mode
```bash
# Generate PDF with debug info
weasyprint --debug input.html output.pdf

# Check for warnings and errors in output
```

### CSS Validation
```bash
# Validate CSS for print media
# Use W3C CSS Validator with media=print
```

### Manual Inspection Points
1. **Page breaks**: Do sections break appropriately?
2. **Margins**: Are margins consistent and appropriate?
3. **Typography**: Is text readable and well-spaced?
4. **Images**: Do images display and scale correctly?
5. **Tables**: Do tables fit within page width?
6. **Headers/footers**: Are running headers working?

## 6. Specific Issue Diagnosis

### "All pages have title: Table of contents"
```html
<!-- Problem: Generic title in head -->
<title>Table of contents</title>

<!-- Solution: Use proper document title -->
<title>The Future of Enterprise AI - Whitepaper</title>
```

### "Lead fact cards overlap"
```css
/* Problem: Absolute positioning */
.fact-card {
  position: absolute;
  bottom: 0;
}

/* Solution: Use flexbox or grid */
.fact-cards {
  display: flex;
  gap: 1rem;
}
```

### "No embedded images visible"
```html
<!-- Problem: Images not loading -->
<img src="relative/path/image.svg" />

<!-- Check: Are paths correct for WeasyPrint? -->
<!-- Check: Are images in supported formats? -->
```

### "No proper font hierarchy"
```css
/* Problem: All headings same size */
h1, h2, h3 { font-size: 1rem; }

/* Solution: Define clear hierarchy */
h1 { font-size: 2rem; }
h2 { font-size: 1.5rem; }
h3 { font-size: 1.25rem; }
```

## 7. Evaluation Workflow

### Step 1: Browser Print Preview
1. Open HTML in browser
2. Use Ctrl+P (Cmd+P) to see print preview
3. Check layout, fonts, images
4. Note any issues

### Step 2: DevTools Print Media
1. Open DevTools
2. Emulate print media
3. Inspect computed styles
4. Check for missing print CSS

### Step 3: WeasyPrint Test
1. Generate PDF with WeasyPrint
2. Compare with browser print preview
3. Note WeasyPrint-specific issues
4. Check console output for warnings

### Step 4: PDF Analysis
1. Open generated PDF
2. Check font sizes and hierarchy
3. Verify image display
4. Test page navigation
5. Check metadata (title, author)

## 8. Common Fixes

### Font Hierarchy
```css
@media print {
  h1 { font-size: 24pt; line-height: 1.2; }
  h2 { font-size: 20pt; line-height: 1.3; }
  h3 { font-size: 16pt; line-height: 1.4; }
  p  { font-size: 12pt; line-height: 1.5; }
}
```

### Image Display
```css
@media print {
  img {
    max-width: 100%;
    height: auto;
    page-break-inside: avoid;
  }
}
```

### Page Titles
```html
<head>
  <title>Specific Document Title</title>
</head>
```

### Layout Fixes
```css
@media print {
  .container {
    display: block; /* Avoid complex layouts */
    width: 100%;
  }
  
  .no-break {
    page-break-inside: avoid;
  }
}
```

## Next Steps

1. **Implement evaluation tools** to automatically check HTML
2. **Create print-specific CSS** for whitepaper layouts
3. **Test with actual content** to identify real-world issues
4. **Iterate based on PDF output** rather than browser preview

This framework provides a systematic approach to evaluating and improving HTML for professional PDF generation with WeasyPrint.
