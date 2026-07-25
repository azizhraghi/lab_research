from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
from app.schemas.mis import Projet as ProjetSchema, Personnel as PersonnelSchema, Equipement as EquipementSchema, Budget as BudgetSchema
from app.models.mis import Projet as ProjetModel, Personnel as PersonnelModel, Equipement as EquipementModel, Budget as BudgetModel
from app.database import get_db

router = APIRouter(tags=["MIS"])


# Projets CRUD

@router.post("/projets/", response_model=ProjetSchema)
async def create_projet(projet: ProjetSchema, db: AsyncSession = Depends(get_db)) -> ProjetSchema:
    db_projet = ProjetModel(
        id=projet.id,
        nom=projet.nom,
        description=projet.description,
        statut=projet.statut,
        date_debut=projet.date_debut,
        date_fin_prevue=projet.date_fin_prevue,
        budget_alloue=projet.budget_alloue,
        responsable=projet.responsable,
    )
    db.add(db_projet)
    await db.commit()
    await db.refresh(db_projet)
    return ProjetSchema.model_validate(db_projet.__dict__)


@router.get("/projets/", response_model=list[ProjetSchema])
async def list_projets(db: AsyncSession = Depends(get_db)) -> list[ProjetSchema]:
    result = await db.execute(select(ProjetModel))
    projets = result.scalars().all()
    return [ProjetSchema.model_validate(p.__dict__) for p in projets]


@router.get("/projets/{projet_id}", response_model=ProjetSchema)
async def get_projet(projet_id: str, db: AsyncSession = Depends(get_db)) -> ProjetSchema:
    projet = await db.get(ProjetModel, projet_id)
    if projet is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return ProjetSchema.model_validate(projet.__dict__)


@router.put("/projets/{projet_id}", response_model=ProjetSchema)
async def update_projet(projet_id: str, data: dict, db: AsyncSession = Depends(get_db)) -> ProjetSchema:
    projet = await db.get(ProjetModel, projet_id)
    if projet is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    for key, value in data.items():
        setattr(projet, key, value)
    await db.commit()
    await db.refresh(projet)
    return ProjetSchema.model_validate(projet.__dict__)


@router.delete("/projets/{projet_id}")
async def delete_projet(projet_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    projet = await db.get(ProjetModel, projet_id)
    if projet is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    await db.delete(projet)
    await db.commit()
    return {"message": f"Projet {projet_id} supprime avec succes"}


# Personnel CRUD

@router.post("/personnels/", response_model=PersonnelSchema)
async def create_personnel(personnel: PersonnelSchema, db: AsyncSession = Depends(get_db)) -> PersonnelSchema:
    db_personnel = PersonnelModel(
        id=personnel.id,
        nom=personnel.nom,
        prenom=personnel.prenom,
        email=personnel.email,
        role=personnel.role,
        competences=json.dumps(personnel.competences),
        disponible=personnel.disponible,
        projet_actuel_id=personnel.projet_actuel_id,
    )
    db.add(db_personnel)
    await db.commit()
    await db.refresh(db_personnel)
    data = db_personnel.__dict__.copy()
    data["competences"] = json.loads(data["competences"])
    return PersonnelSchema.model_validate(data)


@router.get("/personnels/", response_model=list[PersonnelSchema])
async def list_personnels(db: AsyncSession = Depends(get_db)) -> list[PersonnelSchema]:
    result = await db.execute(select(PersonnelModel))
    personnels = result.scalars().all()
    out = []
    for p in personnels:
        data = p.__dict__.copy()
        data["competences"] = json.loads(data["competences"])
        out.append(PersonnelSchema.model_validate(data))
    return out


@router.get("/personnels/{personnel_id}", response_model=PersonnelSchema)
async def get_personnel(personnel_id: str, db: AsyncSession = Depends(get_db)) -> PersonnelSchema:
    personnel = await db.get(PersonnelModel, personnel_id)
    if personnel is None:
        raise HTTPException(status_code=404, detail="Personnel introuvable")
    data = personnel.__dict__.copy()
    data["competences"] = json.loads(data["competences"])
    return PersonnelSchema.model_validate(data)


@router.put("/personnels/{personnel_id}", response_model=PersonnelSchema)
async def update_personnel(personnel_id: str, data: dict, db: AsyncSession = Depends(get_db)) -> PersonnelSchema:
    personnel = await db.get(PersonnelModel, personnel_id)
    if personnel is None:
        raise HTTPException(status_code=404, detail="Personnel introuvable")
    if "competences" in data and isinstance(data["competences"], list):
        data["competences"] = json.dumps(data["competences"])
    for key, value in data.items():
        setattr(personnel, key, value)
    await db.commit()
    await db.refresh(personnel)
    out = personnel.__dict__.copy()
    out["competences"] = json.loads(out["competences"])
    return PersonnelSchema.model_validate(out)


@router.delete("/personnels/{personnel_id}")
async def delete_personnel(personnel_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    personnel = await db.get(PersonnelModel, personnel_id)
    if personnel is None:
        raise HTTPException(status_code=404, detail="Personnel introuvable")
    await db.delete(personnel)
    await db.commit()
    return {"message": f"Personnel {personnel_id} supprime avec succes"}


# Équipements CRUD

@router.post("/equipements/", response_model=EquipementSchema)
async def create_equipement(equipement: EquipementSchema, db: AsyncSession = Depends(get_db)) -> EquipementSchema:
    db_equipement = EquipementModel(
        id=equipement.id,
        nom=equipement.nom,
        type=equipement.type,
        etat=equipement.etat,
        localisation=equipement.localisation,
        responsable_id=equipement.responsable_id,
        date_acquisition=equipement.date_acquisition,
        valeur_estimee=equipement.valeur_estimee,
    )
    db.add(db_equipement)
    await db.commit()
    await db.refresh(db_equipement)
    return EquipementSchema.model_validate(db_equipement.__dict__)


@router.get("/equipements/", response_model=list[EquipementSchema])
async def list_equipements(db: AsyncSession = Depends(get_db)) -> list[EquipementSchema]:
    result = await db.execute(select(EquipementModel))
    equipements = result.scalars().all()
    return [EquipementSchema.model_validate(e.__dict__) for e in equipements]


@router.get("/equipements/{equipement_id}", response_model=EquipementSchema)
async def get_equipement(equipement_id: str, db: AsyncSession = Depends(get_db)) -> EquipementSchema:
    equipement = await db.get(EquipementModel, equipement_id)
    if equipement is None:
        raise HTTPException(status_code=404, detail="Equipement introuvable")
    return EquipementSchema.model_validate(equipement.__dict__)


@router.put("/equipements/{equipement_id}", response_model=EquipementSchema)
async def update_equipement(equipement_id: str, data: dict, db: AsyncSession = Depends(get_db)) -> EquipementSchema:
    equipement = await db.get(EquipementModel, equipement_id)
    if equipement is None:
        raise HTTPException(status_code=404, detail="Equipement introuvable")
    for key, value in data.items():
        setattr(equipement, key, value)
    await db.commit()
    await db.refresh(equipement)
    return EquipementSchema.model_validate(equipement.__dict__)


@router.delete("/equipements/{equipement_id}")
async def delete_equipement(equipement_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    equipement = await db.get(EquipementModel, equipement_id)
    if equipement is None:
        raise HTTPException(status_code=404, detail="Equipement introuvable")
    await db.delete(equipement)
    await db.commit()
    return {"message": f"Equipement {equipement_id} supprime avec succes"}


# Budgets CRUD

@router.post("/budgets/", response_model=BudgetSchema)
async def create_budget(budget: BudgetSchema, db: AsyncSession = Depends(get_db)) -> BudgetSchema:
    db_budget = BudgetModel(
        id=budget.id,
        projet_id=budget.projet_id,
        montant_alloue=budget.montant_alloue,
        montant_depense=budget.montant_depense,
        devise=budget.devise,
        date_debut=budget.date_debut,
        date_fin=budget.date_fin,
        description=budget.description,
    )
    db.add(db_budget)
    await db.commit()
    await db.refresh(db_budget)
    return BudgetSchema.model_validate(db_budget.__dict__)


@router.get("/budgets/", response_model=list[BudgetSchema])
async def list_budgets(db: AsyncSession = Depends(get_db)) -> list[BudgetSchema]:
    result = await db.execute(select(BudgetModel))
    budgets = result.scalars().all()
    return [BudgetSchema.model_validate(b.__dict__) for b in budgets]


@router.get("/budgets/{budget_id}", response_model=BudgetSchema)
async def get_budget(budget_id: str, db: AsyncSession = Depends(get_db)) -> BudgetSchema:
    budget = await db.get(BudgetModel, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    return BudgetSchema.model_validate(budget.__dict__)


@router.put("/budgets/{budget_id}", response_model=BudgetSchema)
async def update_budget(budget_id: str, data: dict, db: AsyncSession = Depends(get_db)) -> BudgetSchema:
    budget = await db.get(BudgetModel, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    for key, value in data.items():
        setattr(budget, key, value)
    await db.commit()
    await db.refresh(budget)
    return BudgetSchema.model_validate(budget.__dict__)


@router.delete("/budgets/{budget_id}")
async def delete_budget(budget_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    budget = await db.get(BudgetModel, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    await db.delete(budget)
    await db.commit()
    return {"message": f"Budget {budget_id} supprime avec succes"}