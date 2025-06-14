"""
PDF generation module for Buckia using WeasyPrint
"""

import logging
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlparse

from .client import BuckiaClient
from .config import BucketConfig, BuckiaConfig

# Configure logging
logger = logging.getLogger("buckia.pdf")

try:
    import weasyprint

    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint not available. Install with: pip install buckia[pdf]")


def _is_url(path: str) -> bool:
    """Check if a path is a URL (http/https)"""
    parsed = urlparse(path)
    return parsed.scheme in ("http", "https")


def _fetch_html_from_url(url: str) -> str:
    """
    Fetch HTML content from a URL and save to temporary file

    Args:
        url: The URL to fetch HTML from

    Returns:
        Path to temporary HTML file containing the fetched content
    """
    logger.info(f"Fetching HTML content from URL: {url}")

    try:
        # Fetch HTML content
        with urllib.request.urlopen(url) as response:
            html_content = response.read().decode("utf-8")

        logger.info(f"Successfully fetched HTML content ({len(html_content)} characters)")

        # Create temporary file with fetched HTML
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as temp_html:
            temp_html.write(html_content)
            temp_html_path = temp_html.name

        logger.info(f"Saved fetched HTML to temporary file: {temp_html_path}")
        return temp_html_path

    except Exception as e:
        raise RuntimeError(f"Failed to fetch HTML from URL {url}: {str(e)}") from e


class PDFRenderer:
    """PDF rendering using WeasyPrint with cloud bucket upload"""

    def __init__(self, config: BucketConfig):
        """Initialize PDF renderer with bucket configuration"""
        if not WEASYPRINT_AVAILABLE:
            raise ImportError(
                "WeasyPrint is required for PDF generation. Install with: pip install buckia[pdf]"
            )

        self.config = config
        self.client = BuckiaClient(config)

        # Get PDF-specific configuration
        self.pdf_config = getattr(config, "pdf", {})

        # Default WeasyPrint options
        self.default_options = {
            "presentational_hints": True,
            "optimize_images": True,
            "pdf_version": "1.7",
            "pdf_forms": False,
        }

        # Merge with user-provided options
        self.weasyprint_options = {
            **self.default_options,
            **self.pdf_config.get("weasyprint_options", {}),
        }

        logger.debug(f"Initialized PDF renderer for bucket: {config.bucket_name}")

    def render_html_to_pdf(
        self,
        html_file_path: str,
        pdf_filename: str,
        unguessable_id: str,
        upload: bool = True,
        css_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Render HTML file or URL to PDF and optionally upload to bucket

        Args:
            html_file_path: Path to the HTML file to render OR URL to fetch HTML from
            pdf_filename: Name for the output PDF file (without extension)
            unguessable_id: Unique identifier for the PDF path
            upload: Whether to upload to bucket (default: True)
            css_override: Optional path to CSS file to inject

        Returns:
            Dictionary with render results including local_path, remote_path, and url
        """
        # Handle URLs by fetching HTML content first
        temp_html_from_url = None
        if _is_url(html_file_path):
            logger.info(f"Detected URL input: {html_file_path}")
            temp_html_from_url = _fetch_html_from_url(html_file_path)
            actual_html_path = temp_html_from_url
        else:
            # Regular file path
            if not os.path.exists(html_file_path):
                raise FileNotFoundError(f"HTML file not found: {html_file_path}")
            actual_html_path = html_file_path

        # Ensure PDF filename has .pdf extension
        if not pdf_filename.endswith(".pdf"):
            pdf_filename += ".pdf"

        logger.info(f"Rendering HTML to PDF: {html_file_path} -> {pdf_filename}")

        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name

        try:
            # Process HTML to fix relative paths
            processed_html_path = self._process_html_for_pdf(actual_html_path, css_override)

            # Render HTML to PDF using WeasyPrint
            html_doc = weasyprint.HTML(filename=processed_html_path)
            html_doc.write_pdf(temp_pdf_path, **self.weasyprint_options)

            # Clean up processed HTML if it's different from original
            if processed_html_path != actual_html_path:
                os.unlink(processed_html_path)

            # Clean up temporary HTML file from URL if it was created
            if temp_html_from_url:
                os.unlink(temp_html_from_url)
                logger.info(f"Cleaned up temporary HTML file: {temp_html_from_url}")

            logger.info(f"PDF rendered successfully: {temp_pdf_path}")

            # Get file size for logging
            pdf_size = os.path.getsize(temp_pdf_path)
            logger.info(f"PDF size: {pdf_size / 1024:.1f} KB")

            result = {
                "local_path": temp_pdf_path,
                "filename": pdf_filename,
                "unguessable_id": unguessable_id,
                "size_bytes": pdf_size,
                "upload_success": False,
                "remote_path": None,
                "url": None,
            }

            if upload:
                # Upload to bucket
                upload_result = self._upload_pdf(temp_pdf_path, pdf_filename, unguessable_id)
                result.update(upload_result)

            return result

        except Exception as e:
            # Clean up temp files on error
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
            if temp_html_from_url and os.path.exists(temp_html_from_url):
                os.unlink(temp_html_from_url)
            raise RuntimeError(f"Failed to render PDF: {str(e)}") from e

    def _upload_pdf(
        self, local_pdf_path: str, pdf_filename: str, unguessable_id: str
    ) -> Dict[str, Any]:
        """Upload PDF to bucket and return upload results"""
        try:
            # Generate remote path using PDF configuration
            remote_path = self._generate_remote_path(pdf_filename, unguessable_id)

            logger.info(f"Uploading PDF to bucket: {remote_path}")

            # Upload using Buckia client
            upload_success = self.client.upload_file(local_pdf_path, remote_path)

            if upload_success:
                # Generate public URL
                url = self._generate_public_url(remote_path)
                logger.info(f"PDF uploaded successfully: {url}")

                return {"upload_success": True, "remote_path": remote_path, "url": url}
            else:
                logger.error("Failed to upload PDF to bucket")
                return {"upload_success": False, "remote_path": remote_path, "url": None}

        except Exception as e:
            logger.error(f"Error uploading PDF: {str(e)}")
            return {"upload_success": False, "remote_path": None, "url": None, "error": str(e)}

    def _generate_remote_path(self, pdf_filename: str, unguessable_id: str) -> str:
        """Generate remote path for PDF based on configuration"""
        # Get path template from PDF config
        path_template = self.pdf_config.get("path_template", "{id}/{name}")

        # Replace placeholders
        remote_path = path_template.format(id=unguessable_id, name=pdf_filename)

        # Ensure path doesn't start with /
        return remote_path.lstrip("/")

    def _generate_public_url(self, remote_path: str) -> str:
        """Generate public URL for the uploaded PDF"""
        # Get base URL from PDF config
        base_url = self.pdf_config.get("base_url", "")

        if base_url:
            # Ensure base_url doesn't end with / and remote_path doesn't start with /
            base_url = base_url.rstrip("/")
            remote_path = remote_path.lstrip("/")
            return f"{base_url}/{remote_path}"
        else:
            # Fallback to bucket-specific URL generation
            return f"https://{self.config.bucket_name}/{remote_path}"

    def _process_html_for_pdf(self, html_file_path: str, css_override: Optional[str] = None) -> str:
        """
        Process HTML file to fix relative paths for WeasyPrint

        Args:
            html_file_path: Path to the original HTML file

        Returns:
            Path to processed HTML file (may be same as input if no changes needed)
        """
        import re

        # Read the HTML content
        with open(html_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Get the directory containing the HTML file
        html_dir = os.path.dirname(html_file_path)

        # Find the dist directory (go up until we find _astro)
        dist_dir = html_dir
        while dist_dir and dist_dir != "/":
            potential_astro = os.path.join(dist_dir, "_astro")
            if os.path.exists(potential_astro):
                break
            dist_dir = os.path.dirname(dist_dir)

        if not dist_dir or not os.path.exists(os.path.join(dist_dir, "_astro")):
            logger.warning("Could not find _astro directory, using original HTML")
            return html_file_path

        # Convert to absolute path
        dist_dir = os.path.abspath(dist_dir)
        logger.info(f"Found dist directory: {dist_dir}")

        # Convert relative /_astro/ URLs to absolute file:// URLs
        def fix_astro_url(match):
            quote_char = match.group(1)  # Capture the quote character (" or ')
            relative_path = match.group(2)
            absolute_path = os.path.join(dist_dir, relative_path.lstrip("/"))

            if os.path.exists(absolute_path):
                file_url = f"file://{absolute_path}"
                logger.debug(f"Fixed URL: {relative_path} -> {file_url}")
                return f"{quote_char}{file_url}{quote_char}"
            else:
                logger.warning(f"File not found: {absolute_path}")
                return match.group(0)  # Return original if file doesn't exist

        # Fix CSS, image, and script URLs - handle both single and double quotes
        original_content = html_content
        html_content = re.sub(r'(["\'])(\/_astro\/[^"\']+)\1', fix_astro_url, html_content)

        # Also handle any other asset paths that might not be in _astro
        def fix_asset_url(match):
            quote_char = match.group(1)
            relative_path = match.group(2)

            # Skip external URLs (http/https)
            if relative_path.startswith(("http://", "https://", "//")):
                return match.group(0)

            # Skip data URLs
            if relative_path.startswith("data:"):
                return match.group(0)

            # Handle root-relative paths that might be assets
            if relative_path.startswith("/") and not relative_path.startswith("//"):
                absolute_path = os.path.join(dist_dir, relative_path.lstrip("/"))
                if os.path.exists(absolute_path):
                    file_url = f"file://{absolute_path}"
                    logger.debug(f"Fixed asset URL: {relative_path} -> {file_url}")
                    return f"{quote_char}{file_url}{quote_char}"

            return match.group(0)  # Return original if not a local asset

        # Fix other asset URLs (like /assets/*, /favicon.*, etc.)
        html_content = re.sub(
            r'(["\'])(\/[^"\']*\.(css|js|png|jpg|jpeg|gif|svg|webp|ico|pdf))\1',
            fix_asset_url,
            html_content,
        )

        # Apply CSS override if provided
        if css_override:
            html_content = _inject_css_override(html_content, css_override)

        # If no changes were made and no CSS override, return original file
        if html_content == original_content and not css_override:
            logger.info("No URL fixes or CSS overrides needed")
            return html_file_path

        # Create temporary file with processed HTML
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as temp_html:
            temp_html.write(html_content)
            temp_html_path = temp_html.name

        logger.info(f"Created processed HTML: {temp_html_path}")
        return temp_html_path


def render_pdf_local_only(
    html_file_path: str,
    pdf_filename: str,
    unguessable_id: str,
    output_dir: Optional[str] = None,
    pdf_config: Optional[Dict[str, Any]] = None,
    css_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Render PDF locally without uploading to bucket

    Args:
        html_file_path: Path to HTML file to render OR URL to fetch HTML from
        pdf_filename: Name for output PDF file
        unguessable_id: Unique identifier for PDF path
        output_dir: Directory to save PDF (defaults to current directory)
        pdf_config: PDF configuration settings
        css_override: Optional path to CSS file to inject

    Returns:
        Dictionary with render results
    """
    if not WEASYPRINT_AVAILABLE:
        raise ImportError(
            "WeasyPrint is required for PDF generation. Install with: pip install buckia[pdf]"
        )

    # Handle URLs by fetching HTML content first
    temp_html_from_url = None
    if _is_url(html_file_path):
        logger.info(f"Detected URL input: {html_file_path}")
        temp_html_from_url = _fetch_html_from_url(html_file_path)
        actual_html_path = temp_html_from_url
    else:
        # Regular file path
        if not os.path.exists(html_file_path):
            raise FileNotFoundError(f"HTML file not found: {html_file_path}")
        actual_html_path = html_file_path

    # Ensure PDF filename has .pdf extension
    if not pdf_filename.endswith(".pdf"):
        pdf_filename += ".pdf"

    # Determine output directory
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, pdf_filename)
    else:
        output_path = pdf_filename

    logger.info(f"Rendering HTML to PDF (local-only): {html_file_path} -> {output_path}")

    # Default WeasyPrint options
    default_options = {
        "presentational_hints": True,
        "optimize_images": True,
        "pdf_version": "1.7",
        "pdf_forms": False,
    }

    # Merge with user-provided options
    pdf_config = pdf_config or {}
    weasyprint_options = {**default_options, **pdf_config.get("weasyprint_options", {})}

    try:
        # Process HTML to fix relative paths
        # Pass original URL if input was a URL for proper relative path resolution
        source_url = html_file_path if _is_url(html_file_path) else None
        processed_html_path = _process_html_for_pdf_standalone(
            actual_html_path, css_override, source_url
        )

        # Render HTML to PDF using WeasyPrint
        html_doc = weasyprint.HTML(filename=processed_html_path)
        html_doc.write_pdf(output_path, **weasyprint_options)

        # Clean up processed HTML if it's different from original
        if processed_html_path != actual_html_path:
            os.unlink(processed_html_path)

        # Clean up temporary HTML file from URL if it was created
        if temp_html_from_url:
            os.unlink(temp_html_from_url)
            logger.info(f"Cleaned up temporary HTML file: {temp_html_from_url}")

        # Get file size for logging
        pdf_size = os.path.getsize(output_path)
        logger.info(f"PDF rendered successfully: {output_path} ({pdf_size / 1024:.1f} KB)")

        return {
            "local_path": output_path,
            "filename": pdf_filename,
            "unguessable_id": unguessable_id,
            "size_bytes": pdf_size,
            "upload_success": False,  # Not uploaded in local-only mode
            "remote_path": None,
            "url": None,
            "local_only": True,
        }

    except Exception as e:
        # Clean up temporary HTML file from URL on error
        if temp_html_from_url and os.path.exists(temp_html_from_url):
            os.unlink(temp_html_from_url)
        raise RuntimeError(f"Failed to render PDF: {str(e)}") from e


def _inject_css_override(html_content: str, css_override_path: str) -> str:
    """
    Inject additional CSS into HTML content

    Args:
        html_content: Original HTML content
        css_override_path: Path to CSS file to inject

    Returns:
        HTML content with injected CSS
    """
    if not os.path.exists(css_override_path):
        logger.warning(f"CSS override file not found: {css_override_path}")
        return html_content

    try:
        with open(css_override_path, "r", encoding="utf-8") as f:
            css_content = f.read()

        # Inject CSS before closing </head> tag
        css_injection = (
            f'<style type="text/css">\n/* Buckia CSS Override */\n{css_content}\n</style>'
        )

        if "</head>" in html_content:
            html_content = html_content.replace("</head>", f"{css_injection}\n</head>")
            logger.info(f"Injected CSS override from: {css_override_path}")
        else:
            logger.warning("No </head> tag found, CSS override not injected")

    except Exception as e:
        logger.error(f"Failed to inject CSS override: {e}")

    return html_content


def _process_html_for_pdf_standalone(
    html_file_path: str, css_override: Optional[str] = None, source_url: Optional[str] = None
) -> str:
    """
    Standalone version of HTML processing for local-only mode

    Args:
        html_file_path: Path to the HTML file (may be temporary file from URL)
        css_override: Optional path to CSS file to inject
        source_url: Original URL if HTML was fetched from URL (for relative path resolution)
    """
    import re

    # Read the HTML content
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Determine if we're processing HTML from a URL or local file
    if source_url:
        logger.info(f"Processing HTML from URL: {source_url}")
        # For URLs, we'll resolve relative paths relative to the source URL
        base_url = source_url
    else:
        logger.info(f"Processing HTML from local file: {html_file_path}")
        # For local files, find the dist directory (go up until we find _astro)
        html_dir = os.path.dirname(html_file_path)
        dist_dir = html_dir
        while dist_dir and dist_dir != "/":
            potential_astro = os.path.join(dist_dir, "_astro")
            if os.path.exists(potential_astro):
                break
            dist_dir = os.path.dirname(dist_dir)

        if not dist_dir or not os.path.exists(os.path.join(dist_dir, "_astro")):
            logger.warning("Could not find _astro directory, using original HTML")
            return html_file_path

        # Convert to absolute path
        dist_dir = os.path.abspath(dist_dir)
        logger.info(f"Found dist directory: {dist_dir}")
        base_url = None

    # Define URL fixing functions based on context (URL vs file)
    if source_url:
        # URL context: resolve relative paths relative to the source URL
        def fix_url_path(match):
            quote_char = match.group(1)
            relative_path = match.group(2)

            # Skip external URLs (http/https)
            if relative_path.startswith(("http://", "https://", "//")):
                return match.group(0)

            # Skip data URLs
            if relative_path.startswith("data:"):
                return match.group(0)

            # Resolve relative to source URL
            resolved_url = urljoin(base_url, relative_path)
            logger.debug(f"Fixed URL: {relative_path} -> {resolved_url}")
            return f"{quote_char}{resolved_url}{quote_char}"

        # Apply URL fixing to all asset references
        original_content = html_content

        # Fix all relative paths (including ../../assets/*, /_astro/*, /assets/*, etc.)
        html_content = re.sub(
            r'(["\'])((?:\.\.\/)*[^"\']*\.(css|js|png|jpg|jpeg|gif|svg|webp|ico|pdf)|\/[^"\']*\.(css|js|png|jpg|jpeg|gif|svg|webp|ico|pdf))\1',
            fix_url_path,
            html_content,
        )

        # Also fix /_astro/ paths specifically
        html_content = re.sub(r'(["\'])(\/_astro\/[^"\']+)\1', fix_url_path, html_content)

    else:
        # File context: convert to file:// URLs for local files
        def fix_astro_url(match):
            quote_char = match.group(1)
            relative_path = match.group(2)
            absolute_path = os.path.join(dist_dir, relative_path.lstrip("/"))

            if os.path.exists(absolute_path):
                file_url = f"file://{absolute_path}"
                logger.debug(f"Fixed URL: {relative_path} -> {file_url}")
                return f"{quote_char}{file_url}{quote_char}"
            else:
                logger.warning(f"File not found: {absolute_path}")
                return match.group(0)

        def fix_asset_url(match):
            quote_char = match.group(1)
            relative_path = match.group(2)

            # Skip external URLs (http/https)
            if relative_path.startswith(("http://", "https://", "//")):
                return match.group(0)

            # Skip data URLs
            if relative_path.startswith("data:"):
                return match.group(0)

            # Handle root-relative paths that might be assets
            if relative_path.startswith("/") and not relative_path.startswith("//"):
                absolute_path = os.path.join(dist_dir, relative_path.lstrip("/"))
                if os.path.exists(absolute_path):
                    file_url = f"file://{absolute_path}"
                    logger.debug(f"Fixed asset URL: {relative_path} -> {file_url}")
                    return f"{quote_char}{file_url}{quote_char}"

            return match.group(0)

        # Apply file-based URL fixing
        original_content = html_content
        html_content = re.sub(r'(["\'])(\/_astro\/[^"\']+)\1', fix_astro_url, html_content)
        html_content = re.sub(
            r'(["\'])(\/[^"\']*\.(css|js|png|jpg|jpeg|gif|svg|webp|ico|pdf))\1',
            fix_asset_url,
            html_content,
        )

    # Apply CSS override if provided
    if css_override:
        html_content = _inject_css_override(html_content, css_override)

    # If no changes were made and no CSS override, return original file
    if html_content == original_content and not css_override:
        logger.info("No URL fixes or CSS overrides needed")
        return html_file_path

    # Create temporary file with processed HTML
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as temp_html:
        temp_html.write(html_content)
        temp_html_path = temp_html.name

    logger.info(f"Created processed HTML: {temp_html_path}")
    return temp_html_path


def render_pdf_command(
    html_file_path: str,
    bucket_name: str,
    unguessable_id: str,
    pdf_filename: str,
    config_file: Optional[str] = None,
    local_only: bool = False,
    output_dir: Optional[str] = None,
    css_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Command-line interface function for PDF rendering

    Args:
        html_file_path: Path to HTML file to render
        bucket_name: Name of bucket configuration to use
        unguessable_id: Unique identifier for PDF path
        pdf_filename: Name for output PDF file
        config_file: Optional path to config file (defaults to .buckia)
        local_only: If True, save PDF locally without uploading
        output_dir: Directory to save PDF when local_only=True (defaults to current dir)
        css_override: Path to additional CSS file to inject into HTML

    Returns:
        Dictionary with render results
    """
    # Load configuration
    if config_file and os.path.exists(config_file):
        buckia_config = BuckiaConfig.from_file(config_file)
    else:
        # Try to find .buckia file in current directory or parent directories
        config_path = find_buckia_config()
        if not config_path:
            raise FileNotFoundError("No .buckia configuration file found")
        buckia_config = BuckiaConfig.from_file(config_path)

    # Get bucket configuration
    if bucket_name not in buckia_config:
        raise ValueError(f"Bucket configuration '{bucket_name}' not found in config")

    bucket_config = buckia_config[bucket_name]

    # Handle local-only mode
    if local_only:
        return render_pdf_local_only(
            html_file_path=html_file_path,
            pdf_filename=pdf_filename,
            unguessable_id=unguessable_id,
            output_dir=output_dir,
            pdf_config=bucket_config.pdf,
            css_override=css_override,
        )

    # Create PDF renderer and render with upload
    renderer = PDFRenderer(bucket_config)
    return renderer.render_html_to_pdf(
        html_file_path, pdf_filename, unguessable_id, css_override=css_override
    )


def find_buckia_config() -> Optional[str]:
    """Find .buckia configuration file in current directory or parent directories"""
    current_dir = Path.cwd()

    # Check current directory and parents
    for directory in [current_dir] + list(current_dir.parents):
        config_path = directory / ".buckia"
        if config_path.exists():
            return str(config_path)

    return None
