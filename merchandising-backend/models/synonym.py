"""
Synonym Models
==============

Pydantic models for synonym management.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4


class SynonymGroup(BaseModel):
    """A group of synonymous terms."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique synonym group ID")
    name: str = Field(..., description="Human-readable name for this synonym group")
    base_term: str = Field(..., description="Primary term (e.g., 'faucet')")
    synonyms: List[str] = Field(..., description="Synonym terms (e.g., ['tap', 'spigot'])")
    enabled: bool = Field(default=True, description="Whether synonym is active")
    createdBy: str = Field(default="system", description="User who created the synonym")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: Optional[datetime] = Field(default=None)
    
    def to_solr_format(self) -> str:
        """Convert to Solr synonym format for Azure AI Search.
        
        Format: term1, term2, term3 => base_term
        Example: tap, spigot => faucet
        """
        all_terms = [self.base_term] + self.synonyms
        # Bidirectional synonym mapping
        return ", ".join(all_terms)


class SynonymCreate(BaseModel):
    """Create new synonym group request."""
    name: str
    base_term: str
    synonyms: List[str]
    enabled: bool = True
    createdBy: str = "system"


class SynonymUpdate(BaseModel):
    """Update existing synonym group request."""
    name: Optional[str] = None
    base_term: Optional[str] = None
    synonyms: Optional[List[str]] = None
    enabled: Optional[bool] = None


class SynonymListResponse(BaseModel):
    """List of synonym groups response."""
    synonyms: List[SynonymGroup]
    total: int


class SynonymTestRequest(BaseModel):
    """Test a search query with synonyms."""
    query: str = Field(..., description="Search query to test")


class SynonymTestResponse(BaseModel):
    """Test results showing impact of synonyms."""
    query: str
    expanded_terms: List[str]
    sample_results: List[dict]


class BulkSynonymImport(BaseModel):
    """Bulk import synonyms from CSV format."""
    synonyms: List[SynonymCreate]
    overwrite_existing: bool = Field(default=False, description="Overwrite existing synonyms")
