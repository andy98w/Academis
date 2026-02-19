"""
User progress service for storing and retrieving user learning data.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from .rag_service import db

logger = logging.getLogger(__name__)


def get_user_progress_collection():
    """Get the user_progress collection from MongoDB."""
    if db is None:
        raise ValueError("MongoDB connection not available")
    return db.user_progress


async def save_quiz_progress(
    user_id: str,
    subject: str,
    chapter_id: str,
    answers: Dict[int, int],
    submitted: Dict[int, bool],
    score: Optional[int] = None,
    total: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Save or update quiz progress for a user.

    Args:
        user_id: Firebase UID
        subject: Subject code (e.g., 'micro', 'macro')
        chapter_id: Chapter identifier (e.g., '1.1')
        answers: Dict mapping question index to selected answer
        submitted: Dict mapping question index to submission status
        score: Number of correct answers (optional)
        total: Total number of questions (optional)

    Returns:
        The saved progress document
    """
    collection = get_user_progress_collection()

    progress_doc = {
        "user_id": user_id,
        "subject": subject,
        "chapter_id": chapter_id,
        "type": "quiz",
        "answers": answers,
        "submitted": submitted,
        "updated_at": datetime.now(timezone.utc),
    }

    if score is not None:
        progress_doc["score"] = score
    if total is not None:
        progress_doc["total"] = total
        if score is not None:
            progress_doc["completed"] = score == total
            progress_doc["completed_at"] = datetime.now(timezone.utc)

    # Upsert the progress document
    result = collection.update_one(
        {"user_id": user_id, "subject": subject, "chapter_id": chapter_id, "type": "quiz"},
        {"$set": progress_doc, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
        upsert=True,
    )

    logger.info(f"Saved quiz progress for user {user_id}, {subject}/{chapter_id}")
    return progress_doc


async def save_scroll_position(
    user_id: str,
    subject: str,
    chapter_id: str,
    scroll_position: int,
) -> Dict[str, Any]:
    """Save scroll position for a chapter."""
    collection = get_user_progress_collection()

    progress_doc = {
        "user_id": user_id,
        "subject": subject,
        "chapter_id": chapter_id,
        "type": "scroll",
        "scroll_position": scroll_position,
        "updated_at": datetime.now(timezone.utc),
    }

    collection.update_one(
        {"user_id": user_id, "subject": subject, "chapter_id": chapter_id, "type": "scroll"},
        {"$set": progress_doc, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
        upsert=True,
    )

    return progress_doc


async def get_user_progress(
    user_id: str,
    subject: Optional[str] = None,
    chapter_id: Optional[str] = None,
    progress_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get user progress with optional filtering.

    Args:
        user_id: Firebase UID
        subject: Filter by subject (optional)
        chapter_id: Filter by chapter (optional)
        progress_type: Filter by type ('quiz' or 'scroll') (optional)

    Returns:
        List of progress documents
    """
    collection = get_user_progress_collection()

    query: Dict[str, Any] = {"user_id": user_id}
    if subject:
        query["subject"] = subject
    if chapter_id:
        query["chapter_id"] = chapter_id
    if progress_type:
        query["type"] = progress_type

    cursor = collection.find(query, {"_id": 0})
    results = list(cursor)

    return results


async def get_chapter_quiz_progress(
    user_id: str,
    subject: str,
    chapter_id: str,
) -> Optional[Dict[str, Any]]:
    """Get quiz progress for a specific chapter."""
    collection = get_user_progress_collection()

    result = collection.find_one(
        {"user_id": user_id, "subject": subject, "chapter_id": chapter_id, "type": "quiz"},
        {"_id": 0},
    )

    return result


async def get_chapter_scroll_position(
    user_id: str,
    subject: str,
    chapter_id: str,
) -> Optional[int]:
    """Get scroll position for a specific chapter."""
    collection = get_user_progress_collection()

    result = collection.find_one(
        {"user_id": user_id, "subject": subject, "chapter_id": chapter_id, "type": "scroll"},
        {"scroll_position": 1, "_id": 0},
    )

    return result.get("scroll_position") if result else None


async def get_user_stats(user_id: str) -> Dict[str, Any]:
    """
    Get overall statistics for a user.

    Returns:
        Dict with stats like chapters_completed, total_score, etc.
    """
    collection = get_user_progress_collection()

    # Get all quiz progress for the user
    quiz_progress = list(collection.find(
        {"user_id": user_id, "type": "quiz"},
        {"score": 1, "total": 1, "completed": 1, "subject": 1, "_id": 0},
    ))

    chapters_completed = sum(1 for p in quiz_progress if p.get("completed"))
    total_questions = sum(p.get("total", 0) for p in quiz_progress if p.get("total"))
    total_correct = sum(p.get("score", 0) for p in quiz_progress if p.get("score"))

    # Calculate average score
    average_score = (total_correct / total_questions * 100) if total_questions > 0 else 0

    # Get subjects studied
    subjects = list(set(p.get("subject") for p in quiz_progress if p.get("subject")))

    return {
        "chapters_completed": chapters_completed,
        "total_questions_answered": total_questions,
        "total_correct": total_correct,
        "average_score": round(average_score, 1),
        "subjects_studied": subjects,
    }


async def delete_user_progress(user_id: str) -> int:
    """Delete all progress for a user. Returns count of deleted documents."""
    collection = get_user_progress_collection()
    result = collection.delete_many({"user_id": user_id})
    logger.info(f"Deleted {result.deleted_count} progress documents for user {user_id}")
    return result.deleted_count
