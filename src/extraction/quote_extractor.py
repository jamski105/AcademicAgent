"""
Quote Extractor für Academic Agent v2.0

⚠️ PARTIALLY DEPRECATED ⚠️

LLM-based extraction is now handled by: .claude/agents/quote_extractor.md (Claude Code Agent)

What's deprecated:
- Anthropic SDK calls (QuoteExtractor class)
- Direct LLM integration

What's still used:
- Quote dataclass (data structure)
- QuoteValidator (validation logic)
- PDF parsing utilities

The quote_extractor Agent (Haiku 4.5) is spawned by linear_coordinator during Phase 6.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from src.extraction.pdf_parser import PDFParser, parse_pdf
from src.extraction.quote_validator import QuoteValidator

# Anthropic SDK (lazy import)
try:
    import anthropic
except ImportError:
    anthropic = None


@dataclass
class Quote:
    """Extracted quote"""
    text: str
    page: int
    section: Optional[str] = None
    word_count: int = 0
    relevance_score: float = 0.0
    reasoning: Optional[str] = None
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    validated: bool = False


@dataclass
class ExtractionResult:
    """Result of quote extraction"""
    success: bool
    quotes: List[Quote]
    total_quotes: int
    extraction_quality: str = "unknown"
    warnings: List[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class QuoteExtractor:
    """Extract quotes from PDFs using Haiku"""

    # Agent prompt file
    AGENT_PROMPT_FILE = Path(__file__).parent.parent.parent / ".claude" / "agents" / "quote_extractor.md"

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        use_llm: bool = True,
        max_quotes_per_paper: int = 3,
        max_words_per_quote: int = 25
    ):
        """
        Initialize Quote Extractor

        Args:
            anthropic_api_key: Optional Anthropic API key (None = from ENV)
            use_llm: Use Haiku LLM (False = fallback keyword extraction)
            max_quotes_per_paper: Maximum quotes to extract per paper
            max_words_per_quote: Maximum words per quote
        """
        self.api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.use_llm = use_llm and self.api_key is not None
        self.max_quotes = max_quotes_per_paper
        self.max_words = max_words_per_quote

        # Initialize clients
        self.pdf_parser = PDFParser()
        self.validator = QuoteValidator(max_word_count=max_words_per_quote)

        # Initialize Anthropic client
        if self.use_llm and anthropic:
            self.anthropic_client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.anthropic_client = None
            if self.use_llm:
                print("⚠️ Anthropic SDK not available, falling back to keyword extraction")
                self.use_llm = False

    def extract_quotes(
        self,
        pdf_path: Path,
        research_query: str,
        paper_title: Optional[str] = None,
        academic_context: Optional[Dict[str, Any]] = None
    ) -> ExtractionResult:
        """
        Extract quotes from PDF

        Args:
            pdf_path: Path to PDF file
            research_query: Research query
            paper_title: Optional paper title
            academic_context: Optional academic context (keywords, etc.)

        Returns:
            ExtractionResult with extracted quotes
        """
        if not pdf_path.exists():
            return ExtractionResult(
                success=False,
                quotes=[],
                total_quotes=0,
                error=f"PDF not found: {pdf_path}"
            )

        try:
            # Parse PDF
            pdf_doc = self.pdf_parser.parse(pdf_path)

            if self.use_llm:
                # Use Haiku for extraction
                quotes = self._extract_with_haiku(
                    pdf_doc,
                    research_query,
                    paper_title,
                    academic_context
                )
            else:
                # Fallback: Keyword-based extraction
                quotes = self._extract_with_keywords(
                    pdf_doc,
                    research_query
                )

            # Validate quotes
            validated_quotes = self._validate_quotes(quotes, pdf_doc)

            return ExtractionResult(
                success=True,
                quotes=validated_quotes,
                total_quotes=len(validated_quotes),
                extraction_quality="high" if self.use_llm else "medium"
            )

        except Exception as e:
            return ExtractionResult(
                success=False,
                quotes=[],
                total_quotes=0,
                error=f"Extraction failed: {str(e)}"
            )

    def _extract_with_haiku(
        self,
        pdf_doc,
        research_query: str,
        paper_title: Optional[str],
        academic_context: Optional[Dict[str, Any]]
    ) -> List[Quote]:
        """Extract quotes using Haiku"""

        # Truncate PDF text if too long (Haiku has 200K context limit)
        pdf_text = pdf_doc.full_text
        max_chars = 150000  # Leave room for prompt

        if len(pdf_text) > max_chars:
            # Take first pages (abstract, intro usually most relevant)
            pdf_text = pdf_text[:max_chars] + "\n\n[... PDF truncated ...]"

        # Build prompt
        prompt = self._build_haiku_prompt(
            pdf_text,
            research_query,
            paper_title,
            academic_context
        )

        # Call Haiku
        response = self.anthropic_client.messages.create(
            model="claude-haiku-4-20250122",
            max_tokens=4000,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse response
        response_text = response.content[0].text
        quotes = self._parse_haiku_response(response_text)

        return quotes

    def _build_haiku_prompt(
        self,
        pdf_text: str,
        research_query: str,
        paper_title: Optional[str],
        academic_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for Haiku"""

        # Read agent prompt template
        if self.AGENT_PROMPT_FILE.exists():
            agent_instructions = self.AGENT_PROMPT_FILE.read_text()
            # Extract just the instructions part (not the frontmatter)
            agent_instructions = agent_instructions.split("---", 2)[-1]
        else:
            agent_instructions = "Extract 2-3 relevant quotes from the PDF."

        prompt = f"""
{agent_instructions}

# Task

Extract {self.max_quotes} highly relevant quotes from this paper.

**Research Query:** {research_query}
**Paper Title:** {paper_title or "Unknown"}

**PDF Text:**
{pdf_text}

**Requirements:**
- Extract exactly {self.max_quotes} quotes (or fewer if not enough relevant content)
- Each quote must be ≤{self.max_words} words
- Quotes must be direct text from the paper (no paraphrasing!)
- Focus on passages that directly address the research query

**Output Format (JSON):**
```json
{{
  "quotes": [
    {{
      "text": "exact quote from paper",
      "page": 1,
      "section": "Introduction",
      "word_count": 10,
      "relevance_score": 0.95,
      "reasoning": "why this quote is relevant",
      "context_before": "30-50 words before the quote",
      "context_after": "30-50 words after the quote"
    }}
  ]
}}
```

Extract the quotes now.
"""

        return prompt

    def _parse_haiku_response(self, response_text: str) -> List[Quote]:
        """Parse Haiku JSON response"""

        # Extract JSON from response
        json_match = response_text.find("{")
        if json_match == -1:
            return []

        json_end = response_text.rfind("}") + 1
        json_text = response_text[json_match:json_end]

        try:
            data = json.loads(json_text)
            quotes_data = data.get("quotes", [])

            quotes = []
            for q in quotes_data:
                quote = Quote(
                    text=q.get("text", ""),
                    page=q.get("page", 1),
                    section=q.get("section"),
                    word_count=q.get("word_count", len(q.get("text", "").split())),
                    relevance_score=q.get("relevance_score", 0.0),
                    reasoning=q.get("reasoning"),
                    context_before=q.get("context_before"),
                    context_after=q.get("context_after"),
                    validated=False
                )
                quotes.append(quote)

            return quotes

        except json.JSONDecodeError:
            print(f"⚠️ Failed to parse Haiku response as JSON")
            return []

    def _extract_with_keywords(
        self,
        pdf_doc,
        research_query: str
    ) -> List[Quote]:
        """Fallback: Extract quotes using keyword matching"""

        quotes = []
        query_words = research_query.lower().split()

        # Search each page
        for page in pdf_doc.pages:
            sentences = page.text.split('.')

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                # Check if sentence contains query words
                sentence_lower = sentence.lower()
                matches = sum(1 for word in query_words if word in sentence_lower)

                if matches >= len(query_words) / 2:  # At least half the query words
                    # Check word count
                    word_count = len(sentence.split())
                    if word_count <= self.max_words:
                        quote = Quote(
                            text=sentence,
                            page=page.page_number,
                            word_count=word_count,
                            relevance_score=matches / len(query_words),
                            validated=False
                        )
                        quotes.append(quote)

                        if len(quotes) >= self.max_quotes:
                            return quotes

        return quotes[:self.max_quotes]

    def _validate_quotes(self, quotes: List[Quote], pdf_doc) -> List[Quote]:
        """Validate quotes against PDF"""

        validated_quotes = []

        for quote in quotes:
            # Validate
            validation = self.validator.validate_quote(quote.text, pdf_doc)

            if validation.is_valid:
                # Update quote with validation info
                quote.validated = True
                quote.page = validation.page_number or quote.page
                quote.context_before = validation.context_before or quote.context_before
                quote.context_after = validation.context_after or quote.context_after

                validated_quotes.append(quote)
            else:
                print(f"⚠️ Quote validation failed: {validation.error}")

        return validated_quotes


# ============================================
# Convenience Functions
# ============================================

def extract_quotes_from_pdf(
    pdf_path: Path,
    research_query: str,
    max_quotes: int = 3,
    use_llm: bool = True
) -> List[Quote]:
    """
    Simple helper to extract quotes

    Args:
        pdf_path: Path to PDF
        research_query: Research query
        max_quotes: Maximum quotes to extract
        use_llm: Use Haiku LLM

    Returns:
        List of Quote objects
    """
    extractor = QuoteExtractor(
        use_llm=use_llm,
        max_quotes_per_paper=max_quotes
    )

    result = extractor.extract_quotes(pdf_path, research_query)

    return result.quotes if result.success else []


# ============================================
# Test Code
# ============================================

if __name__ == "__main__":
    """Test Quote Extractor"""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python quote_extractor.py <pdf-path> <research-query>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    research_query = sys.argv[2]

    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    print("Testing Quote Extractor...")

    extractor = QuoteExtractor(use_llm=True)
    result = extractor.extract_quotes(pdf_path, research_query)

    print(f"\n✂️ Extraction Result:")
    print(f"   Success: {result.success}")
    print(f"   Total Quotes: {result.total_quotes}")
    print(f"   Quality: {result.extraction_quality}")

    for i, quote in enumerate(result.quotes, 1):
        print(f"\n   Quote {i}:")
        print(f"      Text: '{quote.text}'")
        print(f"      Page: {quote.page}")
        print(f"      Words: {quote.word_count}")
        print(f"      Validated: {quote.validated}")
        print(f"      Relevance: {quote.relevance_score:.2f}")

    if result.error:
        print(f"\n   Error: {result.error}")

    print("\n✅ Quote Extractor test completed!")
