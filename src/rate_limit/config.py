from schemas.RateLimit import SRateLimitRule


AUTH_LOGIN_IP = SRateLimitRule("auth_login_ip", 10, 60)
AUTH_LOGIN_EMAIL = SRateLimitRule("auth_login_email", 5, 600)
AUTH_REGISTER_IP = SRateLimitRule("auth_register_ip", 3, 60)
WORKOUTS_LIST_USER = SRateLimitRule("workouts_list_user", 100, 60)
WORKOUTS_CREATE_USER = SRateLimitRule("workouts_create_user", 30, 60)