from typing import Dict, List, Any
from .textbook_service import MICRO_TOC, MACRO_TOC

class SubjectConfig:
    """Configuration for different AP subjects"""
    
    SUBJECTS = {
        "micro": {
            "name": "Microeconomics",
            "full_name": "AP Microeconomics",
            "description": "Study individual economic behavior, markets, and business decisions.",
            "toc": MICRO_TOC,
            "collection_prefix": "economics",
            "agent_prefix": "[Microeconomics Question]"
        },
        "macro": {
            "name": "Macroeconomics", 
            "full_name": "AP Macroeconomics",
            "description": "Explore national economies, economic indicators, and government policies.",
            "toc": MACRO_TOC,
            "collection_prefix": "economics",
            "agent_prefix": "[Macroeconomics Question]"
        },
        "biology": {
            "name": "Biology",
            "full_name": "AP Biology", 
            "description": "Explore life sciences, cellular processes, genetics, and evolution.",
            "toc": None,  # Will be loaded from database or file
            "collection_prefix": "biology",
            "agent_prefix": "[Biology Question]"
        },
        "physics": {
            "name": "Physics",
            "full_name": "AP Physics",
            "description": "Study mechanics, thermodynamics, waves, and modern physics.",
            "toc": None,
            "collection_prefix": "physics", 
            "agent_prefix": "[Physics Question]"
        },
        "chemistry": {
            "name": "Chemistry",
            "full_name": "AP Chemistry",
            "description": "Understand atomic structure, chemical bonding, and reactions.",
            "toc": None,
            "collection_prefix": "chemistry",
            "agent_prefix": "[Chemistry Question]"
        }
    }
    
    @classmethod
    def get_subject_config(cls, subject: str) -> Dict[str, Any]:
        """Get configuration for a specific subject"""
        if subject not in cls.SUBJECTS:
            raise ValueError(f"Subject '{subject}' not found. Available subjects: {list(cls.SUBJECTS.keys())}")
        return cls.SUBJECTS[subject]
    
    @classmethod
    def get_available_subjects(cls) -> List[str]:
        """Get list of all available subjects"""
        return list(cls.SUBJECTS.keys())
    
    @classmethod
    def is_valid_subject(cls, subject: str) -> bool:
        """Check if a subject is valid"""
        return subject in cls.SUBJECTS
    
    @classmethod
    def get_subject_name(cls, subject: str) -> str:
        """Get display name for a subject"""
        return cls.get_subject_config(subject)["name"]
    
    @classmethod
    def get_full_subject_name(cls, subject: str) -> str:
        """Get full display name for a subject"""
        return cls.get_subject_config(subject)["full_name"]