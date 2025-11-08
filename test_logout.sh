#!/bin/bash

echo "=== Test de la fonctionnalité de Logout ==="
echo ""

# 1. Login
echo "1. Connexion..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@test.com&password=test123")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['refresh_token'])")

echo "Access Token: ${ACCESS_TOKEN:0:50}..."
echo "Refresh Token: ${REFRESH_TOKEN:0:50}..."
echo ""

# 2. Vérifier que le token fonctionne
echo "2. Vérification que le token fonctionne..."
ME_RESPONSE=$(curl -s -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Réponse /me: $ME_RESPONSE"
echo ""

# 3. Logout
echo "3. Déconnexion (logout)..."
LOGOUT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")

echo "Réponse logout: $LOGOUT_RESPONSE"
echo ""

# 4. Essayer d'utiliser le token révoqué
echo "4. Tentative d'utilisation du token révoqué..."
ME_RESPONSE_AFTER=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Réponse: $ME_RESPONSE_AFTER"
echo ""

echo "=== Test terminé ==="
