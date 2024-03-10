import google.auth

# Get credentials and refresh token
credentials = google.oauth2.service_account.Credentials.from_service_account_file(
    filename="web/database/v_assist_auth.json",
    scopes=["https://www.googleapis.com/auth/cloud-platform"]  
)
refresh_token = credentials.authorized_user.refresh_token
