"""Food Item Creator UI

This module provides a simple Tkinter-based editor to create and edit food products
stored in `data/products.json`.

Run:
    python services/food_item_creator.py

"""

from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_PATH = PROJECT_ROOT / "data" / "products.json"

FOOD_ITEM_KEYS = [
    "barcode",
    "name",
    "category",
    "unit_type",
    "package_quantity",
    "package_unit",
    "serving_size",
    "serving_unit",
    "price",
]

UNIT_TYPES = ["weight", "volume", "count"]


def load_products() -> List[Dict[str, Any]]:
    """Load the list of food products from the products.json file."""
    if not PRODUCTS_PATH.exists():
        return []

    with PRODUCTS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_products(products: List[Dict[str, Any]]) -> None:
    """Persist the list of food products back to products.json."""
    with PRODUCTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(products, f, indent=4, ensure_ascii=False)


class FoodItemEditor:
    """Tkinter UI for viewing and editing food products."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Food Product Editor")
        self.root.geometry("900x600")

        self.products: List[Dict[str, Any]] = load_products()
        self.selected_index: int | None = None

        self.status_var = tk.StringVar(value="Ready")
        self.entries: Dict[str, tk.Entry] = {}

        self._build_ui()
        self._refresh_list()
        self._warn_duplicates_if_any()

    def _find_duplicates(self) -> List[str]:
        """Return a list of warning lines describing duplicate barcodes."""
        barcode_map: Dict[str, List[Dict[str, Any]]] = {}

        for item in self.products:
            barcode = item.get("barcode") or ""
            if barcode:
                barcode_map.setdefault(barcode, []).append(item)

        warnings: List[str] = []

        for barcode, items in barcode_map.items():
            if len(items) > 1:
                warnings.append(
                    f"Duplicate barcode '{barcode}' found with these entries:\n"
                    + "\n".join(
                        f"  - {i.get('name', '<unknown>')} ({i.get('barcode', '')})"
                        for i in items
                    )
                )

        return warnings

    def _warn_duplicates_if_any(self) -> None:
        """Show a persistent warning if there are duplicates in the loaded products."""
        warnings = self._find_duplicates()
        if not warnings:
            return

        messagebox.showwarning(
            "Duplicate Products Detected",
            "\n\n".join(warnings),
        )

    def _build_ui(self) -> None:
        # Top-level layout: 1/3 list, 2/3 editor.
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1, minsize=300)
        self.root.columnconfigure(1, weight=2)

        # Left frame: product list
        left_frame = ttk.Frame(self.root, padding=(10, 10, 5, 10))
        left_frame.grid(row=0, column=0, sticky="nsew")
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)

        ttk.Label(left_frame, text="Products", font=(None, 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        self.product_tree = ttk.Treeview(left_frame, columns=("display",), show="tree headings", height=15)
        self.product_tree.heading("#0", text="")
        self.product_tree.heading("display", text="Products")
        self.product_tree.column("display", width=250)
        self.product_tree.grid(row=1, column=0, sticky="nsew")
        self.product_tree.bind("<<TreeviewSelect>>", self._on_select)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            left_frame, orient="vertical", command=self.product_tree.yview
        )
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.product_tree.configure(yscrollcommand=scrollbar.set)

        # Define tags for duplicates
        self.product_tree.tag_configure("duplicate", foreground="red")

        # Right frame: fields
        right_frame = ttk.Frame(self.root, padding=(10, 10, 10, 10))
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.columnconfigure(1, weight=1)

        ttk.Label(right_frame, text="Food Item Details", font=(None, 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        for idx, key in enumerate(FOOD_ITEM_KEYS, start=1):
            label = ttk.Label(right_frame, text=f"{key.replace('_', ' ').title()}: ")
            label.grid(row=idx, column=0, sticky="e", padx=(0, 8), pady=4)

            if key == "unit_type":
                widget = ttk.Combobox(
                    right_frame, values=UNIT_TYPES, state="readonly", width=20
                )
                widget.set(UNIT_TYPES[0])
            else:
                widget = ttk.Entry(right_frame)

            widget.grid(row=idx, column=1, sticky="ew", pady=4)
            self.entries[key] = widget  # type: ignore[assignment]

        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=len(FOOD_ITEM_KEYS) + 2, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(button_frame, text="New", command=self._new_item).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(button_frame, text="Save", command=self._save_current).grid(
            row=0, column=1, padx=4
        )
        ttk.Button(button_frame, text="Save as New", command=self._save_as_new_current).grid(
            row=0, column=2, padx=4
        )
        ttk.Button(button_frame, text="Delete", command=self._delete_current).grid(
            row=0, column=3, padx=4
        )

        status = ttk.Label(self.root, textvariable=self.status_var, anchor="w")
        status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

    def _refresh_list(self) -> None:
        # Clear existing items
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)

        # Insert all products
        for idx, item in enumerate(self.products):
            name = item.get("name", "")
            barcode = item.get("barcode", "")
            display = f"{name} ({barcode})" if barcode else name
            self.product_tree.insert("", "end", iid=str(idx), values=(display,))

        # Identify duplicates (only by barcode)
        barcode_counts: Dict[str, int] = {}
        for item in self.products:
            barcode = item.get("barcode") or ""
            if barcode:
                barcode_counts[barcode] = barcode_counts.get(barcode, 0) + 1

        # Apply tags to duplicates
        for idx, item in enumerate(self.products):
            barcode = item.get("barcode") or ""
            if barcode_counts.get(barcode, 0) > 1:
                self.product_tree.item(str(idx), tags=("duplicate",))

        # If the underlying JSON contains duplicates, warn the user so they can resolve them.
        self._warn_duplicates_if_any()

    def _on_select(self, event: tk.Event) -> None:
        selection = self.product_tree.selection()
        if not selection:
            return
        self.selected_index = int(selection[0])
        self._load_selected()

    def _load_selected(self) -> None:
        if self.selected_index is None:
            return
        item = self.products[self.selected_index]
        for key in FOOD_ITEM_KEYS:
            value = item.get(key, "")
            widget = self.entries[key]
            widget.delete(0, tk.END)
            widget.insert(0, "" if value is None else str(value))

        self.status_var.set(f"Editing: {item.get('name', '')}")

    def _new_item(self) -> None:
        self.selected_index = None
        for key, widget in self.entries.items():
            widget.delete(0, tk.END)
            if key == "unit_type":
                widget.set(UNIT_TYPES[0])
        self.status_var.set("Creating new item. Fill out fields and click Save.")
        self.product_tree.selection_remove(self.product_tree.selection())

    def _validate_and_build_item(self, ignore_index: int | None = None) -> Dict[str, Any] | None:
        item: Dict[str, Any] = {}

        for key in FOOD_ITEM_KEYS:
            raw = self.entries[key].get().strip()

            if key == "barcode" and not raw:
                messagebox.showwarning(
                    "Validation Error", "Barcode is required and must be unique."
                )
                return None

            if key in {"package_quantity", "serving_size", "price"}:
                if raw == "":
                    item[key] = None if key == "price" else 0.0
                else:
                    try:
                        item[key] = float(raw)
                    except ValueError:
                        messagebox.showwarning(
                            "Validation Error",
                            f"{key.replace('_', ' ').title()} must be a number.",
                        )
                        return None
            else:
                item[key] = raw

        # Ensure barcode uniqueness
        for idx, existing in enumerate(self.products):
            if idx == ignore_index:
                continue
            if existing.get("barcode") == item.get("barcode"):
                messagebox.showwarning(
                    "Validation Error",
                    "Barcode must be unique among products.",
                )
                return None

        return item

    def _save_current(self) -> None:
        item = self._validate_and_build_item(ignore_index=self.selected_index)
        if item is None:
            return

        if self.selected_index is None:
            self.products.append(item)
            self.selected_index = len(self.products) - 1
        else:
            self.products[self.selected_index] = item

        save_products(self.products)
        self._refresh_list()
        if self.selected_index is not None:
            self.product_tree.selection_set(str(self.selected_index))
            self.product_tree.see(str(self.selected_index))

        self.status_var.set("Saved.")

    def _save_as_new_current(self) -> None:
        item = self._validate_and_build_item(ignore_index=None)
        if item is None:
            return

        self.products.append(item)
        self.selected_index = len(self.products) - 1

        save_products(self.products)
        self._refresh_list()
        self.product_tree.selection_set(str(self.selected_index))
        self.product_tree.see(str(self.selected_index))

        self.status_var.set("Saved as new item.")

    def _delete_current(self) -> None:
        if self.selected_index is None:
            messagebox.showinfo("Delete", "No product selected to delete.")
            return

        item = self.products[self.selected_index]
        confirm = messagebox.askyesno(
            "Delete", f"Delete '{item.get('name', '')}' from products?"
        )
        if not confirm:
            return

        del self.products[self.selected_index]
        save_products(self.products)
        self._refresh_list()
        self._new_item()
        self.status_var.set("Deleted.")


def main() -> None:
    root = tk.Tk()
    FoodItemEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
