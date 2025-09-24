from contextlib import asynccontextmanager
from typing import Annotated, Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from .routers import items, users, notification
from .internal import admin
from fastapi.staticfiles import StaticFiles
from pathlib import Path

description = """
ChimichangApp API helps you do awesome stuff. 🚀

## Items

You can **read items**.

## Users

You will be able to:

* **Create users** (_not implemented_).
* **Read users** (_not implemented_).
"""

tags_metadata = [
    {
        "name": "users",
        "description": "Operations with users. The **login** logic is also here.",
    },
    {
        "name": "items",
        "description": "Manage items. So _fancy_ they have their own docs.",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
]



class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    secret_name: str

class HeroUpdate(SQLModel):
    name: Optional[str] = None
    age: Optional[int] = None
    secret_name: Optional[str] = None

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

print(SQLModel.metadata.tables.keys())

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # chạy khi app startup
    create_db_and_tables()
    yield
    # chạy khi app shutdown (nếu muốn dọn tài nguyên thì viết thêm ở đây)
    engine.dispose()  # đóng kết nối database khi app tắt

# truyền lifespan khi tạo app
app = FastAPI(lifespan=lifespan, 
    title="ChimichangApp",
    description=description,
    summary="Deadpool's favorite app. Nuff said.",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "identifier": "MIT",
        # "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    openapi_tags=tags_metadata
    )

app.include_router(users.router)
app.include_router(items.router)
app.include_router(admin.router)
app.include_router(notification.router)


app.mount("/static", StaticFiles(directory="App/static/"), name="static")

@app.post("/heroes/", tags=["heroes"], response_model=Hero)
def create_hero(hero: Hero, session: SessionDep) :
    print("hero before commit:", hero)
    session.add(hero)
    session.commit()
    session.refresh(hero)
    print("hero after commit:", hero)
    return hero

@app.patch("/heroes/{hero_id}", response_model=Hero, tags=["heroes"])
def update_hero(hero_id: int, hero_in: HeroUpdate, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    hero_data = hero_in.model_dump(exclude_unset=True)  
    for key, value in hero_data.items():
        setattr(hero, key, value)

    # session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero

# Code above omitted 👆

@app.delete("/heroes/{hero_id}", tags=["heroes"])
def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}

@app.get("/heroes/", tags=["heroes"])
def read_heroes(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Hero]:
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes



@app.get("/heroes/{hero_id}", tags=["heroes"], response_model=Hero)
def read_hero(hero_id: int, session: SessionDep) :
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

