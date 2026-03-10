"""
Reference Linker Utility

Automatically adds hyperlinks to reference terms in answers, linking to:
- Wikipedia for general terms
- Government sites for regulatory/legal terms
- Authoritative sources for real estate/financial terms

All links open in new tabs (target="_blank")
"""

import re
from typing import Dict, List, Tuple


class ReferenceLinker:
    """
    Adds hyperlinks to reference terms in text with hover tooltips

    Features:
    - Links only first occurrence of each term
    - Hover tooltip with definition
    - Opens in new tab
    """

    # Term Definitions (for hover tooltips)
    DEFINITIONS = {
        # Regulatory and Government
        "RERA": "Real Estate Regulatory Authority - Regulates real estate sector to protect homebuyers",
        "Real Estate Regulatory Authority": "Regulates real estate sector to protect homebuyers and ensure transparency",
        "UDCPR": "Unified Development Control and Promotion Regulations - Building and planning regulations for Maharashtra",
        "Unified Development Control and Promotion Regulations": "Building and planning regulations for Maharashtra state",
        "National Building Code": "Comprehensive building code providing guidelines for regulating building construction",
        "NBC": "National Building Code - Guidelines for regulating building construction activities",
        "Bureau of Indian Standards": "National standards body of India for standardization and certification",
        "BIS": "Bureau of Indian Standards - National standards body",
        "Maharashtra RERA": "Real Estate Regulatory Authority for Maharashtra state",
        "Smart Cities Mission": "Urban renewal program by Government of India for 100 smart cities",
        "Ministry of Housing and Urban Affairs": "Central ministry responsible for housing and urban development",
        "MoHUA": "Ministry of Housing and Urban Affairs",
        "Census India": "Official census organization of India for population statistics",
        "Pune Municipal Corporation": "Local governing body for Pune city",
        "PMC": "Pune Municipal Corporation - Local governing body for Pune",
        "ISO": "International Organization for Standardization - Worldwide federation of national standards bodies",
        "International Organization for Standardization": "Worldwide federation of national standards bodies",

        # Real Estate Terms
        "FSI": "Floor Space Index - Ratio of building's total floor area to the size of the land",
        "Floor Space Index": "Ratio of building's total floor area to the size of the land upon which it is built",
        "FAR": "Floor Area Ratio - Maximum floor area allowed relative to plot size",
        "Floor Area Ratio": "Maximum floor area allowed relative to the size of the plot",
        "Carpet Area": "Usable floor area excluding walls, balconies, and common areas",
        "Built-up Area": "Total covered area including walls and balconies",
        "Super Built-up Area": "Built-up area plus proportionate common areas like lobby, lifts, stairs",
        "Saleable Area": "Area that can be sold to the buyer, typically carpet area plus walls",
        "ECS": "Equivalent Car Space - Standard unit for parking space calculations",
        "Equivalent Car Space": "Standard unit for calculating parking requirements",

        # Financial Metrics
        "IRR": "Internal Rate of Return - Rate at which NPV of cash flows equals zero",
        "Internal Rate of Return": "Discount rate at which net present value of cash flows equals zero",
        "NPV": "Net Present Value - Present value of future cash flows minus initial investment",
        "Net Present Value": "Present value of all future cash flows minus the initial investment",
        "ROI": "Return on Investment - Ratio of net profit to cost of investment",
        "Return on Investment": "Ratio of net profit to the cost of investment, expressed as percentage",
        "Absorption Rate": "Rate at which available inventory is sold in a specific time period",
        "Cap Rate": "Capitalization Rate - Net operating income divided by property value",
        "Capitalization Rate": "Rate of return on real estate investment based on income",
        "NOI": "Net Operating Income - Gross income minus operating expenses",
        "Net Operating Income": "Property's gross income minus all operating expenses",

        # Property Types
        "Studio Apartment": "Single-room apartment with combined living and sleeping area",
        "Penthouse": "Luxury apartment on the top floor of a building",
        "Duplex": "Two-floor apartment with internal staircase",
        "Triplex": "Three-floor apartment with internal staircases",

        # Urban Planning
        "Zoning": "Dividing land into zones with different permitted uses and regulations",
        "Master Plan": "Comprehensive long-term planning document for urban development",
        "Urban Planning": "Technical and political process of designing and managing land use",
        "Green Building": "Environmentally responsible and resource-efficient building",
        "LEED": "Leadership in Energy and Environmental Design - Green building certification",
        "Sustainable Development": "Development that meets present needs without compromising future generations",

        # Locations
        "Pune": "Major city in Maharashtra, India - IT and education hub",
        "Mumbai": "Capital city of Maharashtra and financial capital of India",
        "Chakan": "Industrial town near Pune known for automotive manufacturing",
        "Maharashtra": "State in western India, second-most populous state",
        "India": "South Asian country, world's largest democracy and seventh-largest by area",
    }

    # Regulatory and Government Terms
    GOVERNMENT_REFERENCES = {
        # Indian Regulations
        "RERA": "https://rera.maharashtra.gov.in/",
        "Real Estate Regulatory Authority": "https://rera.maharashtra.gov.in/",
        "UDCPR": "https://udcpr.maharashtra.gov.in/",
        "Unified Development Control and Promotion Regulations": "https://udcpr.maharashtra.gov.in/",
        "National Building Code": "https://www.bis.gov.in/national-building-code/",
        "NBC": "https://www.bis.gov.in/national-building-code/",
        "Bureau of Indian Standards": "https://www.bis.gov.in/",
        "BIS": "https://www.bis.gov.in/",
        "Maharashtra RERA": "https://rera.maharashtra.gov.in/",
        "Smart Cities Mission": "https://smartcities.gov.in/",
        "Ministry of Housing and Urban Affairs": "https://mohua.gov.in/",
        "MoHUA": "https://mohua.gov.in/",
        "Census India": "https://censusindia.gov.in/",
        "Pune Municipal Corporation": "https://www.pmc.gov.in/",
        "PMC": "https://www.pmc.gov.in/",

        # International Standards
        "ISO": "https://www.iso.org/",
        "International Organization for Standardization": "https://www.iso.org/",
    }

    # Real Estate and Financial Terms (Wikipedia)
    REAL_ESTATE_TERMS = {
        "FSI": "https://en.wikipedia.org/wiki/Floor_area_ratio",
        "Floor Space Index": "https://en.wikipedia.org/wiki/Floor_area_ratio",
        "FAR": "https://en.wikipedia.org/wiki/Floor_area_ratio",
        "Floor Area Ratio": "https://en.wikipedia.org/wiki/Floor_area_ratio",
        "Carpet Area": "https://en.wikipedia.org/wiki/Carpet_area",
        "Built-up Area": "https://en.wikipedia.org/wiki/Floor_area",
        "Super Built-up Area": "https://en.wikipedia.org/wiki/Floor_area",
        "Saleable Area": "https://en.wikipedia.org/wiki/Floor_area",
        "ECS": "https://en.wikipedia.org/wiki/Equivalent_car_space",
        "Equivalent Car Space": "https://en.wikipedia.org/wiki/Equivalent_car_space",

        # Financial Metrics
        "IRR": "https://en.wikipedia.org/wiki/Internal_rate_of_return",
        "Internal Rate of Return": "https://en.wikipedia.org/wiki/Internal_rate_of_return",
        "NPV": "https://en.wikipedia.org/wiki/Net_present_value",
        "Net Present Value": "https://en.wikipedia.org/wiki/Net_present_value",
        "ROI": "https://en.wikipedia.org/wiki/Return_on_investment",
        "Return on Investment": "https://en.wikipedia.org/wiki/Return_on_investment",
        "Absorption Rate": "https://en.wikipedia.org/wiki/Absorption_rate",
        "Cap Rate": "https://en.wikipedia.org/wiki/Capitalization_rate",
        "Capitalization Rate": "https://en.wikipedia.org/wiki/Capitalization_rate",
        "NOI": "https://en.wikipedia.org/wiki/Net_operating_income",
        "Net Operating Income": "https://en.wikipedia.org/wiki/Net_operating_income",

        # Property Types
        "Studio Apartment": "https://en.wikipedia.org/wiki/Studio_apartment",
        "Penthouse": "https://en.wikipedia.org/wiki/Penthouse_apartment",
        "Duplex": "https://en.wikipedia.org/wiki/Duplex_(building)",
        "Triplex": "https://en.wikipedia.org/wiki/Apartment#Duplex_and_triplex",

        # Urban Planning
        "Zoning": "https://en.wikipedia.org/wiki/Zoning",
        "Master Plan": "https://en.wikipedia.org/wiki/Urban_planning",
        "Urban Planning": "https://en.wikipedia.org/wiki/Urban_planning",
        "Green Building": "https://en.wikipedia.org/wiki/Green_building",
        "LEED": "https://en.wikipedia.org/wiki/Leadership_in_Energy_and_Environmental_Design",
        "Sustainable Development": "https://en.wikipedia.org/wiki/Sustainable_development",
    }

    # Cities and Locations (Wikipedia)
    LOCATION_REFERENCES = {
        "Pune": "https://en.wikipedia.org/wiki/Pune",
        "Mumbai": "https://en.wikipedia.org/wiki/Mumbai",
        "Chakan": "https://en.wikipedia.org/wiki/Chakan,_Pune",
        "Maharashtra": "https://en.wikipedia.org/wiki/Maharashtra",
        "India": "https://en.wikipedia.org/wiki/India",
    }

    def __init__(self):
        """Initialize the reference linker with combined references"""
        # Combine all reference dictionaries
        self.references = {
            **self.GOVERNMENT_REFERENCES,
            **self.REAL_ESTATE_TERMS,
            **self.LOCATION_REFERENCES
        }

        # Sort by length (longest first) to avoid partial matches
        self.sorted_terms = sorted(self.references.keys(), key=len, reverse=True)

    def add_links(self, text: str, format: str = "html") -> str:
        """
        Add hyperlinks to reference terms in text

        Args:
            text: Input text to process
            format: Output format ("html" for HTML links, "markdown" for Markdown links)

        Returns:
            Text with hyperlinks added
        """
        if not text:
            return text

        # Track which terms we've already linked (to avoid duplicate links)
        linked_positions = set()

        # Create a mutable version of text
        result = text

        # Process each term
        for term in self.sorted_terms:
            url = self.references[term]

            # Create regex pattern for case-insensitive whole-word match
            # Avoid matching if already inside a link or bold/italic markers
            pattern = r'\b(' + re.escape(term) + r')\b'

            # Find all matches
            matches = list(re.finditer(pattern, result, re.IGNORECASE))

            # Process matches in reverse order to maintain positions
            for match in reversed(matches):
                start, end = match.span()

                # Check if this position overlaps with already linked text
                if any(start <= pos < end or pos <= start < pos + 100 for pos in linked_positions):
                    continue

                # Check if already inside a markdown link or HTML tag
                before_text = result[max(0, start-10):start]
                after_text = result[end:min(len(result), end+10)]

                # Skip if inside existing link/tag
                if ('[' in before_text and '](' in after_text) or \
                   ('<a' in before_text and '</a>' in after_text) or \
                   ('**' in before_text or '**' in after_text):
                    continue

                matched_text = match.group(1)

                # Create the link based on format
                if format == "html":
                    link = f'<a href="{url}" target="_blank" rel="noopener noreferrer">{matched_text}</a>'
                else:  # markdown
                    link = f'[{matched_text}]({url}){{:target="_blank"}}'

                # Replace the match
                result = result[:start] + link + result[end:]

                # Mark this position as linked
                linked_positions.add(start)

        return result

    def add_links_preserve_bold(self, text: str, format: str = "html") -> str:
        """
        Add hyperlinks while preserving bold (**text**) formatting

        NEW FEATURES:
        - Links only FIRST occurrence of each term
        - Adds hover tooltip with definition
        - Opens in new tab

        Args:
            text: Input text with potential **bold** markers
            format: Output format

        Returns:
            Text with hyperlinks, tooltips, and bold preserved
        """
        if not text:
            return text

        # Track which TERMS we've already linked (not positions)
        # This ensures only first occurrence of each term is linked
        linked_terms = set()

        # Process each term
        result = text

        for term in self.sorted_terms:
            # Skip if we've already linked this term
            if term.lower() in linked_terms:
                continue

            url = self.references[term]
            definition = self.DEFINITIONS.get(term, "")

            # Pattern that handles both plain and bold versions
            # Matches: term, **term**, or **term
            pattern = r'\b(\*{0,2})(' + re.escape(term) + r')(\*{0,2})\b'

            # Find FIRST match only
            match = re.search(pattern, result, re.IGNORECASE)

            if match:
                start, end = match.span()

                # Check if inside existing link
                before_text = result[max(0, start-20):start]
                after_text = result[end:min(len(result), end+20)]

                if ('<a' in before_text and '</a>' in after_text):
                    continue

                # Extract parts
                leading_stars = match.group(1)
                matched_text = match.group(2)
                trailing_stars = match.group(3)

                # Create the link with tooltip
                if format == "html":
                    # HTML with title attribute for hover tooltip
                    if leading_stars or trailing_stars:
                        # Bold + Link + Tooltip
                        link = f'<strong><a href="{url}" target="_blank" rel="noopener noreferrer" title="{definition}">{matched_text}</a></strong>'
                    else:
                        # Link + Tooltip
                        link = f'<a href="{url}" target="_blank" rel="noopener noreferrer" title="{definition}">{matched_text}</a>'
                else:  # markdown
                    # For markdown, preserve ** and add link (tooltip via title)
                    link = f'{leading_stars}[{matched_text}]({url} "{definition}"){{:target="_blank"}}{trailing_stars}'

                # Replace ONLY the first match
                result = result[:start] + link + result[end:]

                # Mark this term as linked
                linked_terms.add(term.lower())

                # Also mark variations (e.g., if "FSI" is linked, mark "Floor Space Index" too)
                # This prevents linking synonyms
                if term == "FSI":
                    linked_terms.add("floor space index")
                elif term == "Floor Space Index":
                    linked_terms.add("fsi")
                elif term == "FAR":
                    linked_terms.add("floor area ratio")
                elif term == "Floor Area Ratio":
                    linked_terms.add("far")
                elif term == "RERA":
                    linked_terms.add("real estate regulatory authority")
                elif term == "Real Estate Regulatory Authority":
                    linked_terms.add("rera")
                elif term == "NBC":
                    linked_terms.add("national building code")
                elif term == "National Building Code":
                    linked_terms.add("nbc")
                elif term == "UDCPR":
                    linked_terms.add("unified development control and promotion regulations")
                elif term == "Unified Development Control and Promotion Regulations":
                    linked_terms.add("udcpr")
                elif term == "IRR":
                    linked_terms.add("internal rate of return")
                elif term == "Internal Rate of Return":
                    linked_terms.add("irr")
                elif term == "NPV":
                    linked_terms.add("net present value")
                elif term == "Net Present Value":
                    linked_terms.add("npv")
                elif term == "ROI":
                    linked_terms.add("return on investment")
                elif term == "Return on Investment":
                    linked_terms.add("roi")

        return result


# Singleton instance
_reference_linker = None


def get_reference_linker() -> ReferenceLinker:
    """Get or create singleton ReferenceLinker instance"""
    global _reference_linker
    if _reference_linker is None:
        _reference_linker = ReferenceLinker()
    return _reference_linker


def add_reference_links(text: str, format: str = "html", preserve_bold: bool = True) -> str:
    """
    Convenience function to add reference links to text

    Args:
        text: Input text
        format: "html" or "markdown"
        preserve_bold: Whether to preserve **bold** formatting

    Returns:
        Text with reference links added

    Example:
        >>> text = "The RERA regulations require FSI compliance"
        >>> add_reference_links(text)
        'The <a href="..." target="_blank">RERA</a> regulations require <a href="..." target="_blank">FSI</a> compliance'
    """
    linker = get_reference_linker()

    if preserve_bold:
        return linker.add_links_preserve_bold(text, format)
    else:
        return linker.add_links(text, format)
