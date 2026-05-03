"""v1 API 聚合 router"""
from fastapi import APIRouter

from app.api.v1 import auth, classes, students, pets, behaviors
from app.api.v1 import subjects, score_rules, homeworks, shop, words, pet_species, dashboard

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(classes.router)
api_router.include_router(students.router)
api_router.include_router(pets.router)
api_router.include_router(behaviors.router)
# 迭代 2 新增
api_router.include_router(subjects.router)
api_router.include_router(score_rules.router)
api_router.include_router(homeworks.router)
api_router.include_router(shop.router)
api_router.include_router(words.router)
api_router.include_router(pet_species.router)
api_router.include_router(dashboard.router)


@api_router.get("/ping", tags=["health"])
def ping():
    return {"ok": True, "service": "class-pet-api"}
