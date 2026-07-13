"""HTTP layer for ticket routing. Knows about requests/responses only —
the actual work is delegated to router_service. Thin on purpose.
"""

import time

from fastapi import APIRouter

from app.schemas.ticket import RouteResult, TicketRequest
from app.services.router_service import route_ticket

# prefix => every route here lives under /api. tags => grouping in /docs.
router = APIRouter(prefix="/api", tags=["tickets"])


@router.post("/route-ticket", response_model=RouteResult)
def route_ticket_endpoint(request: TicketRequest) -> RouteResult:
    # perf_counter = monotonic stopwatch, correct tool for measuring durations.
    start = time.perf_counter()
    result = route_ticket(request.text)
    result.processing_time_ms = round((time.perf_counter() - start) * 1000, 1)
    return result
