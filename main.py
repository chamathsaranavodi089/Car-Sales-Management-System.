import datetime
import os
import shutil
import sys
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ================= MOCK DATABASE ================= #
MOCK_BRANDS = {
    1: "Sedan",
    2: "Hatchback",
    3: "SUV",
    4: "Coupe",
    5: "Pickup Truck",
    6: "MPV",
}

MOCK_CARS = {
    1: {
        "name": "Toyota Corolla",
        "brand": "Sedan",
        "price": 24000,
        "img": "Toyota Corolla.png",
    },
    2: {
        "name": "Honda Civic",
        "brand": "Sedan",
        "price": 25000,
        "img": "Honda Civic.png",
    },
    3: {
        "name": "Toyota Yaris",
        "brand": "Hatchback",
        "price": 20000,
        "img": "Toyota Yaris.png",
    },
    4: {
        "name": "Honda Fit",
        "brand": "Hatchback",
        "price": 19000,
        "img": "honda fit.png",
    },
    5: {
        "name": "Toyota RAV4",
        "brand": "SUV",
        "price": 32000,
        "img": "Toyota RAV4.png",
    },
    6: {
        "name": "Honda CR-V",
        "brand": "SUV",
        "price": 33000,
        "img": "Honda CR-V.png",
    },
    7: {
        "name": "BMW",
        "brand": "Coupe",
        "price": 38000,
        "img": "BMW.png",
    },
    8: {
        "name": "Toyota Hilux",
        "brand": "Pickup Truck",
        "price": 35000,
        "img": "Toyota Hilux.png",
    },
    9: {
        "name": "Ford Ranger",
        "brand": "Pickup Truck",
        "price": 36000,
        "img": "Ford ranger.png",
    },
    10: {
        "name": "Toyota Avanza",
        "brand": "MPV",
        "price": 22000,
        "img": "Toyota Avanza.png",
    },
    11: {
        "name": "Kia Carnival",
        "brand": "MPV",
        "price": 37000,
        "img": "Kia Carnival.png",
    },
}
MOCK_SALES = {}


# ================= ASSET DIRECTORY MANAGEMENT (EXE SAFE) ================= #
def get_base_dir():
    """Returns the base directory of the script or compiled EXE."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def ensure_asset_folder():
    """Ensures the assets directory exists relative to the EXE location."""
    assets_dir = os.path.join(get_base_dir(), "assets")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    return assets_dir


def get_asset_path(filename):
    """Resolves correct path for images, supporting PyInstaller bundles and external folders."""
    # 1. Check in external 'assets' folder next to the .exe file
    ext_path = os.path.join(get_base_dir(), "assets", filename)
    if os.path.exists(ext_path):
        return ext_path

    # 2. Check in PyInstaller internal temporary folder (_MEIPASS)
    if hasattr(sys, "_MEIPASS"):
        bundle_path = os.path.join(sys._MEIPASS, "assets", filename)
        if os.path.exists(bundle_path):
            return bundle_path

    return ext_path


# Initialize directory setup before UI startup
ensure_asset_folder()


# ================= DATABASE STUB FUNCTIONS ================= #
def fetch_categories():
    return list(MOCK_BRANDS.values())


def fetch_categories_full():
    return [(k, v) for k, v in MOCK_BRANDS.items()]


def fetch_menu_from_db():
    return [
        (v["name"], v["price"], v["img"], v["brand"])
        for v in MOCK_CARS.values()
    ]


def fetch_menu_full():
    return [
        (k, v["name"], v["brand"], v["price"], v["img"])
        for k, v in MOCK_CARS.items()
    ]


def fetch_orders():
    return [
        (k, v["date"], v["total"], v["items"]) for k, v in MOCK_SALES.items()
    ]


def save_category(name):
    new_id = len(MOCK_BRANDS) + 1
    MOCK_BRANDS[new_id] = name
    return True


def update_category_in_db(cat_id, name):
    MOCK_BRANDS[int(cat_id)] = name
    return True


def delete_category_from_db(cat_id):
    if int(cat_id) in MOCK_BRANDS:
        del MOCK_BRANDS[int(cat_id)]
    return True


def save_product(name, brand, price, img):
    new_id = len(MOCK_CARS) + 1
    MOCK_CARS[new_id] = {
        "name": name,
        "brand": brand,
        "price": price,
        "img": img,
    }
    return True


def update_product_in_db(car_id, name, brand, price, img):
    cid = int(car_id)
    if cid in MOCK_CARS:
        MOCK_CARS[cid]["name"] = name
        MOCK_CARS[cid]["brand"] = brand
        MOCK_CARS[cid]["price"] = price
        if img:
            MOCK_CARS[cid]["img"] = img
    return True


def delete_product_from_db(car_id):
    cid = int(car_id)
    if cid in MOCK_CARS:
        del MOCK_CARS[cid]
    return True


def save_order(cart, total):
    sale_id = len(MOCK_SALES) + 1
    items_str = ", ".join(
        [f"{item['row'].qty}x {name}" for name, item in cart.items()]
    )
    MOCK_SALES[sale_id] = {
        "date": datetime.date.today().strftime("%Y-%m-%d"),
        "total": total,
        "items": items_str,
    }
    return True


def delete_order_from_db(sale_id):
    sid = int(sale_id)
    if sid in MOCK_SALES:
        del MOCK_SALES[sid]
    return True


# ================= APPLICATION INIT ================= #
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Car Sales System")
app.geometry("1200x700")

# ================= STATE MANAGEMENT ================= #
current_brand = "All"
car_cards = []
cart_items = {}
selected_image_path = None
selected_brand_id = None
selected_car_id = None
selected_view_sale_id = None


# ================= NAVIGATION LOGIC ================= #
def show_page(page_name):
    home_page.grid_forget()
    add_brand_page.grid_forget()
    add_car_page.grid_forget()
    view_sales_page.grid_forget()

    if page_name == "home":
        home_page.grid(row=0, column=0, sticky="nsew")
        refresh_cars_grid()
    elif page_name == "brand":
        add_brand_page.grid(row=0, column=0, sticky="nsew")
        refresh_brand_table()
    elif page_name == "car":
        add_car_page.grid(row=0, column=0, sticky="nsew")
        refresh_car_table()
        update_car_brand_dropdown()
    elif page_name == "sales":
        view_sales_page.grid(row=0, column=0, sticky="nsew")
        refresh_sales_table()


# ================= ROOT GRID ================= #
app.grid_columnconfigure(1, weight=1)
app.grid_rowconfigure(0, weight=1)

# ================= LEFT SIDEBAR ================= #
brand_frame = ctk.CTkFrame(app, width=180, corner_radius=0)
brand_frame.grid(row=0, column=0, sticky="nsw", padx=5, pady=5)
brand_frame.grid_propagate(False)


def filter_brand(brand):
    global current_brand
    current_brand = brand
    show_page("home")
    update_grid()


def refresh_sidebar():
    for widget in brand_frame.winfo_children():
        widget.destroy()
    ctk.CTkLabel(
        brand_frame, text="Car Types", font=("Arial", 18, "bold")
    ).pack(pady=15)
    ctk.CTkButton(
        brand_frame,
        text="All",
        height=36,
        fg_color="#555",
        command=lambda: filter_brand("All"),
    ).pack(fill="x", padx=12, pady=4)

    for brand in fetch_categories():
        ctk.CTkButton(
            brand_frame,
            text=brand,
            height=36,
            command=lambda b=brand: filter_brand(b),
        ).pack(fill="x", padx=12, pady=4)


# ================= MIDDLE PANEL CONTAINER ================= #
middle_panel_container = ctk.CTkFrame(app, fg_color="transparent")
middle_panel_container.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
middle_panel_container.grid_rowconfigure(1, weight=1)
middle_panel_container.grid_columnconfigure(0, weight=1)

# --- GLOBAL NAVIGATION BAR ---
nav_bar = ctk.CTkFrame(middle_panel_container)
nav_bar.grid(row=0, column=0, sticky="ew", pady=(0, 5))

ctk.CTkButton(
    nav_bar, text="Showroom", width=90, command=lambda: show_page("home")
).pack(side="left", padx=8, pady=8)
ctk.CTkButton(
    nav_bar, text="Add Types", width=90, command=lambda: show_page("brand")
).pack(side="left", padx=8)
ctk.CTkButton(
    nav_bar, text="Add Cars", width=90, command=lambda: show_page("car")
).pack(side="left", padx=8)
ctk.CTkButton(
    nav_bar, text="View Sales", width=90, command=lambda: show_page("sales")
).pack(side="left", padx=8)

search_entry = ctk.CTkEntry(nav_bar, placeholder_text="Search cars...")
search_entry.pack(side="right", fill="x", expand=True, padx=10)
search_entry.bind("<KeyRelease>", lambda e: update_grid())

# --- PAGE CONTENT AREA ---
content_area = ctk.CTkFrame(middle_panel_container, fg_color="transparent")
content_area.grid(row=1, column=0, sticky="nsew")
content_area.grid_columnconfigure(0, weight=1)
content_area.grid_rowconfigure(0, weight=1)

# 1. HOME PAGE (SHOWROOM)
home_page = ctk.CTkFrame(content_area, fg_color="transparent")
cars_frame = ctk.CTkScrollableFrame(home_page)
cars_frame.pack(fill="both", expand=True, pady=0)
cars_frame.grid_columnconfigure((0, 1, 2), weight=1)

# 2. ADD TYPES (BRANDS) PAGE
add_brand_page = ctk.CTkFrame(content_area, fg_color="transparent")
brand_form = ctk.CTkFrame(add_brand_page, fg_color="#DBDBDB", corner_radius=15)
brand_form.pack(pady=20, padx=20, fill="x")

ctk.CTkLabel(
    brand_form, text="Car Type:", font=("Arial", 14, "bold"), text_color="black"
).pack(side="left", padx=15, pady=20)
brand_entry = ctk.CTkEntry(
    brand_form, placeholder_text="Enter type (e.g., Coupe)...", width=250
)
brand_entry.pack(side="left", padx=10)


def handle_save_brand():
    name = brand_entry.get().strip()
    if name and save_category(name):
        brand_entry.delete(0, "end")
        refresh_brand_table()
        refresh_sidebar()
        messagebox.showinfo("Success", "Car Type added!")


def handle_update_brand():
    global selected_brand_id
    name = brand_entry.get().strip()
    if selected_brand_id and name:
        if update_category_in_db(selected_brand_id, name):
            messagebox.showinfo("Success", "Car Type updated!")
            brand_entry.delete(0, "end")
            selected_brand_id = None
            refresh_brand_table()
            refresh_sidebar()
    else:
        messagebox.showwarning("Selection", "Please select a type first.")


def handle_delete_brand():
    global selected_brand_id
    if selected_brand_id:
        msg = "Are you sure? Ensure no cars are linked to this type."
        if messagebox.askyesno("Confirm Delete", msg):
            if delete_category_from_db(selected_brand_id):
                messagebox.showinfo("Success", "Car Type deleted!")
                brand_entry.delete(0, "end")
                selected_brand_id = None
                refresh_brand_table()
                refresh_sidebar()
                refresh_cars_grid()
    else:
        messagebox.showwarning("Selection", "Please select a type first.")


def on_brand_select(event):
    global selected_brand_id
    selected_item = brand_tree.focus()
    if selected_item:
        values = brand_tree.item(selected_item, "values")
        selected_brand_id = values[0]
        brand_entry.delete(0, "end")
        brand_entry.insert(0, values[1])


ctk.CTkButton(
    brand_form, text="Save", width=80, command=handle_save_brand
).pack(side="left", padx=5)
ctk.CTkButton(
    brand_form,
    text="Update",
    width=80,
    fg_color="#fbbf24",
    hover_color="#d97706",
    text_color="black",
    command=handle_update_brand,
).pack(side="left", padx=5)
ctk.CTkButton(
    brand_form,
    text="Delete",
    width=80,
    fg_color="#ef4444",
    hover_color="#b91c1c",
    command=handle_delete_brand,
).pack(side="left", padx=5)

brand_table_frame = ctk.CTkFrame(
    add_brand_page, fg_color="white", corner_radius=15, height=350
)
brand_table_frame.pack(pady=10, padx=20, fill="x")
brand_table_frame.pack_propagate(False)

brand_tree = ttk.Treeview(
    brand_table_frame, columns=("ID", "Name"), show="headings"
)
brand_tree.heading("ID", text="ID")
brand_tree.heading("Name", text="Car Type")
brand_tree.column("ID", width=100, anchor="center")
brand_tree.pack(fill="both", expand=True, padx=15, pady=15)
brand_tree.bind("<<TreeviewSelect>>", on_brand_select)


def refresh_brand_table():
    for item in brand_tree.get_children():
        brand_tree.delete(item)
    for cid, name in fetch_categories_full():
        brand_tree.insert("", "end", values=(cid, name))


# 3. ADD CARS PAGE
add_car_page = ctk.CTkFrame(content_area, fg_color="transparent")
car_form = ctk.CTkFrame(add_car_page, fg_color="#DBDBDB", corner_radius=15)
car_form.pack(pady=20, padx=20, fill="x")
car_form.columnconfigure((1, 3), weight=1)

ctk.CTkLabel(car_form, text="Car Model:", text_color="black").grid(
    row=0, column=0, padx=10, pady=10
)
car_name_entry = ctk.CTkEntry(car_form)
car_name_entry.grid(row=0, column=1, sticky="ew", padx=10)

ctk.CTkLabel(car_form, text="Type:", text_color="black").grid(
    row=0, column=2, padx=10
)
car_brand_dropdown = ctk.CTkOptionMenu(car_form, values=["Select Type"])
car_brand_dropdown.grid(row=0, column=3, sticky="ew", padx=10)

ctk.CTkLabel(car_form, text="Price ($):", text_color="black").grid(
    row=1, column=0, padx=10, pady=10
)
car_price_entry = ctk.CTkEntry(car_form)
car_price_entry.grid(row=1, column=1, sticky="ew", padx=10)


def choose_image():
    global selected_image_path
    path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg *.png *.jpeg")]
    )
    if path:
        selected_image_path = path
        img_btn.configure(text=os.path.basename(path), fg_color="#28a745")


img_btn = ctk.CTkButton(
    car_form, text="Choose Image", command=choose_image, fg_color="#555"
)
img_btn.grid(row=1, column=2, columnspan=2, sticky="ew", padx=10)


def handle_save_car():
    name = car_name_entry.get().strip()
    brand = car_brand_dropdown.get()
    price = car_price_entry.get().strip()
    if not (name and price and selected_image_path and brand != "Select Type"):
        messagebox.showwarning("Error", "All fields are required!")
        return
    filename = os.path.basename(selected_image_path)
    asset_dir = ensure_asset_folder()
    shutil.copy(selected_image_path, os.path.join(asset_dir, filename))
    if save_product(name, brand, int(float(price)), filename):
        messagebox.showinfo("Success", "Car added!")
        clear_car_form()
        refresh_car_table()
        refresh_cars_grid()


def handle_update_car():
    global selected_car_id, selected_image_path
    name = car_name_entry.get().strip()
    brand = car_brand_dropdown.get()
    price = car_price_entry.get().strip()
    if not selected_car_id:
        messagebox.showwarning(
            "Selection", "Please select a car from the table."
        )
        return
    filename = None
    if selected_image_path:
        filename = os.path.basename(selected_image_path)
        asset_dir = ensure_asset_folder()
        shutil.copy(selected_image_path, os.path.join(asset_dir, filename))
    if update_product_in_db(
        selected_car_id, name, brand, int(float(price)), filename
    ):
        messagebox.showinfo("Success", "Car updated!")
        clear_car_form()
        refresh_car_table()
        refresh_cars_grid()


def handle_delete_car():
    global selected_car_id
    if selected_car_id:
        if messagebox.askyesno(
            "Confirm", "Are you sure you want to delete this car?"
        ):
            if delete_product_from_db(selected_car_id):
                messagebox.showinfo("Success", "Car deleted!")
                clear_car_form()
                refresh_car_table()
                refresh_cars_grid()
    else:
        messagebox.showwarning("Selection", "Please select a car first.")


def on_car_select(event):
    global selected_car_id, selected_image_path
    selected_item = car_tree.focus()
    if selected_item:
        values = car_tree.item(selected_item, "values")
        selected_car_id = values[0]
        car_name_entry.delete(0, "end")
        car_name_entry.insert(0, values[1])
        car_brand_dropdown.set(values[2])
        car_price_entry.delete(0, "end")
        car_price_entry.insert(0, int(float(values[3])))
        img_btn.configure(text=values[4], fg_color="#28a745")
        selected_image_path = None


def clear_car_form():
    global selected_car_id, selected_image_path
    selected_car_id = None
    selected_image_path = None
    car_name_entry.delete(0, "end")
    car_price_entry.delete(0, "end")
    car_brand_dropdown.set("Select Type")
    img_btn.configure(text="Choose Image", fg_color="#555")


btn_frame = ctk.CTkFrame(car_form, fg_color="transparent")
btn_frame.grid(row=2, column=0, columnspan=4, pady=15)
ctk.CTkButton(
    btn_frame, text="Save Car", command=handle_save_car, width=120, height=40
).pack(side="left", padx=10)
ctk.CTkButton(
    btn_frame,
    text="Update Car",
    command=handle_update_car,
    width=120,
    height=40,
    fg_color="#fbbf24",
    hover_color="#d97706",
    text_color="black",
).pack(side="left", padx=10)
ctk.CTkButton(
    btn_frame,
    text="Delete Car",
    command=handle_delete_car,
    width=120,
    height=40,
    fg_color="#ef4444",
    hover_color="#b91c1c",
).pack(side="left", padx=10)

car_table_frame = ctk.CTkFrame(
    add_car_page, fg_color="white", corner_radius=15, height=280
)
car_table_frame.pack(pady=10, padx=20, fill="x")
car_table_frame.pack_propagate(False)

car_tree = ttk.Treeview(
    car_table_frame,
    columns=("ID", "Model", "Type", "Price", "Image"),
    show="headings",
)
for col in ("ID", "Model", "Type", "Price", "Image"):
    car_tree.heading(col, text=col)
    car_tree.column(col, width=100, anchor="center")
car_tree.pack(fill="both", expand=True, padx=15, pady=15)
car_tree.bind("<<TreeviewSelect>>", on_car_select)


def refresh_car_table():
    for item in car_tree.get_children():
        car_tree.delete(item)
    for row in fetch_menu_full():
        cleaned_row = list(row)
        cleaned_row[3] = int(float(row[3]))
        car_tree.insert("", "end", values=cleaned_row)


def update_car_brand_dropdown():
    brands = fetch_categories()
    car_brand_dropdown.configure(values=brands)


# 4. VIEW SALES PAGE
view_sales_page = ctk.CTkFrame(content_area, fg_color="transparent")

sale_search_frame = ctk.CTkFrame(
    view_sales_page, fg_color="#DBDBDB", corner_radius=15
)
sale_search_frame.pack(pady=20, padx=20, fill="x")
ctk.CTkLabel(
    sale_search_frame,
    text="Search Sale ID:",
    font=("Arial", 14, "bold"),
    text_color="black",
).pack(side="left", padx=15, pady=20)
sale_search_entry = ctk.CTkEntry(
    sale_search_frame, placeholder_text="Enter ID...", width=200
)
sale_search_entry.pack(side="left", padx=10)
sale_search_entry.bind("<KeyRelease>", lambda e: refresh_sales_table())


def on_sale_select(event):
    global selected_view_sale_id
    selected_item = sale_tree.focus()
    if selected_item:
        values = sale_tree.item(selected_item, "values")
        selected_view_sale_id = values[0]


def handle_delete_sale():
    global selected_view_sale_id
    if selected_view_sale_id:
        if messagebox.askyesno(
            "Confirm", f"Delete Sale #{selected_view_sale_id}?"
        ):
            if delete_order_from_db(selected_view_sale_id):
                messagebox.showinfo("Success", "Sale deleted!")
                selected_view_sale_id = None
                refresh_sales_table()
    else:
        messagebox.showwarning(
            "Selection", "Please select a sale from the table."
        )


ctk.CTkButton(
    sale_search_frame,
    text="Delete Sale",
    fg_color="#ef4444",
    hover_color="#b91c1c",
    command=handle_delete_sale,
).pack(side="right", padx=15)

sale_table_frame = ctk.CTkFrame(
    view_sales_page, fg_color="white", corner_radius=15, height=400
)
sale_table_frame.pack(pady=10, padx=20, fill="x")
sale_table_frame.pack_propagate(False)

sale_tree = ttk.Treeview(
    sale_table_frame,
    columns=("ID", "Date", "Total", "Items"),
    show="headings",
)
for col in ("ID", "Date", "Total", "Items"):
    sale_tree.heading(col, text=col)
    sale_tree.column(col, width=150, anchor="center")
sale_tree.column("Items", width=400, anchor="w")
sale_tree.pack(fill="both", expand=True, padx=15, pady=15)
sale_tree.bind("<<TreeviewSelect>>", on_sale_select)


def refresh_sales_table():
    for item in sale_tree.get_children():
        sale_tree.delete(item)
    search_term = sale_search_entry.get().strip()
    sales = fetch_orders()
    for row in sales:
        if not search_term or str(row[0]).startswith(search_term):
            cleaned_sale = list(row)
            cleaned_sale[2] = int(float(row[2]))
            sale_tree.insert("", "end", values=cleaned_sale)


# ================= HELPER FUNCTIONS ================= #
def get_clipped_image(img_path, target_size, radius):
    try:
        img = Image.open(img_path).convert("RGBA")
        img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
        mask = Image.new("L", target_size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle(
            [0, 0, target_size[0], target_size[1] + radius],
            radius=radius,
            fill=255,
        )
        result = Image.new("RGBA", target_size, (0, 0, 0, 0))
        result.paste(img, (0, 0), mask=mask)
        return result
    except Exception:
        return None


def car_card(parent, name, price, img_path, brand):
    card_width, img_height, corner_rad = 220, 130, 15
    card = ctk.CTkFrame(
        parent, height=260, corner_radius=corner_rad, fg_color="#DBDBDB"
    )
    card.pack_propagate(False)
    card.brand, card.car_name = brand, name

    # Resolve exact path for EXE / dev workspace
    full_img_path = get_asset_path(img_path)
    img = get_clipped_image(full_img_path, (300, img_height), corner_rad)
    if img:
        ctk_img = ctk.CTkImage(light_image=img, size=(240, img_height))
        ctk_img_lbl = ctk.CTkLabel(card, text="", image=ctk_img)
        ctk_img_lbl.pack(side="top", fill="x")
    else:
        ctk.CTkLabel(
            card,
            text="No Image",
            height=img_height,
            fg_color="#e2e2e2",
            text_color="gray",
        ).pack(fill="x")

    ctk.CTkLabel(
        card, text=name, font=("Arial", 15, "bold"), text_color="black"
    ).pack(pady=(6, 0))
    ctk.CTkLabel(
        card, text=f"$ {int(price):,}", font=("Arial", 13), text_color="#1e293b"
    ).pack()

    btn_cont = ctk.CTkFrame(card, fg_color="transparent")
    btn_cont.pack(side="bottom", fill="x", padx=10, pady=8)
    ctk.CTkButton(
        btn_cont,
        text="Add to Sale",
        height=32,
        command=lambda: add_to_cart(name, price),
    ).pack(fill="x", expand=True)
    return card


def refresh_cars_grid():
    global car_cards
    for card in car_cards:
        card.destroy()
    car_cards.clear()
    cars_data = fetch_menu_from_db()
    for name, price, img, brand in cars_data:
        card = car_card(cars_frame, name, price, img, brand)
        car_cards.append(card)
    update_grid()


def update_grid(event=None):
    search_term = search_entry.get().lower()
    visible_cards = []
    for card in car_cards:
        if (current_brand == "All" or card.brand == current_brand) and (
            search_term in card.car_name.lower()
        ):
            visible_cards.append(card)
            card.grid()
        else:
            card.grid_forget()
    num_cols = 3
    for i, card in enumerate(visible_cards):
        card.grid(
            row=i // num_cols, column=i % num_cols, padx=10, pady=10, sticky="nsew"
        )


# ================= CART & ORDER LOGIC ================= #
def add_to_cart(name, price):
    if name in cart_items:
        cart_items[name]["row"].increase()
    else:
        cart_items[name] = {"row": SaleItem(sale_frame, name, price)}
    update_total()


def update_total():
    total = sum(
        item["row"].qty * item["row"].price for item in cart_items.values()
    )
    total_label.configure(text=f"Total: $ {int(total):,}")


def clear_cart():
    global cart_items
    for widget in sale_frame.winfo_children():
        widget.destroy()
    cart_items.clear()
    update_total()


def handle_enter_button():
    if not cart_items:
        messagebox.showwarning(
            "Empty Sale", "Please add cars to the sale list first."
        )
        return
    total_val = sum(i["row"].qty * i["row"].price for i in cart_items.values())
    if save_order(cart_items, int(total_val)):
        messagebox.showinfo("Success", "Sale completed successfully!")
        clear_cart()


class SaleItem(ctk.CTkFrame):

    def __init__(self, parent, name, price):
        super().__init__(parent, corner_radius=15)
        self.pack(fill="x", padx=10, pady=6)
        self.name, self.price, self.qty = name, price, 1
        self.expanded = False
        self.normal_color = self.cget("fg_color")
        self.selected_color = "#dbeafe"

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="x", padx=15, pady=10)
        self.container.bind("<Button-1>", self.toggle)

        self.name_lbl = ctk.CTkLabel(
            self.container, text=name, font=("Arial", 15, "bold")
        )
        self.name_lbl.pack(anchor="w", pady=(0, 4))
        self.name_lbl.bind("<Button-1>", self.toggle)

        self.info_row = ctk.CTkFrame(self.container, fg_color="transparent")
        self.info_row.pack(fill="x")
        self.info_row.bind("<Button-1>", self.toggle)

        self.price_lbl = ctk.CTkLabel(
            self.info_row, text=f"${int(price):,}", font=("Arial", 13)
        )
        self.price_lbl.pack(side="left")
        self.qty_lbl = ctk.CTkLabel(
            self.info_row, text="1", font=("Arial", 13, "bold")
        )
        self.qty_lbl.pack(side="left", expand=True)
        self.total_lbl = ctk.CTkLabel(
            self.info_row, text=f"${int(price):,}", font=("Arial", 13)
        )
        self.total_lbl.pack(side="right")

        self.controls = ctk.CTkFrame(self, fg_color="transparent")
        ctk.CTkButton(
            self.controls,
            text="−",
            width=45,
            height=30,
            fg_color="#3b82f6",
            command=self.decrease,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            self.controls,
            text="+",
            width=45,
            height=30,
            fg_color="#3b82f6",
            command=self.increase,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            self.controls,
            text="🗑",
            width=45,
            height=30,
            fg_color="#ef4444",
            command=self.delete,
        ).pack(side="left", padx=4)

    def toggle(self, event=None):
        if self.expanded:
            self.controls.pack_forget()
            self.configure(fg_color=self.normal_color)
        else:
            self.controls.pack(pady=(0, 10))
            self.configure(fg_color=self.selected_color)
        self.expanded = not self.expanded

    def increase(self):
        self.qty += 1
        self.update_view()
        update_total()

    def decrease(self):
        if self.qty > 1:
            self.qty -= 1
            self.update_view()
            update_total()

    def delete(self):
        if self.name in cart_items:
            del cart_items[self.name]
        self.destroy()
        update_total()

    def update_view(self):
        self.qty_lbl.configure(text=f"{self.qty}")
        self.total_lbl.configure(text=f"${int(self.qty * self.price):,}")


# ================= RIGHT PANEL (SALES LIST) ================= #
right_frame = ctk.CTkFrame(app, width=350)
right_frame.grid(row=0, column=2, sticky="nse", padx=5, pady=5)
right_frame.grid_propagate(False)

ctk.CTkLabel(
    right_frame, text="Current Sale", font=("Arial", 20, "bold")
).pack(pady=12)
sale_frame = ctk.CTkScrollableFrame(right_frame, height=380)
sale_frame.pack(fill="both", expand=True, padx=10, pady=5)

bottom_panel = ctk.CTkFrame(right_frame, fg_color="#e0e0e0", corner_radius=10)
bottom_panel.pack(fill="x", padx=15, pady=15)

total_label = ctk.CTkLabel(
    bottom_panel, text="Total: $ 0", font=("Arial", 18, "bold")
)
total_label.pack(pady=10)

enter_btn = ctk.CTkButton(
    bottom_panel,
    text="Complete Sale",
    width=250,
    height=45,
    fg_color="#28a745",
    hover_color="#218838",
    font=("Arial", 16, "bold"),
    command=handle_enter_button,
)
enter_btn.pack(pady=(0, 15))

# ================= INITIALIZATION ================= #
refresh_sidebar()
refresh_cars_grid()
show_page("home")

app.mainloop()