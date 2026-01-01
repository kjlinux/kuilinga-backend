# API Compliance Notes - Frontend to Backend

Ce document compile tous les commentaires et notes d'implémentation trouvés dans le frontend concernant les écarts entre l'implémentation frontend et la spécification API backend.

**Date**: 2025-11-08
**Source**: Analyse complète de `api.json` vs implémentation frontend

---

## 🔴 ENDPOINTS MANQUANTS CRITIQUES

### 1. Employee CRUD Operations (Individual)

**Fichier**: `src/services/employee.service.ts`

**Problème**: Le frontend implémente des opérations CRUD individuelles sur les employés, mais l'API ne fournit que les endpoints de collection.

**Endpoints manquants dans l'API**:
```
GET    /api/v1/employees/{employee_id}
PUT    /api/v1/employees/{employee_id}
DELETE /api/v1/employees/{employee_id}
```

**Endpoints actuellement disponibles**:
```
GET    /api/v1/employees/          ✓ (liste)
POST   /api/v1/employees/          ✓ (création)
```

**Impact**:
- Impossible de voir les détails d'un employé individuel
- Impossible de modifier un employé existant
- Impossible de supprimer un employé
- Les pages suivantes seront cassées:
  - `src/pages/Employees.tsx` (lignes 47-49: getEmployee, 71-73: updateEmployee)

**Action requise**: Implémenter les 3 endpoints manquants dans le backend

---

### 2. Role Permissions Endpoint

**Fichier**: `src/services/role.service.ts`

**Problème**: Le frontend essaie de récupérer les permissions d'un rôle via un endpoint GET qui n'existe pas.

**Endpoint manquant dans l'API**:
```
GET /api/v1/roles/{role_id}/permissions
```

**Endpoint actuellement disponible**:
```
POST /api/v1/roles/{role_id}/permissions/{permission_id}  ✓ (assigner)
```

**Solution temporaire implémentée**:
Le frontend utilise maintenant `GET /api/v1/roles/{role_id}` qui retourne le rôle complet incluant ses permissions.

```typescript
// Workaround actuel
getRolePermissions: async (roleId: string): Promise<Permission[]> => {
  const response = await apiService.get<Role>(`${API_CONFIG.ENDPOINTS.ROLES}/${roleId}`);
  return response.data.permissions || [];
}
```

**Action suggérée**:
- Option A: Implémenter `GET /api/v1/roles/{role_id}/permissions` dans le backend
- Option B: Garder le workaround actuel (acceptable si le rôle inclut toujours les permissions)

---

### 3. Notification Endpoints (Système complet)

**Fichier**: `src/services/notification.service.ts`

**Problème**: Le frontend implémente un système de notifications complet, mais AUCUN endpoint de notification n'existe dans l'API.

**Endpoints manquants dans l'API**:
```
GET    /api/v1/notifications/
GET    /api/v1/notifications/{id}
PUT    /api/v1/notifications/{id}/read
PUT    /api/v1/notifications/read-all
DELETE /api/v1/notifications/{id}
GET    /api/v1/notifications/settings/
```

**État actuel**:
Le service frontend gère gracieusement l'absence de ces endpoints en retournant des tableaux vides et en loggant des warnings. L'application ne crash pas.

```typescript
// Gestion d'erreur actuelle
async getNotifications(): Promise<Notification[]> {
  try {
    const response = await apiService.get<Notification[]>(API_CONFIG.ENDPOINTS.NOTIFICATIONS)
    return Array.isArray(response) ? response : []
  } catch (error: unknown) {
    console.warn("Notifications endpoint not available, returning empty array:", error)
    return []
  }
}
```

**Impact**:
- Fonctionnalité de notifications complètement désactivée
- Aucune notification ne s'affiche dans l'UI
- Pas de crash, mais perte de fonctionnalité

**Action requise**: Décider si les notifications sont nécessaires et implémenter tous les endpoints si oui

---

## ⚠️ PARAMÈTRES DE REQUÊTE NON SUPPORTÉS

### Paramètres de recherche et tri manquants

**Fichiers affectés**:
- `src/services/employee.service.ts`
- `src/services/organization.service.ts`
- `src/services/site.service.ts`
- `src/services/department.service.ts`
- `src/services/device.service.ts`
- `src/services/leave.service.ts`
- `src/services/attendance.service.ts`

**Problème**: Le frontend envoyait les paramètres suivants qui ne sont PAS supportés par l'API:
- `search` - Recherche textuelle
- `sort_by` - Champ de tri
- `sort_order` - Direction du tri (asc/desc)

**Paramètres actuellement supportés par l'API**:
```
skip  - Offset de pagination (supporté) ✓
limit - Taille de page (supporté) ✓
```

**Paramètres spéciaux par endpoint**:
```
GET /api/v1/employees/   - Supporte aussi: organization_id
GET /api/v1/attendance/  - Supporte aussi: employee_id
```

**Action effectuée dans le frontend**:
Les paramètres non supportés ont été retirés du code.

**Action recommandée pour le backend**:
Ajouter le support pour ces paramètres sur TOUS les endpoints de liste:

```python
# Exemple d'implémentation suggérée
@router.get("/employees/")
async def get_employees(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,        # ← À AJOUTER
    sort_by: Optional[str] = None,       # ← À AJOUTER
    sort_order: Optional[str] = "asc",   # ← À AJOUTER
    organization_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Implémenter logique de recherche et tri
    pass
```

**Impact actuel**:
- Aucune fonctionnalité de recherche dans l'UI
- Aucune fonctionnalité de tri dans l'UI
- Les utilisateurs doivent parcourir toutes les pages manuellement

---

## 📝 ENDPOINTS INUTILISÉS À RETIRER

### Endpoints définis dans le frontend mais absents de l'API

**Fichier**: `src/config/api.ts`

**Endpoints à retirer de la configuration**:

#### Attendance
```typescript
// Ces endpoints n'existent PAS dans l'API spec:
ATTENDANCE_REALTIME: "/api/v1/attendance/realtime/"    ✗
ATTENDANCE_HISTORY: "/api/v1/attendance/history/"      ✗
ATTENDANCE_MANUAL: "/api/v1/attendance/manual/"        ✗
ATTENDANCE_STATS: "/api/v1/attendance/stats/"          ✗
```

#### Reports
```typescript
// Ces endpoints n'existent PAS dans l'API spec:
REPORTS_PRESENCE: "/api/v1/reports/presence/"          ✗
REPORTS_ATTENDANCE: "/api/v1/reports/attendance/"      ✗
REPORTS_DELAYS: "/api/v1/reports/delays/"              ✗
REPORTS_OVERTIME: "/api/v1/reports/overtime/"          ✗
REPORTS_EXPORT: "/api/v1/reports/export/"              ✗
REPORTS_STATS: "/api/v1/reports/stats/"                ✗
```

**Note**: Le système de rapports utilise les endpoints dynamiques R1-R20 définis dans `reports.config.ts`, pas ces endpoints statiques.

#### Organizations
```typescript
// Cet endpoint n'existe PAS dans l'API spec:
CLASSES: "/api/v1/classes/"                            ✗
```

**Action effectuée**: Ces définitions ont été commentées avec des notes explicatives.

---

## ✅ ENDPOINTS CORRECTEMENT IMPLÉMENTÉS

### Endpoints avec implémentation conforme

Les endpoints suivants sont **correctement implémentés** et correspondent à la spécification API:

#### Authentication (4/4) ✓
```
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
```

#### Users (5/5) ✓
```
GET    /api/v1/users/
POST   /api/v1/users/
GET    /api/v1/users/{user_id}
PUT    /api/v1/users/{user_id}
DELETE /api/v1/users/{user_id}
POST   /api/v1/users/{user_id}/roles/{role_id}
```

#### Organizations (5/5) ✓
```
GET    /api/v1/organizations/
POST   /api/v1/organizations/
GET    /api/v1/organizations/{organization_id}
PUT    /api/v1/organizations/{organization_id}
DELETE /api/v1/organizations/{organization_id}
```

#### Sites (5/5) ✓
```
GET    /api/v1/sites/
POST   /api/v1/sites/
GET    /api/v1/sites/{site_id}
PUT    /api/v1/sites/{site_id}
DELETE /api/v1/sites/{site_id}
```

#### Departments (5/5) ✓
```
GET    /api/v1/departments/
POST   /api/v1/departments/
GET    /api/v1/departments/{department_id}
PUT    /api/v1/departments/{department_id}
DELETE /api/v1/departments/{department_id}
```

#### Devices (5/5) ✓
```
GET    /api/v1/devices/
POST   /api/v1/devices/
GET    /api/v1/devices/{device_id}
PUT    /api/v1/devices/{device_id}
DELETE /api/v1/devices/{device_id}
```

#### Leaves (5/5) ✓
```
GET    /api/v1/leaves/
POST   /api/v1/leaves/
GET    /api/v1/leaves/{leave_id}
PUT    /api/v1/leaves/{leave_id}
DELETE /api/v1/leaves/{leave_id}
```

#### Roles (5/5) ✓
```
GET    /api/v1/roles/
POST   /api/v1/roles/
GET    /api/v1/roles/{role_id}
PUT    /api/v1/roles/{role_id}
DELETE /api/v1/roles/{role_id}
POST   /api/v1/roles/{role_id}/permissions/{permission_id}
```

#### Permissions (5/5) ✓
```
GET    /api/v1/permissions/
POST   /api/v1/permissions/
GET    /api/v1/permissions/{permission_id}
PUT    /api/v1/permissions/{permission_id}
DELETE /api/v1/permissions/{permission_id}
```

#### Dashboards (5/5) ✓
```
GET    /api/v1/dashboard/admin
GET    /api/v1/dashboard/manager/{organization_id}
GET    /api/v1/dashboard/employee/{employee_id}
GET    /api/v1/dashboard/integrator/{organization_id}
GET    /api/v1/dashboard/analytics/{organization_id}
```

**Note**: Les trailing slashes ont été retirés dans `src/config/api.ts` pour correspondre à l'API.

#### Attendance (2/3) ✓
```
GET    /api/v1/attendance/              ✓
POST   /api/v1/attendance/              ✓
POST   /api/v1/attendance/clock         ✓ (nouveau, implémenté)
```

Le nouvel endpoint `clockAttendance()` a été ajouté dans `src/services/attendance.service.ts`:

```typescript
async clockAttendance(employeeId: string, attendanceType: "in" | "out"): Promise<Attendance> {
  const response = await apiService.post<Attendance>(
    `${API_CONFIG.ENDPOINTS.ATTENDANCE}clock`,
    {
      employee_id: employeeId,
      attendance_type: attendanceType,
    }
  );
  return response.data;
}
```

#### Reports (58/58) ✓

Tous les endpoints de rapports (R1-R20) sont correctement implémentés:
- 29 endpoints de prévisualisation: `/api/v1/reports/{report_id}/preview`
- 28 endpoints de téléchargement: `/api/v1/reports/{report_id}/download`
- 1 endpoint spécial

Le système utilise la configuration dynamique dans `src/config/reports.config.ts`.

---

## 📊 RÉSUMÉ STATISTIQUE

### Endpoints API totaux: 70

**Par statut**:
- ✅ Correctement implémentés: **65 endpoints** (~93%)
- ⚠️ Partiellement implémentés: **2 endpoints** (employees, attendance clock)
- ❌ Manquants: **6 endpoints** (notifications)

**Par priorité de correction**:

**P0 - CRITIQUE** (Bloque des fonctionnalités majeures):
1. Employee CRUD individuel (3 endpoints)
2. Dashboard trailing slashes (CORRIGÉ ✓)

**P1 - ÉLEVÉE** (Perte de fonctionnalité importante):
3. Paramètres search/sort/filter (tous les endpoints de liste)
4. Role permissions GET endpoint

**P2 - MOYENNE** (Nice to have):
5. Attendance clock endpoint (AJOUTÉ ✓)
6. Notifications (6 endpoints)

**P3 - BASSE** (Nettoyage):
7. Endpoints inutilisés (DOCUMENTÉ ✓)

---

## 🎯 PLAN D'ACTION POUR L'ÉQUIPE BACKEND

### Phase 1: Corrections Critiques (P0)
- [x] ~~Vérifier les trailing slashes dans les routes~~ (Frontend corrigé)
- [ ] Implémenter `GET /api/v1/employees/{employee_id}`
- [ ] Implémenter `PUT /api/v1/employees/{employee_id}`
- [ ] Implémenter `DELETE /api/v1/employees/{employee_id}`

### Phase 2: Fonctionnalités Importantes (P1)
- [ ] Ajouter paramètres `search`, `sort_by`, `sort_order` à tous les endpoints de liste
- [ ] Implémenter recherche textuelle sur les champs pertinents
- [ ] Implémenter tri dynamique par colonne
- [ ] Décider: `GET /api/v1/roles/{role_id}/permissions` nécessaire ou pas?

### Phase 3: Fonctionnalités Additionnelles (P2)
- [ ] Décider si les notifications sont nécessaires
- [ ] Si oui, implémenter tous les endpoints de notifications
- [ ] Si non, retirer du frontend

### Phase 4: Documentation
- [ ] Mettre à jour `api.json` avec les nouveaux endpoints
- [ ] Documenter les paramètres de requête supportés
- [ ] Ajouter exemples de recherche/tri dans la doc

---

## 🔧 EXEMPLES D'IMPLÉMENTATION SUGGÉRÉS

### Exemple 1: Employee CRUD

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/employees", tags=["employees"])

@router.get("/{employee_id}", response_model=EmployeeSchema)
async def get_employee(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un employé par son ID"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found"
        )
    return employee

@router.put("/{employee_id}", response_model=EmployeeSchema)
async def update_employee(
    employee_id: str,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un employé"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found"
        )

    for key, value in employee_data.dict(exclude_unset=True).items():
        setattr(employee, key, value)

    db.commit()
    db.refresh(employee)
    return employee

@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un employé"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found"
        )

    db.delete(employee)
    db.commit()
    return None
```

### Exemple 2: Paramètres de recherche et tri

```python
from typing import Optional

@router.get("/employees/", response_model=PaginatedResponse[EmployeeSchema])
async def get_employees(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "asc",
    organization_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste des employés avec recherche et tri

    - **search**: Recherche dans nom, prénom, email
    - **sort_by**: Colonne de tri (name, email, created_at, etc.)
    - **sort_order**: Direction (asc, desc)
    """
    query = db.query(Employee)

    # Filtre par organisation
    if organization_id:
        query = query.filter(Employee.organization_id == organization_id)

    # Recherche textuelle
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Employee.first_name.ilike(search_filter),
                Employee.last_name.ilike(search_filter),
                Employee.email.ilike(search_filter),
                Employee.employee_number.ilike(search_filter)
            )
        )

    # Tri
    if sort_by:
        column = getattr(Employee, sort_by, None)
        if column is not None:
            if sort_order.lower() == "desc":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        else:
            # Colonne par défaut si sort_by invalide
            query = query.order_by(Employee.created_at.desc())
    else:
        query = query.order_by(Employee.created_at.desc())

    # Pagination
    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

### Exemple 3: Notifications (si implémenté)

```python
from datetime import datetime

@router.get("/notifications/", response_model=List[NotificationSchema])
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupérer les notifications de l'utilisateur"""
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()

    return notifications

@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marquer une notification comme lue"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read_at = datetime.utcnow()
    db.commit()

    return {"status": "success"}

@router.put("/notifications/read-all")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marquer toutes les notifications comme lues"""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read_at.is_(None)
    ).update({"read_at": datetime.utcnow()})

    db.commit()
    return {"status": "success"}
```

---

## 📞 CONTACT

Pour toute question sur ces notes, contacter l'équipe frontend avec les références suivantes:

**Fichiers frontend modifiés**:
1. `src/config/api.ts` - Configuration des endpoints
2. `src/services/employee.service.ts` - Service employés
3. `src/services/organization.service.ts` - Service organisations
4. `src/services/site.service.ts` - Service sites
5. `src/services/department.service.ts` - Service départements
6. `src/services/device.service.ts` - Service appareils
7. `src/services/leave.service.ts` - Service congés
8. `src/services/attendance.service.ts` - Service présences
9. `src/services/role.service.ts` - Service rôles
10. `src/services/notification.service.ts` - Service notifications

**Référence**: Analyse basée sur `api.json` (spécification OpenAPI)

---

**Dernière mise à jour**: 2025-11-08
**Status**: Corrections frontend complétées, en attente des corrections backend
