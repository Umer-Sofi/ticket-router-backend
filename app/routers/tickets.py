"""HTTP layer for ticket routing. Knows about requests/responses only —
the actual work is delegated to router_service. Thin on purpose.
"""

from fastapi import APIRouter

from app.schemas.ticket import RouteResult, TicketRequest
from app.services.router_service import route_message

# prefix => every route here lives under /api. tags => grouping in /docs.
router = APIRouter(prefix="/api", tags=["tickets"])


@router.post("/route-ticket", response_model=list[RouteResult])
def route_ticket_endpoint(request: TicketRequest) -> list[RouteResult]:
    return route_message(request.text)
