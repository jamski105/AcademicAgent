"""
Error Formatter für Academic Agent v2.0

User-friendly Error Messages mit:
- Clear error descriptions
- Actionable suggestions
- Resume instructions
"""

from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box


class ErrorFormatter:
    """Format errors for user-friendly display"""

    def __init__(self):
        """Initialize Error Formatter"""
        self.console = Console()

        # Error type mappings
        self.error_types = {
            "API_ERROR": "API Connection Error",
            "PDF_ERROR": "PDF Download Error",
            "EXTRACTION_ERROR": "Quote Extraction Error",
            "VALIDATION_ERROR": "Validation Error",
            "CONFIG_ERROR": "Configuration Error",
            "NETWORK_ERROR": "Network Error",
            "TIMEOUT_ERROR": "Timeout Error",
            "AUTH_ERROR": "Authentication Error"
        }

        # Suggestions for common errors
        self.suggestions = {
            "API_ERROR": [
                "Check your internet connection",
                "Verify API keys in config/api_config.yaml",
                "Try again in a few minutes (rate limit?)"
            ],
            "PDF_ERROR": [
                "Check if DOI is valid",
                "Try alternative PDF sources",
                "Check institutional access (DBIS credentials)"
            ],
            "EXTRACTION_ERROR": [
                "Check if PDF is valid",
                "Verify Anthropic API key",
                "Try with fallback mode (keyword extraction)"
            ],
            "CONFIG_ERROR": [
                "Check config/api_config.yaml syntax",
                "Verify all required fields",
                "See INSTALLATION.md for setup guide"
            ],
            "NETWORK_ERROR": [
                "Check your internet connection",
                "Check if firewall blocks connections",
                "Try with VPN if behind proxy"
            ],
            "TIMEOUT_ERROR": [
                "API might be slow, try again",
                "Increase timeout in config",
                "Check if service is down"
            ],
            "AUTH_ERROR": [
                "Check API keys in config/api_config.yaml",
                "Verify credentials for DBIS/Shibboleth",
                "See API_SETUP.md for key registration"
            ]
        }

    def format_error(
        self,
        error_type: str,
        error_message: str,
        phase: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Format and print error message

        Args:
            error_type: Error type (API_ERROR, PDF_ERROR, etc.)
            error_message: Detailed error message
            phase: Optional phase name
            session_id: Optional session ID for resume
            context: Optional additional context
        """
        # Get friendly error title
        error_title = self.error_types.get(error_type, "Error")
        if phase:
            error_title = f"{error_title} in {phase}"

        # Build error content
        content = f"[red bold]{error_message}[/red bold]\n"

        # Add context if provided
        if context:
            content += "\n[yellow]Context:[/yellow]\n"
            for key, value in context.items():
                content += f"  • {key}: {value}\n"

        # Get suggestions
        suggestions = self.suggestions.get(error_type, [])
        if suggestions:
            content += "\n[cyan]💡 Suggestions:[/cyan]\n"
            for i, suggestion in enumerate(suggestions, 1):
                content += f"  {i}. {suggestion}\n"

        # Add resume instructions
        if session_id:
            content += f"\n[green]📝 Session saved: {session_id}[/green]\n"
            content += "[green]You can resume later with this session ID[/green]"

        # Print error panel
        panel = Panel(
            content,
            title=f"❌ {error_title}",
            border_style="red",
            box=box.ROUNDED
        )

        self.console.print("\n")
        self.console.print(panel)

    def format_warning(
        self,
        warning_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Format and print warning message

        Args:
            warning_message: Warning message
            context: Optional context
        """
        content = f"[yellow]{warning_message}[/yellow]"

        if context:
            content += "\n\n[dim]Details:[/dim]\n"
            for key, value in context.items():
                content += f"  • {key}: {value}\n"

        panel = Panel(
            content,
            title="⚠️  Warning",
            border_style="yellow",
            box=box.ROUNDED
        )

        self.console.print("\n")
        self.console.print(panel)

    def format_critical_error(
        self,
        error_message: str,
        traceback: Optional[str] = None
    ) -> None:
        """
        Format critical error (show traceback)

        Args:
            error_message: Error message
            traceback: Optional traceback string
        """
        content = f"[red bold]{error_message}[/red bold]\n"

        if traceback:
            content += f"\n[dim]{traceback}[/dim]"

        content += "\n\n[yellow]Please report this issue at:[/yellow]"
        content += "\n[blue underline]https://github.com/anthropics/claude-code/issues[/blue underline]"

        panel = Panel(
            content,
            title="🚨 Critical Error",
            border_style="red bold",
            box=box.DOUBLE
        )

        self.console.print("\n")
        self.console.print(panel)

    def format_validation_errors(
        self,
        errors: List[Dict[str, str]]
    ) -> None:
        """
        Format validation errors (multiple)

        Args:
            errors: List of error dicts with 'field' and 'message'
        """
        table = Table(title="Validation Errors", box=box.ROUNDED)

        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Error", style="red")

        for error in errors:
            field = error.get("field", "Unknown")
            message = error.get("message", "Validation failed")
            table.add_row(field, message)

        self.console.print("\n")
        self.console.print(table)

    def print_help_message(self, topic: str):
        """
        Print help message for common issues

        Args:
            topic: Help topic (api_keys, pdf_download, etc.)
        """
        help_texts = {
            "api_keys": """
[cyan bold]API Keys Setup[/cyan bold]

1. Create free API keys:
   • CrossRef: No key needed ✅
   • OpenAlex: mailto@yourdomain.com ✅
   • Semantic Scholar: https://www.semanticscholar.org/product/api
   • Anthropic: https://console.anthropic.com/

2. Add keys to config/api_config.yaml:
   ```yaml
   api_keys:
     anthropic_api_key: "your-key-here"
     openalex_email: "your@email.com"
   ```

3. See API_SETUP.md for detailed guide
            """,
            "pdf_download": """
[cyan bold]PDF Download Issues[/cyan bold]

1. Open Access Papers:
   • ~40% available via Unpaywall (no setup needed)

2. Institutional Access:
   • Configure DBIS/Shibboleth credentials:
     export TIB_USERNAME="your-username"
     export TIB_PASSWORD="your-password"

3. Success Rate:
   • Unpaywall: ~40%
   • CORE: ~10% (needs API key)
   • DBIS Browser: ~35-40% (needs credentials)
   • Total: 85-90% expected
            """,
            "resume": """
[cyan bold]Resuming a Session[/cyan bold]

Your session is automatically saved and can be resumed:

1. Note your session ID from error message
2. Run: /research --resume SESSION_ID
3. Workflow continues from last checkpoint

Checkpoints are saved after each phase:
  ✅ Phase 1: Search complete
  ✅ Phase 2: Ranking complete
  ✅ Phase 3: PDFs downloaded
  ✅ Phase 4: Quotes extracted
            """
        }

        help_text = help_texts.get(topic, "[red]Unknown help topic[/red]")

        panel = Panel(
            help_text,
            title=f"📚 Help: {topic.replace('_', ' ').title()}",
            border_style="cyan",
            box=box.ROUNDED
        )

        self.console.print("\n")
        self.console.print(panel)


# ============================================
# Convenience Functions
# ============================================

def print_error(
    error_type: str,
    message: str,
    phase: Optional[str] = None,
    session_id: Optional[str] = None
):
    """
    Quick error printing

    Args:
        error_type: Error type
        message: Error message
        phase: Optional phase
        session_id: Optional session ID
    """
    formatter = ErrorFormatter()
    formatter.format_error(error_type, message, phase, session_id)


def print_warning(message: str, context: Optional[Dict[str, Any]] = None):
    """
    Quick warning printing

    Args:
        message: Warning message
        context: Optional context
    """
    formatter = ErrorFormatter()
    formatter.format_warning(message, context)


# ============================================
# Test Code
# ============================================

if __name__ == "__main__":
    """Test Error Formatter"""
    import time

    print("Testing Error Formatter...")

    formatter = ErrorFormatter()

    # Test 1: API Error
    formatter.format_error(
        error_type="API_ERROR",
        error_message="Failed to connect to CrossRef API",
        phase="Phase 2: Search",
        session_id="abc123",
        context={"api": "CrossRef", "status_code": 503}
    )

    time.sleep(1)

    # Test 2: Warning
    formatter.format_warning(
        "3 PDFs could not be downloaded (paywalled)",
        context={"failed": 3, "total": 15}
    )

    time.sleep(1)

    # Test 3: Validation Errors
    formatter.format_validation_errors([
        {"field": "api_config.yaml", "message": "Missing anthropic_api_key"},
        {"field": "research_modes.yaml", "message": "Invalid mode: 'super-fast'"}
    ])

    time.sleep(1)

    # Test 4: Help
    formatter.print_help_message("api_keys")

    print("\n✅ Error Formatter test completed!")
