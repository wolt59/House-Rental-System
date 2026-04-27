from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auth, properties, users, bookings, maintenance, complaints,
    messages, news, audit_logs, contracts, payments, property_images, stats,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])
api_router.include_router(complaints.router, prefix="/complaints", tags=["complaints"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(property_images.router, prefix="/property-images", tags=["property_images"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(audit_logs.router, prefix="/admin/audit-logs", tags=["audit_logs"])
