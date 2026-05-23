from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Supplier(db.Model):
    __tablename__ = "suppliers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact_name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)


class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact_name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)


class RawMaterial(db.Model):
    __tablename__ = "raw_materials"
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    current_stock = db.Column(db.Float, nullable=False, default=0)
    reorder_level = db.Column(db.Float, nullable=False, default=0)
    unit_cost = db.Column(db.Float, nullable=False, default=0)

    @property
    def is_low_stock(self) -> bool:
        return self.current_stock < self.reorder_level


class FinishedProduct(db.Model):
    __tablename__ = "finished_products"
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    current_stock = db.Column(db.Float, nullable=False, default=0)
    unit_price = db.Column(db.Float, nullable=False, default=0)


class Recipe(db.Model):
    __tablename__ = "recipes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("finished_products.id"), nullable=False)
    output_quantity = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)

    product = db.relationship("FinishedProduct")
    items = db.relationship(
        "RecipeItem", backref="recipe", cascade="all, delete-orphan"
    )


class RecipeItem(db.Model):
    __tablename__ = "recipe_items"
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    raw_material_id = db.Column(db.Integer, db.ForeignKey("raw_materials.id"), nullable=False)
    quantity = db.Column(db.Float, nullable=False)

    raw_material = db.relationship("RawMaterial")


class ProductionBatch(db.Model):
    __tablename__ = "production_batches"
    id = db.Column(db.Integer, primary_key=True)
    batch_code = db.Column(db.String(50), unique=True, nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    planned_quantity = db.Column(db.Float, nullable=False)
    actual_quantity = db.Column(db.Float)
    status = db.Column(db.String(20), nullable=False, default="planned")
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipe = db.relationship("Recipe")


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="draft")
    order_date = db.Column(db.Date)
    expected_date = db.Column(db.Date)
    received_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship("Supplier")
    items = db.relationship(
        "PurchaseOrderItem", backref="po", cascade="all, delete-orphan"
    )

    @property
    def total(self) -> float:
        return sum(item.quantity * item.unit_cost for item in self.items)


class PurchaseOrderItem(db.Model):
    __tablename__ = "purchase_order_items"
    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False)
    raw_material_id = db.Column(db.Integer, db.ForeignKey("raw_materials.id"), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float, nullable=False)

    raw_material = db.relationship("RawMaterial")


class SalesOrder(db.Model):
    __tablename__ = "sales_orders"
    id = db.Column(db.Integer, primary_key=True)
    so_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="draft")
    order_date = db.Column(db.Date)
    shipped_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer")
    items = db.relationship(
        "SalesOrderItem", backref="so", cascade="all, delete-orphan"
    )

    @property
    def total(self) -> float:
        return sum(item.quantity * item.unit_price for item in self.items)


class SalesOrderItem(db.Model):
    __tablename__ = "sales_order_items"
    id = db.Column(db.Integer, primary_key=True)
    so_id = db.Column(db.Integer, db.ForeignKey("sales_orders.id"), nullable=False)
    finished_product_id = db.Column(db.Integer, db.ForeignKey("finished_products.id"), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    finished_product = db.relationship("FinishedProduct")
