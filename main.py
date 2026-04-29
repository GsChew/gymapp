from fastapi import FastAPI
from src.auth.router import router as auth_router
from src.workouts.router import router as workout_router
from src.exercises.router import router as exercise_router
from src.workoutExercise.router import router as workoutexercise_router
from src.notifications.router import router as notification_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(workout_router)
app.include_router(exercise_router)
app.include_router(workoutexercise_router)
app.include_router(notification_router)