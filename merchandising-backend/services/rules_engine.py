"""
Rules Engine Service
=====================

Applies merchandising rules to search results.
"""

import logging
from typing import List, Dict, Any
from models.merchandising_rule import MerchandisingRule

logger = logging.getLogger(__name__)


class RulesEngine:
    """Engine that applies merchandising rules to search results."""
    
    @staticmethod
    def apply_rules(results: List[Dict[str, Any]], rules: List[MerchandisingRule]) -> List[Dict[str, Any]]:
        """
        Apply merchandising rules to search results.
        
        Args:
            results: List of search result dictionaries
            rules: List of applicable rules (already sorted by priority)
        
        Returns:
            Modified list of search results
        """
        if not rules:
            return results
        
        logger.info(f"Applying {len(rules)} rules to {len(results)} results")
        
        # Create a working copy
        modified_results = results.copy()
        pinned_items = []
        
        # Apply rules in priority order
        for rule in rules:
            for action in rule.actions:
                if action.type == "pin":
                    # Remove product from current position and mark for pinning
                    for i, result in enumerate(modified_results):
                        if result.get("id") == action.productId or result.get("productId") == action.productId:
                            item = modified_results.pop(i)
                            pinned_items.append((action.position - 1, item))  # Convert to 0-based
                            logger.info(f"Pinned product {action.productId} to position {action.position}")
                            break
                
                elif action.type == "boost":
                    # Increase score for this product
                    for result in modified_results:
                        if result.get("id") == action.productId or result.get("productId") == action.productId:
                            current_score = result.get("@search.score", 1.0)
                            result["@search.score"] = current_score * action.multiplier
                            logger.info(f"Boosted product {action.productId} by {action.multiplier}x")
                            break
                
                elif action.type == "bury":
                    # Move product to end
                    for i, result in enumerate(modified_results):
                        if result.get("id") == action.productId or result.get("productId") == action.productId:
                            item = modified_results.pop(i)
                            modified_results.append(item)
                            logger.info(f"Buried product {action.productId}")
                            break
        
        # Insert pinned items at their positions
        for position, item in sorted(pinned_items, key=lambda x: x[0]):
            # Ensure position is within bounds
            position = min(position, len(modified_results))
            modified_results.insert(position, item)
        
        return modified_results
    
    @staticmethod
    def preview_rules(results: List[Dict[str, Any]], rules: List[MerchandisingRule]) -> Dict[str, Any]:
        """
        Preview the effect of rules without applying them.
        
        Returns:
            Dictionary with before/after results and explanation
        """
        before = results.copy()
        after = RulesEngine.apply_rules(results, rules)
        
        changes = []
        for rule in rules:
            for action in rule.actions:
                changes.append({
                    "rule": rule.name,
                    "action": action.type,
                    "productId": action.productId,
                    "details": f"{action.type} at position {action.position}" if action.position else f"{action.type} with multiplier {action.multiplier}"
                })
        
        return {
            "before": before[:10],  # First 10 results
            "after": after[:10],
            "changes": changes,
            "rulesApplied": len(rules)
        }
