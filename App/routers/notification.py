from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Annotated

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)

def write_log(email: str, message=""):
    with open("log.txt", mode="a") as email_file:
        content = f"notification for {email}: {message}"
        email_file.write(content)

def get_query(background_tasks: BackgroundTasks, q: str | None = None):
    if q:
        message = f"found query: {q}\n"
        print(" message:", message)
        background_tasks.add_task(write_log,"" , message)
    return q


@router.post("/send/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks, q: Annotated[str, Depends(get_query)]):
    message = f"message to {email}\n"
    background_tasks.add_task(write_log, email, message)
    return {"message": "Notification sent in the background"}