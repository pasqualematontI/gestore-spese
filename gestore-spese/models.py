from dataclasses import dataclass
from datetime import datetime


@dataclass
class Spesa:
    """Rappresenta una singola spesa personale."""

    data: str
    importo: float
    categoria: str
    descrizione: str

    def to_dict(self) -> dict:
        return {
            "data": self.data,
            "importo": self.importo,
            "categoria": self.categoria,
            "descrizione": self.descrizione,
        }

    @classmethod
    def from_dict(cls, row: dict) -> "Spesa":
        return cls(
            data=str(row["data"]),
            importo=float(row["importo"]),
            categoria=str(row["categoria"]),
            descrizione=str(row["descrizione"]),
        )

    @classmethod
    def nuova(
        cls,
        importo: float,
        categoria: str,
        descrizione: str,
        data: str | None = None,
    ) -> "Spesa":
        return cls(
            data=data or datetime.now().strftime("%Y-%m-%d"),
            importo=importo,
            categoria=categoria,
            descrizione=descrizione,
        )
