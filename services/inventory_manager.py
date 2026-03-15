"""Inventory Manager UI

This module provides a Tkinter-based UI for managing the inventory stored in `data/inventory.json`.

Run:
    python services/inventory_manager.py

"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import tkinter as tk
from tkinter import messagebox, ttk

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = PROJECT_ROOT / "data" / "inventory.json"
PRODUCTS_PATH = PROJECT_ROOT / "data" / "products.json"


def load_inventory() -> List[Dict[str, Any]]:
    """Load the list of inventory items from the inventory.json file."""
    if not INVENTORY_PATH.exists():
        return []

    with INVENTORY_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Convert date strings to datetime objects
    for item in data:
        item["purchase_date"] = datetime.fromisoformat(item["purchase_date"])
        if item.get("opened_date"):
            item["opened_date"] = datetime.fromisoformat(item["opened_date"])
        item["expiration_date"] = datetime.fromisoformat(item["expiration_date"])

    return data


def save_inventory(inventory: List[Dict[str, Any]]) -> None:
    """Persist the list of inventory items back to inventory.json."""
    # Convert datetime to ISO strings
    data = []
    for item in inventory:
        item_copy = item.copy()
        item_copy["purchase_date"] = item["purchase_date"].isoformat()
        if item.get("opened_date"):
            item_copy["opened_date"] = item["opened_date"].isoformat()
        item_copy["expiration_date"] = item["expiration_date"].isoformat()
        data.append(item_copy)

    with INVENTORY_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_products() -> List[Dict[str, Any]]:
    """Load the list of food products."""
    if not PRODUCTS_PATH.exists():
        return []

    with PRODUCTS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


class InventoryManager:
    """Tkinter UI for managing inventory."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Inventory Manager")
        self.root.geometry("1000x700")

        self.inventory: List[Dict[str, Any]] = load_inventory()
        self.products: List[Dict[str, Any]] = load_products()
        self.selected_products: List[Dict[str, Any]] = []
        self.quantity_entries: List[tk.Entry] = []
        self.last_added: List[Dict[str, Any]] = []  # For undo

        self.sort_column: str | None = None
        self.sort_reverse: bool = False
        self.agg_sort_column: str | None = None
        self.agg_sort_reverse: bool = False

        self._build_ui()
        self._refresh_inventory()
        self._refresh_aggregated()
        self._refresh_products()

    def _sort_inventory(self, col: str) -> None:
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False

        def key_func(item: Dict[str, Any]) -> Any:
            if col == "name":
                product = next((p for p in self.products if p["barcode"] == item["barcode"]), {})
                return product.get("name", "").lower()
            elif col == "quantity":
                return item["quantity"]
            elif col == "unit":
                return item["unit"]
            elif col == "purchase_date":
                return item["purchase_date"]
            elif col == "expiration_date":
                return item["expiration_date"]
            elif col == "storage":
                return item["storage_location"]
            return ""

        self.inventory.sort(key=key_func, reverse=self.sort_reverse)
        self._refresh_inventory()

    def _refresh_aggregated(self) -> None:
        for item in self.aggregated_tree.get_children():
            self.aggregated_tree.delete(item)

        # Aggregate by barcode
        agg_data: Dict[str, Dict[str, Any]] = {}
        for item in self.inventory:
            barcode = item["barcode"]
            if barcode not in agg_data:
                product = next((p for p in self.products if p["barcode"] == barcode), {})
                agg_data[barcode] = {
                    "name": product.get("name", "Unknown"),
                    "total_quantity": 0.0,
                    "unit": item["unit"],
                }
            agg_data[barcode]["total_quantity"] += item["quantity"]

        # Sort agg_data
        if self.agg_sort_column:
            def agg_key_func(item: tuple[str, Dict[str, Any]]) -> Any:
                barcode, data = item
                if self.agg_sort_column == "name":
                    return data["name"].lower()
                elif self.agg_sort_column == "total_quantity":
                    return data["total_quantity"]
                elif self.agg_sort_column == "unit":
                    return data["unit"]
                return ""
            sorted_agg = sorted(agg_data.items(), key=agg_key_func, reverse=self.agg_sort_reverse)
        else:
            sorted_agg = list(agg_data.items())

        for barcode, data in sorted_agg:
            self.aggregated_tree.insert("", "end", values=(data["name"], f"{data['total_quantity']}", data["unit"]))

    def _sort_aggregated(self, col: str) -> None:
        if self.agg_sort_column == col:
            self.agg_sort_reverse = not self.agg_sort_reverse
        else:
            self.agg_sort_column = col
            self.agg_sort_reverse = False

        self._refresh_aggregated()

    def _build_ui(self) -> None:
        self.root.rowconfigure(0, weight=2)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Top frame: Notebook with tabs for Detailed and Aggregated views
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Detailed tab
        detailed_frame = ttk.Frame(self.notebook)
        self.notebook.add(detailed_frame, text="Detailed Inventory")
        detailed_frame.rowconfigure(0, weight=1)
        detailed_frame.columnconfigure(0, weight=1)

        ttk.Label(detailed_frame, text="Current Inventory (Detailed)", font=(None, 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        self.inventory_tree = ttk.Treeview(
            detailed_frame,
            columns=("name", "quantity", "unit", "purchase_date", "expiration_date", "storage"),
            show="headings",
            height=15,
        )
        self.inventory_tree.heading("name", text="Product Name", command=lambda: self._sort_inventory("name"))
        self.inventory_tree.heading("quantity", text="Quantity", command=lambda: self._sort_inventory("quantity"))
        self.inventory_tree.heading("unit", text="Unit", command=lambda: self._sort_inventory("unit"))
        self.inventory_tree.heading("purchase_date", text="Purchase Date", command=lambda: self._sort_inventory("purchase_date"))
        self.inventory_tree.heading("expiration_date", text="Expiration Date", command=lambda: self._sort_inventory("expiration_date"))
        self.inventory_tree.heading("storage", text="Storage", command=lambda: self._sort_inventory("storage"))
        self.inventory_tree.column("name", width=150)
        self.inventory_tree.column("quantity", width=80)
        self.inventory_tree.column("unit", width=60)
        self.inventory_tree.column("purchase_date", width=120)
        self.inventory_tree.column("expiration_date", width=120)
        self.inventory_tree.column("storage", width=80)
        self.inventory_tree.grid(row=1, column=0, sticky="nsew")

        inv_scrollbar = ttk.Scrollbar(detailed_frame, orient="vertical", command=self.inventory_tree.yview)
        inv_scrollbar.grid(row=1, column=1, sticky="ns")
        self.inventory_tree.configure(yscrollcommand=inv_scrollbar.set)

        # Aggregated tab
        aggregated_frame = ttk.Frame(self.notebook)
        self.notebook.add(aggregated_frame, text="Aggregated Inventory")
        aggregated_frame.rowconfigure(0, weight=1)
        aggregated_frame.columnconfigure(0, weight=1)

        ttk.Label(aggregated_frame, text="Current Inventory (Aggregated)", font=(None, 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        self.aggregated_tree = ttk.Treeview(
            aggregated_frame,
            columns=("name", "total_quantity", "unit"),
            show="headings",
            height=15,
        )
        self.aggregated_tree.heading("name", text="Product Name", command=lambda: self._sort_aggregated("name"))
        self.aggregated_tree.heading("total_quantity", text="Total Quantity", command=lambda: self._sort_aggregated("total_quantity"))
        self.aggregated_tree.heading("unit", text="Unit", command=lambda: self._sort_aggregated("unit"))
        self.aggregated_tree.column("name", width=200)
        self.aggregated_tree.column("total_quantity", width=120)
        self.aggregated_tree.column("unit", width=80)
        self.aggregated_tree.grid(row=1, column=0, sticky="nsew")

        agg_scrollbar = ttk.Scrollbar(aggregated_frame, orient="vertical", command=self.aggregated_tree.yview)
        agg_scrollbar.grid(row=1, column=1, sticky="ns")
        self.aggregated_tree.configure(yscrollcommand=agg_scrollbar.set)

        # Bottom frame: Selection and actions (1/3)
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        bottom_frame.rowconfigure(0, weight=1)
        bottom_frame.columnconfigure(0, weight=1, minsize=400)
        bottom_frame.columnconfigure(1, weight=1)

        # Left: Product list
        left_frame = ttk.Frame(bottom_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)

        ttk.Label(left_frame, text="Available Products", font=(None, 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        self.product_listbox = tk.Listbox(left_frame, selectmode=tk.MULTIPLE, exportselection=False)
        self.product_listbox.grid(row=1, column=0, sticky="nsew")
        self.product_listbox.bind("<<ListboxSelect>>", self._on_product_select)

        prod_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.product_listbox.yview)
        prod_scrollbar.grid(row=1, column=1, sticky="ns")
        self.product_listbox.configure(yscrollcommand=prod_scrollbar.set)

        # Right: Selected with quantities
        right_frame = ttk.Frame(bottom_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)

        ttk.Label(right_frame, text="Selected Products & Quantities", font=(None, 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        self.selected_frame = ttk.Frame(right_frame)
        self.selected_frame.grid(row=1, column=0, sticky="nsew")
        self.selected_frame.rowconfigure(0, weight=1)
        self.selected_frame.columnconfigure(0, weight=1)

        # Canvas and scrollbar for selected items
        self.selected_canvas = tk.Canvas(self.selected_frame, height=100)
        self.selected_scrollbar = ttk.Scrollbar(self.selected_frame, orient="vertical", command=self.selected_canvas.yview)
        self.selected_scrollable_frame = ttk.Frame(self.selected_canvas)

        self.selected_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.selected_canvas.configure(scrollregion=self.selected_canvas.bbox("all"))
        )

        self.selected_canvas.create_window((0, 0), window=self.selected_scrollable_frame, anchor="nw")
        self.selected_canvas.configure(yscrollcommand=self.selected_scrollbar.set)

        self.selected_canvas.grid(row=0, column=0, sticky="nsew")
        self.selected_scrollbar.grid(row=0, column=1, sticky="ns")

        # Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=2, column=0, pady=(10, 0))

        self.add_button = ttk.Button(button_frame, text="Add", command=self._add_items)
        self.add_button.grid(row=0, column=0, padx=5)

        self.clear_button = ttk.Button(button_frame, text="Clear", command=self._clear_selection)
        self.clear_button.grid(row=0, column=1, padx=5)

        self.undo_button = ttk.Button(button_frame, text="Undo", command=self._undo_last_add, state="disabled")
        self.undo_button.grid(row=0, column=2, padx=5)

        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self._cancel)
        self.cancel_button.grid(row=0, column=3, padx=5)

    def _refresh_inventory(self) -> None:
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        product_dict = {p["barcode"]: p for p in self.products}

        for item in self.inventory:
            product = product_dict.get(item["barcode"], {})
            name = product.get("name", "Unknown")
            qty = f"{item['quantity']}"
            unit = item["unit"]
            purchase = item["purchase_date"].strftime("%Y-%m-%d")
            exp = item["expiration_date"].strftime("%Y-%m-%d")
            storage = item["storage_location"]
            self.inventory_tree.insert("", "end", values=(name, qty, unit, purchase, exp, storage))

    def _refresh_products(self) -> None:
        self.product_listbox.delete(0, tk.END)
        for product in self.products:
            name = product.get("name", "")
            barcode = product.get("barcode", "")
            display = f"{name} ({barcode})"
            self.product_listbox.insert(tk.END, display)

    def _on_product_select(self, event: tk.Event) -> None:
        selected_indices = self.product_listbox.curselection()
        self.selected_products = [self.products[i] for i in selected_indices]
        self._refresh_selected()

    def _refresh_selected(self) -> None:
        # Clear previous
        for widget in self.selected_scrollable_frame.winfo_children():
            widget.destroy()
        self.quantity_entries.clear()

        for idx, product in enumerate(self.selected_products):
            name = product.get("name", "")
            barcode = product.get("barcode", "")

            row_frame = ttk.Frame(self.selected_scrollable_frame)
            row_frame.grid(row=idx, column=0, sticky="ew", pady=2)

            ttk.Label(row_frame, text=f"{name} ({barcode})").grid(row=0, column=0, sticky="w")

            qty_entry = ttk.Entry(row_frame, width=10)
            qty_entry.insert(0, "1")  # Default quantity
            qty_entry.grid(row=0, column=1, padx=(10, 0))
            self.quantity_entries.append(qty_entry)

    def _add_items(self) -> None:
        if not self.selected_products:
            messagebox.showinfo("Add Items", "No products selected.")
            return

        items_to_add = []
        for product, qty_entry in zip(self.selected_products, self.quantity_entries):
            try:
                qty = float(qty_entry.get().strip())
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", f"Invalid quantity for {product.get('name', '')}.")
                return

            # Create inventory item
            new_item = {
                "barcode": product["barcode"],
                "quantity": qty,
                "unit": product["package_unit"],  # Assume package unit
                "purchase_date": datetime.now(),
                "opened_date": None,
                "expiration_date": datetime.now() + timedelta(days=365),  # Default 1 year
                "storage_location": "pantry",  # Default
            }
            items_to_add.append(new_item)

        # Confirmation dialog
        item_list = "\n".join(
            f"- {p['name']} ({p['barcode']}): {qty} {new_item['unit']}"
            for p, qty in zip(self.selected_products, [float(e.get()) for e in self.quantity_entries])
        )
        confirm = messagebox.askyesno(
            "Confirm Add",
            f"Add the following items to inventory?\n\n{item_list}"
        )
        if not confirm:
            return

        # Add to inventory
        self.inventory.extend(items_to_add)
        self.last_added = items_to_add.copy()
        save_inventory(self.inventory)
        self._refresh_inventory()
        self._refresh_aggregated()
        self.undo_button.config(state="normal")
        self._clear_selection()

    def _clear_selection(self) -> None:
        self.product_listbox.selection_clear(0, tk.END)
        self.selected_products.clear()
        self._refresh_selected()

    def _undo_last_add(self) -> None:
        if not self.last_added:
            return

        for item in self.last_added:
            if item in self.inventory:
                self.inventory.remove(item)

        save_inventory(self.inventory)
        self._refresh_inventory()
        self._refresh_aggregated()
        self.last_added.clear()
        self.undo_button.config(state="disabled")

    def _cancel(self) -> None:
        confirm = messagebox.askyesno("Cancel", "Close without saving changes?")
        if confirm:
            self.root.destroy()


def main() -> None:
    root = tk.Tk()
    InventoryManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
