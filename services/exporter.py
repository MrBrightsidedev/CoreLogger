"""Export functionality for thoughts to various formats."""

import json
import csv
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from models.thought import ThoughtQuery
from services.logger import ThoughtLogger


class ThoughtExporter:
    """Handles exporting thoughts to different formats."""
    
    def __init__(self):
        self.thought_logger = ThoughtLogger()
    
    async def export_thoughts(
        self,
        db: Session,
        format_type: str,
        output_path: str,
        query_filters: Optional[ThoughtQuery] = None
    ) -> Dict[str, Any]:
        """Export thoughts to specified format."""
        
        # Get thoughts based on filters
        if query_filters is None:
            query_filters = ThoughtQuery(
                page=1, 
                size=10000,
                min_importance=None,
                max_importance=None,
                order_by="timestamp",
                order_desc=True
            )  # Get all
        else:
            # Create a new query with updated size for export
            query_dict = query_filters.model_dump()
            query_dict['size'] = 10000
            query_filters = ThoughtQuery(**query_dict)
        
        thoughts_response = self.thought_logger.get_thoughts(db, query_filters)
        
        # Extract thoughts from response
        if hasattr(thoughts_response, 'thoughts'):
            thoughts = thoughts_response.thoughts
        else:
            thoughts = thoughts_response
            
        # Convert to list if needed
        if not isinstance(thoughts, list):
            thoughts = [thoughts] if thoughts else []
        
        if not thoughts:
            return {
                "success": False,
                "message": "No thoughts found matching the criteria",
                "exported_count": 0
            }
        
        # Export based on format
        if format_type.lower() == "json":
            return await self._export_to_json(thoughts, output_path)
        elif format_type.lower() == "csv":
            return await self._export_to_csv(thoughts, output_path)
        else:
            return {
                "success": False,
                "message": f"Unsupported format: {format_type}. Use 'json' or 'csv'",
                "exported_count": 0
            }
    
    async def _export_to_json(self, thoughts: List[Any], output_path: str) -> Dict[str, Any]:
        """Export thoughts to JSON format."""
        try:
            # Convert thoughts to serializable format
            thoughts_data = []
            for thought in thoughts:
                thought_dict = {
                    "id": str(thought.id),
                    "category": thought.category,
                    "content": thought.content,
                    "tags": thought.tags,
                    "emotion": thought.emotion,
                    "importance": thought.importance,
                    "novelty_score": getattr(thought, 'novelty_score', None),
                    "created_at": thought.created_at.isoformat() if thought.created_at else None,
                    "updated_at": thought.updated_at.isoformat() if thought.updated_at else None
                }
                thoughts_data.append(thought_dict)
            
            # Create export metadata
            export_data = {
                "export_metadata": {
                    "format": "json",
                    "exported_at": datetime.now().isoformat(),
                    "total_thoughts": len(thoughts_data),
                    "source": "CoreLogger"
                },
                "thoughts": thoughts_data
            }
            
            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "message": f"Successfully exported {len(thoughts_data)} thoughts to {output_path}",
                "exported_count": len(thoughts_data),
                "output_path": str(output_file.absolute())
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error exporting to JSON: {str(e)}",
                "exported_count": 0
            }
    
    async def _export_to_csv(self, thoughts: List[Any], output_path: str) -> Dict[str, Any]:
        """Export thoughts to CSV format."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'id', 'category', 'content', 'tags', 'emotion', 
                    'importance', 'novelty_score', 'created_at', 'updated_at'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header
                writer.writeheader()
                
                # Write thoughts
                for thought in thoughts:
                    writer.writerow({
                        'id': str(thought.id),
                        'category': thought.category,
                        'content': thought.content,
                        'tags': ','.join(thought.tags) if thought.tags else '',
                        'emotion': thought.emotion or '',
                        'importance': thought.importance or '',
                        'novelty_score': getattr(thought, 'novelty_score', ''),
                        'created_at': thought.created_at.isoformat() if thought.created_at else '',
                        'updated_at': thought.updated_at.isoformat() if thought.updated_at else ''
                    })
            
            return {
                "success": True,
                "message": f"Successfully exported {len(thoughts)} thoughts to {output_path}",
                "exported_count": len(thoughts),
                "output_path": str(output_file.absolute())
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error exporting to CSV: {str(e)}",
                "exported_count": 0
            }
    
    def get_export_statistics(self, thoughts: List[Any]) -> Dict[str, Any]:
        """Generate statistics about the thoughts being exported."""
        if not thoughts:
            return {"total": 0}
        
        stats = {
            "total": len(thoughts),
            "categories": {},
            "emotions": {},
            "tags": {},
            "date_range": {
                "earliest": None,
                "latest": None
            },
            "importance": {
                "average": 0.0,
                "min": None,
                "max": None
            }
        }
        
        importance_values = []
        dates = []
        
        for thought in thoughts:
            # Categories
            category = thought.category
            stats["categories"][category] = stats["categories"].get(category, 0) + 1
            
            # Emotions
            if thought.emotion:
                emotion = thought.emotion
                stats["emotions"][emotion] = stats["emotions"].get(emotion, 0) + 1
            
            # Tags
            if thought.tags:
                for tag in thought.tags:
                    stats["tags"][tag] = stats["tags"].get(tag, 0) + 1
            
            # Importance
            if thought.importance is not None:
                importance_values.append(thought.importance)
            
            # Dates
            if thought.created_at:
                dates.append(thought.created_at)
        
        # Calculate importance stats
        if importance_values:
            stats["importance"]["average"] = sum(importance_values) / len(importance_values)
            stats["importance"]["min"] = min(importance_values)
            stats["importance"]["max"] = max(importance_values)
        
        # Calculate date range
        if dates:
            stats["date_range"]["earliest"] = min(dates).isoformat()
            stats["date_range"]["latest"] = max(dates).isoformat()
        
        return stats
