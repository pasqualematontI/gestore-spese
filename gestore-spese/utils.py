import json
from pathlib import Path

import pandas as pd

from models import Spesa

DATA_DIR = Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "spese.csv"
UNDO_PATH = DATA_DIR / "undo_stack.json"
REDO_PATH = DATA_DIR / "redo_stack.json"
MAX_CRONOLOGIA = 30

COLONNE = ["data", "importo", "categoria", "descrizione"]

CATEGORIE = [
    "Alimentari",
    "Trasporti",
    "Svago",
    "Casa",
    "Salute",
    "Altro",
]


def _assicura_file() -> None:
    """Crea la cartella data e il file CSV se non esistono."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        pd.DataFrame(columns=COLONNE).to_csv(CSV_PATH, index=False)


def _leggi_stack(percorso: Path) -> list[str]:
    if not percorso.exists():
        return []
    try:
        return json.loads(percorso.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _scrivi_stack(percorso: Path, stack: list[str]) -> None:
    percorso.write_text(json.dumps(stack), encoding="utf-8")


def _stato_csv_attuale() -> str:
    _assicura_file()
    return CSV_PATH.read_text(encoding="utf-8")


def _aggiungi_a_stack(percorso: Path, stack: list[str], stato: str) -> list[str]:
    stack.append(stato)
    if len(stack) > MAX_CRONOLOGIA:
        stack = stack[-MAX_CRONOLOGIA:]
    _scrivi_stack(percorso, stack)
    return stack


def _svuota_stack_ripeti() -> None:
    if REDO_PATH.exists():
        REDO_PATH.unlink()


def _salva_stato_per_annulla() -> None:
    """Memorizza lo stato attuale del CSV prima di una nuova modifica."""
    _svuota_stack_ripeti()
    stack = _leggi_stack(UNDO_PATH)
    _aggiungi_a_stack(UNDO_PATH, stack, _stato_csv_attuale())


def puo_annullare() -> bool:
    """True se si può tornare indietro."""
    return len(_leggi_stack(UNDO_PATH)) > 0


def puo_ripetere() -> bool:
    """True se si può andare avanti (dopo un annulla)."""
    return len(_leggi_stack(REDO_PATH)) > 0


def annulla_ultima_modifica() -> bool:
    """Ripristina il CSV allo stato precedente (annulla aggiunta/rimozione)."""
    stack_undo = _leggi_stack(UNDO_PATH)
    if not stack_undo:
        return False
    stack_redo = _leggi_stack(REDO_PATH)
    _aggiungi_a_stack(REDO_PATH, stack_redo, _stato_csv_attuale())
    stato_precedente = stack_undo.pop()
    _scrivi_stack(UNDO_PATH, stack_undo)
    CSV_PATH.write_text(stato_precedente, encoding="utf-8")
    return True


def ripeti_ultima_modifica() -> bool:
    """Ripristina una modifica annullata (es. spese che non ci sono più)."""
    stack_redo = _leggi_stack(REDO_PATH)
    if not stack_redo:
        return False
    stack_undo = _leggi_stack(UNDO_PATH)
    _aggiungi_a_stack(UNDO_PATH, stack_undo, _stato_csv_attuale())
    stato_successivo = stack_redo.pop()
    _scrivi_stack(REDO_PATH, stack_redo)
    CSV_PATH.write_text(stato_successivo, encoding="utf-8")
    return True


def carica_spese() -> list[Spesa]:
    """Carica tutte le spese dal file CSV."""
    _assicura_file()
    df = pd.read_csv(CSV_PATH)
    if df.empty:
        return []
    return [Spesa.from_dict(row) for row in df.to_dict(orient="records")]


def salva_spesa(spesa: Spesa) -> None:
    """Aggiunge una spesa al file CSV."""
    _assicura_file()
    _salva_stato_per_annulla()
    df = pd.read_csv(CSV_PATH)
    nuovo = pd.DataFrame([spesa.to_dict()])
    df = pd.concat([df, nuovo], ignore_index=True)
    df.to_csv(CSV_PATH, index=False)


def spese_in_dataframe() -> pd.DataFrame:
    """Restituisce tutte le spese come DataFrame."""
    _assicura_file()
    return pd.read_csv(CSV_PATH)


def totale_spese() -> float:
    """Calcola la somma di tutte le spese."""
    df = spese_in_dataframe()
    if df.empty:
        return 0.0
    return float(df["importo"].sum())


def numero_spese() -> int:
    """Conta il numero totale di spese."""
    df = spese_in_dataframe()
    return len(df)


def spese_per_categoria() -> pd.DataFrame:
    """Raggruppa le spese per categoria."""
    df = spese_in_dataframe()
    if df.empty:
        return pd.DataFrame(columns=["categoria", "importo"])
    return df.groupby("categoria", as_index=False)["importo"].sum()


def spese_per_mese() -> pd.DataFrame:
    """Raggruppa le spese per mese (formato YYYY-MM)."""
    df = spese_in_dataframe()
    if df.empty:
        return pd.DataFrame(columns=["mese", "importo"])
    df = df.copy()
    df["mese"] = pd.to_datetime(df["data"]).dt.strftime("%Y-%m")
    return df.groupby("mese", as_index=False)["importo"].sum()


def elimina_spesa(indice: int) -> bool:
    """Elimina una spesa per posizione (0 = prima riga del CSV)."""
    _assicura_file()
    df = pd.read_csv(CSV_PATH)
    if indice < 0 or indice >= len(df):
        return False
    _salva_stato_per_annulla()
    df = df.drop(indice).reset_index(drop=True)
    df.to_csv(CSV_PATH, index=False)
    return True


def spese_per_mese_categoria() -> pd.DataFrame:
    """Raggruppa le spese per mese e categoria (formato YYYY-MM)."""
    df = spese_in_dataframe()
    if df.empty:
        return pd.DataFrame(columns=["mese", "categoria", "importo"])
    df = df.copy()
    df["mese"] = pd.to_datetime(df["data"]).dt.strftime("%Y-%m")
    return df.groupby(["mese", "categoria"], as_index=False)["importo"].sum()
# === AGGIUNGI ALLA FINE DI utils.py ===

def modifica_spesa(indice: int, nuova_spesa: Spesa) -> bool:
    """Modifica una spesa esistente per indice."""
    _assicura_file()
    df = pd.read_csv(CSV_PATH)
    
    if indice < 0 or indice >= len(df):
        return False
    
    _salva_stato_per_annulla()
    
    # Aggiorna la riga
    df.loc[indice] = [
        nuova_spesa.data,
        nuova_spesa.importo,
        nuova_spesa.categoria,
        nuova_spesa.descrizione
    ]
    
    df.to_csv(CSV_PATH, index=False)
    return True


def get_spesa_by_index(indice: int) -> Spesa | None:
    """Restituisce una singola spesa per indice."""
    df = spese_in_dataframe()
    if indice < 0 or indice >= len(df):
        return None
    row = df.iloc[indice]
    return Spesa.from_dict(row.to_dict())