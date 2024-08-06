from langchain_core.pydantic_v1 import BaseModel, Field

class ToSearchAgent(BaseModel):
    """Transfers work to a specialized agent to search for real estates."""

    request: str = Field(
        description="Any additional information or requests from the user regarding their search criteria."
    )

class ToAppointmentAgent(BaseModel):
    """Transfers work to a specialized agent to manage appointments: book, edit, cancel, show appointments etc."""

    request: str = Field(
        description="Any additional information or requests from the user regarding their search criteria."
    )
    
class CompleteOrEscalate(BaseModel):
    """A tool to mark the current task as completed and/or to escalate control of the 
    dialog to the main assistant, who can re-route the dialog based on the user's needs."""

    cancel: bool = True
    reason: str

    class Config:
        schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User changed their mind about the current task.",
            },
            "example 2": {
                "cancel": True,
                "reason": "I have fully completed the task.",
            }
        }