#!/bin/bash

echo "=== Test du blocage du Refresh Token ==="
echo ""

# 1. Login
echo "1. Connexion..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@test.com&password=test123")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['refresh_token'])")

echo "Tokens obtenus"
echo ""

# 2. Logout
echo "2. Déconnexion (logout)..."
LOGOUT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")

echo "Réponse logout: $LOGOUT_RESPONSE"
echo ""

# 3. Essayer d'utiliser le refresh token révoqué
echo "3. Tentative d'utilisation du refresh token révoqué..."
REFRESH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")

echo "Réponse: $REFRESH_RESPONSE"
echo ""

echo "=== Test terminé ==="
