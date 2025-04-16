# supabase.py — инициализация базы и переменных сеанса
import os
from datetime import datetime
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

SESSION_TIMEOUT = 600  # 10 минут бездействия
user_last_active = {}  # Отслеживание активности пользователей

# Модератор на дежурстве
moderator_on_duty = {"id": None}
