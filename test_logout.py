"""
Script de test pour la fonctionnalité de logout.
Ce script teste le cycle complet: login -> logout -> tentative d'utilisation du token révoqué
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_logout_flow():
    """Test le flux complet de logout"""

    print("=== Test de la fonctionnalité de Logout ===\n")

    # 1. Login
    print("1. Connexion avec admin@kuilinga.com...")
    login_data = {
        "username": "admin@kuilinga.com",
        "password": "admin123"
    }

    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            data=login_data
        )

        if login_response.status_code != 200:
            print(f"   ❌ Échec de connexion: {login_response.status_code}")
            print(f"   Réponse: {login_response.text}")
            return

        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        print(f"   ✅ Connexion réussie!")
        print(f"   Access Token: {access_token[:50]}...")
        print(f"   Refresh Token: {refresh_token[:50]}...\n")

    except Exception as e:
        print(f"   ❌ Erreur lors de la connexion: {str(e)}")
        return

    # 2. Vérifier que le token fonctionne (GET /auth/me)
    print("2. Vérification que le token fonctionne...")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)

        if me_response.status_code == 200:
            user = me_response.json()
            print(f"   ✅ Token valide - Utilisateur: {user['email']}\n")
        else:
            print(f"   ❌ Token invalide: {me_response.status_code}")
            return

    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification: {str(e)}")
        return

    # 3. Logout
    print("3. Déconnexion (logout)...")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        logout_data = {"refresh_token": refresh_token}

        logout_response = requests.post(
            f"{BASE_URL}/auth/logout",
            headers=headers,
            json=logout_data
        )

        if logout_response.status_code == 200:
            result = logout_response.json()
            print(f"   ✅ Déconnexion réussie!")
            print(f"   Réponse: {json.dumps(result, indent=2)}\n")
        else:
            print(f"   ❌ Échec de déconnexion: {logout_response.status_code}")
            print(f"   Réponse: {logout_response.text}")
            return

    except Exception as e:
        print(f"   ❌ Erreur lors de la déconnexion: {str(e)}")
        return

    # 4. Essayer d'utiliser le token révoqué
    print("4. Tentative d'utilisation du token révoqué...")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)

        if me_response.status_code == 403 or me_response.status_code == 401:
            print(f"   ✅ Token correctement révoqué - Accès refusé (code: {me_response.status_code})\n")
        else:
            print(f"   ❌ PROBLÈME: Le token révoqué fonctionne encore! (code: {me_response.status_code})")
            print(f"   Réponse: {me_response.text}")

    except Exception as e:
        print(f"   ❌ Erreur lors du test: {str(e)}")
        return

    # 5. Essayer d'utiliser le refresh token révoqué
    print("5. Tentative d'utilisation du refresh token révoqué...")
    try:
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json=refresh_data
        )

        if refresh_response.status_code == 401:
            print(f"   ✅ Refresh token correctement révoqué - Accès refusé\n")
        else:
            print(f"   ❌ PROBLÈME: Le refresh token révoqué fonctionne encore! (code: {refresh_response.status_code})")
            print(f"   Réponse: {refresh_response.text}")

    except Exception as e:
        print(f"   ❌ Erreur lors du test: {str(e)}")
        return

    print("=== Test terminé avec succès! ===")


if __name__ == "__main__":
    test_logout_flow()
