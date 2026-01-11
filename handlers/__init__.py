# Handlers package
from handlers.common import router as common_router
from handlers.profile import router as profile_router
from handlers.water import router as water_router
from handlers.food import router as food_router
from handlers.workout import router as workout_router
from handlers.progress import router as progress_router

# Список всех роутеров для регистрации
all_routers = [
    common_router,
    profile_router,
    water_router,
    food_router,
    workout_router,
    progress_router,
]


