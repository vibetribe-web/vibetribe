from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.college import College
from app.models.skill import Skill


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().split())


def get_or_create_college(db: Session, name: str | None) -> College | None:
    if not name:
        return None
    normalized = _normalize_name(name)
    college = db.scalar(select(College).where(College.name.ilike(normalized)))
    if college:
        return college
    college = College(name=normalized)
    db.add(college)
    db.flush()
    return college


def get_or_create_branch(db: Session, name: str | None) -> Branch | None:
    if not name:
        return None
    normalized = _normalize_name(name)
    branch = db.scalar(select(Branch).where(Branch.name.ilike(normalized)))
    if branch:
        return branch
    branch = Branch(name=normalized)
    db.add(branch)
    db.flush()
    return branch


def get_or_create_skills(db: Session, names: list[str] | None) -> list[Skill]:
    skills: list[Skill] = []
    seen: set[str] = set()
    for name in names or []:
        normalized = _normalize_name(name)
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        skill = db.scalar(select(Skill).where(Skill.name.ilike(normalized)))
        if skill is None:
            skill = Skill(name=normalized)
            db.add(skill)
            db.flush()
        skills.append(skill)
    return skills
