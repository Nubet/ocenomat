import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.integrations.llm.protocol import LLMError
from app.modules.ai.schemas import AssistantRequest, AssistantResponse
from app.modules.ai.service import answer_question, refusal
from app.modules.assessments.router import assessment_detail
from app.modules.assessments.schemas import ResultResponse
from app.modules.knowledge.retriever import PostgresKnowledgeRetriever
from app.modules.users.models import User
from app.modules.users.router import get_current_user

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.post("/assistant", response_model=AssistantResponse)
def assistant(
    data: AssistantRequest,
    request: Request,
    response: Response,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> AssistantResponse:
    response.headers["Cache-Control"] = "private, no-store"
    try:
        assessment = None
        if data.assessment_id is not None:
            assessment = assessment_detail(data.assessment_id, user, session, response)
            if data.assessment_kind not in ("unspecified", assessment.kind):
                raise HTTPException(422, "Assessment kind does not match context")
            data = data.model_copy(update={"assessment_kind": assessment.kind})
        result_question = data.task == "assessment_result" or bool(
            re.search(
                r"\b(oblicz\w*|policz\w*|średni\w*|sredni\w*)\b|"
                r"\b(mój|moj|mojej|tej|tego|bieżąc\w*)\b.*\bwynik\w*\b|"
                r"\bwynik\w*\b.*\b(mój|moj|mojej|tej|tego|oceny)\b",
                data.question,
                re.IGNORECASE,
            )
        )
        if result_question:
            if assessment is None:
                return refusal(data)
            return AssistantResponse(
                status="answered",
                mode=data.mode,
                result=ResultResponse.model_validate(
                    assessment.result, from_attributes=True
                ),
                limitations=[
                    "Wynik pochodzi z silnika reguł i zapisanych decyzji "
                    "przełożonego, nie z LLM."
                ],
            )
        answer = answer_question(
            data, PostgresKnowledgeRetriever(session), request.app.state.llm_provider
        )
        if assessment is not None:
            session.expire_all()
            assessment_detail(data.assessment_id, user, session, response)
        return answer
    except LLMError as error:
        status = {"timeout": 504, "rate_limited": 429, "invalid_response": 502}.get(
            error.code, 503
        )
        raise HTTPException(
            status,
            detail={"code": f"llm_{error.code}"},
            headers={"Cache-Control": "private, no-store"},
        ) from None
    except SQLAlchemyError:
        raise HTTPException(
            503,
            "Assistant data unavailable",
            headers={"Cache-Control": "private, no-store"},
        ) from None
