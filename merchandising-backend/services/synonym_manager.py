"""
Synonym Manager Service
========================

Manages synonym groups and syncs with Azure AI Search.
"""

import logging
from typing import List, Optional
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SynonymMap
)

from config import settings
from models.synonym import SynonymGroup

logger = logging.getLogger(__name__)


class SynonymManager:
    """Manages synonyms and syncs with Azure AI Search."""
    
    SYNONYM_MAP_NAME = "product-synonyms"
    
    def __init__(self):
        """Initialize Azure AI Search client."""
        self.search_client = SearchIndexClient(
            endpoint=settings.azure_search_endpoint,
            credential=AzureKeyCredential(settings.azure_search_key)
        )
    
    def _convert_to_solr_format(self, synonym_groups: List[SynonymGroup]) -> str:
        """Convert synonym groups to Solr format for Azure AI Search.
        
        Solr format (one per line):
        faucet, tap, spigot
        refrigerator, fridge, icebox
        """
        enabled_groups = [sg for sg in synonym_groups if sg.enabled]
        solr_lines = [sg.to_solr_format() for sg in enabled_groups]
        return "\n".join(solr_lines)
    
    async def sync_to_azure_search(self, synonym_groups: List[SynonymGroup]) -> bool:
        """Sync all synonym groups to Azure AI Search.
        
        Args:
            synonym_groups: All synonym groups from Cosmos DB
            
        Returns:
            True if sync was successful, False otherwise
        """
        try:
            # Convert to Solr format
            solr_synonyms = self._convert_to_solr_format(synonym_groups)
            
            # Create or update synonym map
            synonym_map = SynonymMap(
                name=self.SYNONYM_MAP_NAME,
                synonyms=solr_synonyms
            )
            
            # Try to create, if exists then update
            try:
                self.search_client.create_synonym_map(synonym_map)
                logger.info(f"✅ Created synonym map: {self.SYNONYM_MAP_NAME}")
            except Exception as create_error:
                if "already exists" in str(create_error).lower():
                    self.search_client.create_or_update_synonym_map(synonym_map)
                    logger.info(f"✅ Updated synonym map: {self.SYNONYM_MAP_NAME}")
                else:
                    raise create_error
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to sync synonyms to Azure Search: {e}")
            return False
    
    async def get_current_synonym_map(self) -> Optional[str]:
        """Get the current synonym map from Azure AI Search.
        
        Returns:
            Current synonyms in Solr format, or None if not found
        """
        try:
            synonym_map = self.search_client.get_synonym_map(self.SYNONYM_MAP_NAME)
            return synonym_map.synonyms
        except Exception as e:
            logger.warning(f"No existing synonym map found: {e}")
            return None
    
    async def delete_synonym_map(self) -> bool:
        """Delete the synonym map from Azure AI Search.
        
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            self.search_client.delete_synonym_map(self.SYNONYM_MAP_NAME)
            logger.info(f"✅ Deleted synonym map: {self.SYNONYM_MAP_NAME}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete synonym map: {e}")
            return False
    
    def parse_solr_format(self, solr_text: str) -> List[dict]:
        """Parse Solr format synonyms back to structured format.
        
        Args:
            solr_text: Synonyms in Solr format (one group per line)
            
        Returns:
            List of dicts with base_term and synonyms
        """
        results = []
        for line in solr_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            
            # Split by comma
            terms = [t.strip() for t in line.split(",")]
            if len(terms) > 1:
                results.append({
                    "base_term": terms[0],
                    "synonyms": terms[1:]
                })
        
        return results
