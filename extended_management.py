"""
extended_management.py

Additional functions for cut list generation and inventory management for the
production management software. These functions build upon the basic parsing
functions in production_management.
"""

import sqlite3
import pandas as pd
from typing import Tuple, Dict


def generate_cut_lists(df: pd.DataFrame) -> Dict[Tuple[str, float], pd.DataFrame]:
    """Generate cut lists grouped by material and thickness.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing piece details with at least the columns
        'Materiale', 'Spessore', 'Lunghezza', 'Larghezza' and 'Quantità'.

    Returns
    -------
    Dict[Tuple[str, float], pd.DataFrame]
        A mapping from (material, thickness) to a DataFrame sorted by length
        and width containing all rows for that combination.
    """
    required_columns = {'Materiale', 'Spessore', 'Lunghezza', 'Larghezza', 'Quantità'}
    missing = required_columns - set(df.columns)
    if missing:
        raise KeyError(f"Missing required columns for cut list generation: {missing}")
    cut_lists: Dict[Tuple[str, float], pd.DataFrame] = {}
    df = df.copy()
    df['Spessore'] = pd.to_numeric(df['Spessore'], errors='coerce')
    df['Lunghezza'] = pd.to_numeric(df['Lunghezza'], errors='coerce')
    df['Larghezza'] = pd.to_numeric(df['Larghezza'], errors='coerce')
    df['Quantità'] = pd.to_numeric(df['Quantità'], errors='coerce')
    grouped = df.groupby(['Materiale', 'Spessore'])
    for (mat, thick), group in grouped:
        g = group.dropna(subset=['Lunghezza', 'Larghezza'])
        g = g.sort_values(by=['Lunghezza', 'Larghezza'])
        cut_lists[(mat, thick)] = g.reset_index(drop=True)
    return cut_lists


def init_inventory_db(db_path: str) -> None:
    """Initialise a SQLite database for material inventory.

    Creates a table called 'materials' with columns 'name' and 'quantity'.
    """
    conn = sqlite3.connect(db_path)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS materials (
                name TEXT PRIMARY KEY,
                quantity REAL NOT NULL
            )
            """
        )
    conn.close()


def get_inventory(db_path: str) -> pd.DataFrame:
    """Return the current material inventory as a DataFrame."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT name AS Material, quantity AS Quantity FROM materials ORDER BY name", conn)
    conn.close()
    return df


def adjust_material_stock(material: str, qty_delta: float, db_path: str) -> None:
    """Adjust the stock quantity for a single material by qty_delta.

    If the material does not exist it will be created.
    """
    conn = sqlite3.connect(db_path)
    with conn:
        conn.execute(
            """
            INSERT INTO materials (name, quantity) VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET quantity = quantity + excluded.quantity
            """,
            (material, qty_delta),
        )
    conn.close()


def update_inventory_from_pieces(df: pd.DataFrame, db_path: str) -> None:
    """Update inventory by subtracting the quantities of materials used in a piece list."""
    if 'Materiale' not in df.columns or 'Quantità' not in df.columns:
        raise KeyError("DataFrame must contain 'Materiale' and 'Quantità' columns for inventory update")
    df = df.copy()
    df['Quantità'] = pd.to_numeric(df['Quantità'], errors='coerce').fillna(0)
    aggregated = df.groupby('Materiale')['Quantità'].sum()
    for material, qty in aggregated.items():
        adjust_material_stock(material, -float(qty), db_path)
