"""数据库引擎与会话（SQLite，零运维）。"""
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "pms.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 单文件 + 多线程访问
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate():
    """向后兼容：已有数据库缺新字段时自动 ALTER 补列，避免旧库启动报错。"""
    inspector = inspect(engine)
    with engine.connect() as conn:
        # employee.status
        cols = [c["name"] for c in inspector.get_columns("employee")]
        if "status" not in cols:
            conn.execute(text("ALTER TABLE employee ADD COLUMN status VARCHAR(20) DEFAULT '在岗'"))
            conn.commit()


def init_db():
    import app.models  # noqa: F401  确保模型已注册
    Base.metadata.create_all(bind=engine)
    _migrate()

