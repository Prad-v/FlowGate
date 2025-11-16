"""Config diff service for comparing agent configs with standard templates"""

import difflib
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class ConfigDiffService:
    """Service for calculating differences between agent and standard configs"""
    
    @staticmethod
    def calculate_unified_diff(agent_config: str, standard_config: str, context_lines: int = 3) -> str:
        """Generate git-style unified diff between two configs
        
        Args:
            agent_config: Agent's effective configuration YAML
            standard_config: Standard/template configuration YAML
            context_lines: Number of context lines to include around changes
        
        Returns:
            Unified diff string (git-style)
        """
        agent_lines = agent_config.splitlines(keepends=True)
        standard_lines = standard_config.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            standard_lines,
            agent_lines,
            fromfile='standard_config.yaml',
            tofile='agent_config.yaml',
            lineterm='',
            n=context_lines
        )
        
        return ''.join(diff)
    
    @staticmethod
    def calculate_line_diff(agent_config: str, standard_config: str) -> Dict[str, Any]:
        """Calculate line-by-line differences
        
        Args:
            agent_config: Agent's effective configuration YAML
            standard_config: Standard/template configuration YAML
        
        Returns:
            Dictionary with line-by-line diff information
        """
        agent_lines = agent_config.splitlines()
        standard_lines = standard_config.splitlines()
        
        # Use SequenceMatcher for detailed comparison
        matcher = difflib.SequenceMatcher(None, standard_lines, agent_lines)
        
        added_lines = []
        removed_lines = []
        modified_lines = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            elif tag == 'delete':
                # Lines removed
                for i in range(i1, i2):
                    removed_lines.append({
                        'line_number': i + 1,
                        'content': standard_lines[i]
                    })
            elif tag == 'insert':
                # Lines added
                for j in range(j1, j2):
                    added_lines.append({
                        'line_number': j + 1,
                        'content': agent_lines[j]
                    })
            elif tag == 'replace':
                # Lines modified
                for i in range(i1, i2):
                    removed_lines.append({
                        'line_number': i + 1,
                        'content': standard_lines[i]
                    })
                for j in range(j1, j2):
                    added_lines.append({
                        'line_number': j + 1,
                        'content': agent_lines[j]
                    })
        
        return {
            'added': added_lines,
            'removed': removed_lines,
            'modified': modified_lines
        }
    
    @staticmethod
    def calculate_stats(agent_config: str, standard_config: str) -> Dict[str, int]:
        """Calculate diff statistics
        
        Args:
            agent_config: Agent's effective configuration YAML
            standard_config: Standard/template configuration YAML
        
        Returns:
            Dictionary with statistics: added, removed, modified, total_lines
        """
        agent_lines = agent_config.splitlines()
        standard_lines = standard_config.splitlines()
        
        matcher = difflib.SequenceMatcher(None, standard_lines, agent_lines)
        
        added = 0
        removed = 0
        modified = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            elif tag == 'delete':
                removed += (i2 - i1)
            elif tag == 'insert':
                added += (j2 - j1)
            elif tag == 'replace':
                removed += (i2 - i1)
                added += (j2 - j1)
                modified += min(i2 - i1, j2 - j1)
        
        return {
            'added': added,
            'removed': removed,
            'modified': modified,
            'total_agent_lines': len(agent_lines),
            'total_standard_lines': len(standard_lines),
            'similarity_ratio': matcher.ratio()
        }
    
    @staticmethod
    def compare_configs(agent_config: str, standard_config: str) -> Dict[str, Any]:
        """Compare two configs and return comprehensive diff information
        
        Args:
            agent_config: Agent's effective configuration YAML
            standard_config: Standard/template configuration YAML
        
        Returns:
            Dictionary with unified diff, line diff, and statistics
        """
        unified_diff = ConfigDiffService.calculate_unified_diff(agent_config, standard_config)
        line_diff = ConfigDiffService.calculate_line_diff(agent_config, standard_config)
        stats = ConfigDiffService.calculate_stats(agent_config, standard_config)
        
        return {
            'unified_diff': unified_diff,
            'line_diff': line_diff,
            'stats': stats,
            'agent_config': agent_config,
            'standard_config': standard_config
        }

