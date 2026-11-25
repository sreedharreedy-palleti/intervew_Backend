from datetime import datetime, timezone
from typing import Dict, Any, List
from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from intervew_app.schemas.admin_schemas import InterviewScheduleRequest
from Resume_Analysis.email_templates import notify_interview_scheduled


async def service_admin_list_interviews(db: AsyncIOMotorDatabase) -> List[Dict[str, Any]]:
    """
    Returns all candidate interview sessions for administrative monitoring and review.
    """
    cursor = db["interviews"].find().sort("started_at", -1)
    interviews = []
    async for doc in cursor:
        interviews.append({
            "id": str(doc["_id"]),
            "interview_token": doc.get("interview_token"),
            "candidate_name": doc.get("candidate_name"),
            "candidate_email": doc.get("candidate_email"),
            "course_title": doc.get("course_title"),
            "course_id": doc.get("course_id"),
            "assignment_score": doc.get("assignment_score"),
            "status": doc.get("status", "in_progress"),
            "precheck_verified": doc.get("precheck_verified", False),
            "current_question_index": doc.get("current_question_index", 0),
            "total_questions": len(doc.get("questions", [])),
            "started_at": doc.get("started_at"),
            "completed_at": doc.get("completed_at"),
            "final_report": doc.get("final_report"),
        })
    return interviews


async def service_admin_schedule_interview(
    interview_token: str,
    payload: InterviewScheduleRequest,
    db: AsyncIOMotorDatabase
) -> Dict[str, Any]:
    """
    Admin scheduling of the live AI interview slot for a candidate.
    """
    session = await db["interviews"].find_one({"interview_token": interview_token})
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    now_iso = datetime.now(timezone.utc).isoformat()
    update_data = {
        "scheduled_datetime": payload.interview_datetime,
        "duration_minutes": payload.duration_minutes or 45,
        "scheduled_at": now_iso,
    }

    await db["interviews"].update_one(
        {"interview_token": interview_token},
        {"$set": update_data}
    )

    course_id = session.get("course_id")
    candidate_email = session.get("candidate_email")
    candidate_name = session.get("candidate_name") or "Candidate"
    course_title = session.get("course_title") or "AI Technical Track"

    if course_id and ObjectId.is_valid(course_id):
        course_doc = await db["courses"].find_one({"_id": ObjectId(course_id)})
        if course_doc:
            course_title = course_doc.get("title") or course_title
            for s in course_doc.get("enrolled_students", []):
                if s.get("interview_token") == interview_token or (session.get("user_id") and s.get("user_id") == session.get("user_id")):
                    candidate_email = candidate_email or s.get("email")
                    candidate_name = candidate_name or s.get("name")
                    break

        await db["courses"].update_one(
            {
                "_id": ObjectId(course_id),
                "enrolled_students.interview_token": interview_token
            },
            {
                "$set": {
                    "enrolled_students.$.interview_datetime": payload.interview_datetime,
                    "enrolled_students.$.interview_duration_minutes": payload.duration_minutes or 45,
                }
            }
        )

    # Dispatch official interview schedule email notification
    email_dispatched = False
    if candidate_email:
        try:
            email_dispatched = notify_interview_scheduled(
                email=candidate_email,
                name=candidate_name,
                course=course_title,
                interview_datetime=payload.interview_datetime,
                interview_token=interview_token,
                duration_minutes=payload.duration_minutes or 45,
            )
        except Exception as exc:
            print(f"[INTERVIEW SCHEDULE EMAIL ERROR] {exc}")

    return {
        "interview_token": interview_token,
        "scheduled_datetime": payload.interview_datetime,
        "duration_minutes": payload.duration_minutes or 45,
        "email_sent": email_dispatched,
        "message": f"Interview successfully scheduled for {payload.interview_datetime}."
    }

