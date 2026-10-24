# Este archivo reúne los routers para que FastAPI publique todos los controladores bajo /api/v1.
"""Controladores HTTP de QrPass."""
from fastapi import APIRouter
from app.controllers.sistema import router as sistema_router
from app.controllers.autenticacion import auth_router
from app.controllers.conductor import driver_router
from app.controllers.pasajero import router as pasajero_router, demo_router
from app.controllers.administracion import admin_router

router = APIRouter(prefix="/api/v1")
router.include_router(sistema_router)
router.include_router(auth_router)
router.include_router(driver_router)
router.include_router(demo_router)
router.include_router(pasajero_router)
router.include_router(admin_router)
