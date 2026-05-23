from datetime import date, datetime

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from models import (
    Customer,
    FinishedProduct,
    ProductionBatch,
    PurchaseOrder,
    PurchaseOrderItem,
    RawMaterial,
    Recipe,
    RecipeItem,
    SalesOrder,
    SalesOrderItem,
    Supplier,
    db,
)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///erp.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "candy-erp-dev-secret"

    db.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


def parse_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def register_routes(app: Flask) -> None:
    # -----------------------------------------------------------------
    # Dashboard
    # -----------------------------------------------------------------
    @app.route("/")
    def dashboard():
        low_stock = RawMaterial.query.filter(
            RawMaterial.current_stock < RawMaterial.reorder_level
        ).all()
        stats = {
            "raw_materials": RawMaterial.query.count(),
            "finished_products": FinishedProduct.query.count(),
            "recipes": Recipe.query.count(),
            "suppliers": Supplier.query.count(),
            "customers": Customer.query.count(),
            "open_batches": ProductionBatch.query.filter(
                ProductionBatch.status.in_(["planned", "in_progress"])
            ).count(),
            "open_sales": SalesOrder.query.filter(
                SalesOrder.status.in_(["draft", "confirmed"])
            ).count(),
            "open_purchases": PurchaseOrder.query.filter(
                PurchaseOrder.status.in_(["draft", "ordered"])
            ).count(),
        }
        recent_batches = (
            ProductionBatch.query.order_by(ProductionBatch.created_at.desc()).limit(5).all()
        )
        recent_sales = (
            SalesOrder.query.order_by(SalesOrder.created_at.desc()).limit(5).all()
        )
        recent_purchases = (
            PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).limit(5).all()
        )
        return render_template(
            "dashboard.html",
            stats=stats,
            low_stock=low_stock,
            recent_batches=recent_batches,
            recent_sales=recent_sales,
            recent_purchases=recent_purchases,
        )

    # -----------------------------------------------------------------
    # Suppliers
    # -----------------------------------------------------------------
    @app.route("/suppliers")
    def suppliers_list():
        suppliers = Supplier.query.order_by(Supplier.name).all()
        return render_template("suppliers/list.html", suppliers=suppliers)

    @app.route("/suppliers/new", methods=["GET", "POST"])
    @app.route("/suppliers/<int:supplier_id>/edit", methods=["GET", "POST"])
    def suppliers_edit(supplier_id=None):
        supplier = Supplier.query.get_or_404(supplier_id) if supplier_id else Supplier()
        if request.method == "POST":
            supplier.name = request.form["name"].strip()
            supplier.contact_name = request.form.get("contact_name", "").strip() or None
            supplier.email = request.form.get("email", "").strip() or None
            supplier.phone = request.form.get("phone", "").strip() or None
            supplier.address = request.form.get("address", "").strip() or None
            if not supplier.name:
                flash("Name is required.", "error")
            else:
                if supplier.id is None:
                    db.session.add(supplier)
                db.session.commit()
                flash("Supplier saved.", "success")
                return redirect(url_for("suppliers_list"))
        return render_template("suppliers/form.html", supplier=supplier)

    @app.route("/suppliers/<int:supplier_id>/delete", methods=["POST"])
    def suppliers_delete(supplier_id):
        supplier = Supplier.query.get_or_404(supplier_id)
        if supplier.id and PurchaseOrder.query.filter_by(supplier_id=supplier.id).first():
            flash("Cannot delete supplier with purchase orders.", "error")
            return redirect(url_for("suppliers_list"))
        db.session.delete(supplier)
        db.session.commit()
        flash("Supplier deleted.", "success")
        return redirect(url_for("suppliers_list"))

    # -----------------------------------------------------------------
    # Customers
    # -----------------------------------------------------------------
    @app.route("/customers")
    def customers_list():
        customers = Customer.query.order_by(Customer.name).all()
        return render_template("customers/list.html", customers=customers)

    @app.route("/customers/new", methods=["GET", "POST"])
    @app.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
    def customers_edit(customer_id=None):
        customer = Customer.query.get_or_404(customer_id) if customer_id else Customer()
        if request.method == "POST":
            customer.name = request.form["name"].strip()
            customer.contact_name = request.form.get("contact_name", "").strip() or None
            customer.email = request.form.get("email", "").strip() or None
            customer.phone = request.form.get("phone", "").strip() or None
            customer.address = request.form.get("address", "").strip() or None
            if not customer.name:
                flash("Name is required.", "error")
            else:
                if customer.id is None:
                    db.session.add(customer)
                db.session.commit()
                flash("Customer saved.", "success")
                return redirect(url_for("customers_list"))
        return render_template("customers/form.html", customer=customer)

    @app.route("/customers/<int:customer_id>/delete", methods=["POST"])
    def customers_delete(customer_id):
        customer = Customer.query.get_or_404(customer_id)
        if SalesOrder.query.filter_by(customer_id=customer.id).first():
            flash("Cannot delete customer with sales orders.", "error")
            return redirect(url_for("customers_list"))
        db.session.delete(customer)
        db.session.commit()
        flash("Customer deleted.", "success")
        return redirect(url_for("customers_list"))

    # -----------------------------------------------------------------
    # Raw materials
    # -----------------------------------------------------------------
    @app.route("/raw-materials")
    def raw_materials_list():
        materials = RawMaterial.query.order_by(RawMaterial.name).all()
        return render_template("raw_materials/list.html", materials=materials)

    @app.route("/raw-materials/new", methods=["GET", "POST"])
    @app.route("/raw-materials/<int:material_id>/edit", methods=["GET", "POST"])
    def raw_materials_edit(material_id=None):
        material = RawMaterial.query.get_or_404(material_id) if material_id else RawMaterial()
        if request.method == "POST":
            material.sku = request.form["sku"].strip()
            material.name = request.form["name"].strip()
            material.unit = request.form["unit"].strip()
            material.current_stock = parse_float(request.form.get("current_stock"))
            material.reorder_level = parse_float(request.form.get("reorder_level"))
            material.unit_cost = parse_float(request.form.get("unit_cost"))
            if not material.sku or not material.name or not material.unit:
                flash("SKU, name, and unit are required.", "error")
            else:
                if material.id is None:
                    db.session.add(material)
                db.session.commit()
                flash("Raw material saved.", "success")
                return redirect(url_for("raw_materials_list"))
        return render_template("raw_materials/form.html", material=material)

    @app.route("/raw-materials/<int:material_id>/delete", methods=["POST"])
    def raw_materials_delete(material_id):
        material = RawMaterial.query.get_or_404(material_id)
        if RecipeItem.query.filter_by(raw_material_id=material.id).first():
            flash("Cannot delete raw material used in a recipe.", "error")
            return redirect(url_for("raw_materials_list"))
        db.session.delete(material)
        db.session.commit()
        flash("Raw material deleted.", "success")
        return redirect(url_for("raw_materials_list"))

    # -----------------------------------------------------------------
    # Finished products
    # -----------------------------------------------------------------
    @app.route("/products")
    def products_list():
        products = FinishedProduct.query.order_by(FinishedProduct.name).all()
        return render_template("finished_products/list.html", products=products)

    @app.route("/products/new", methods=["GET", "POST"])
    @app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
    def products_edit(product_id=None):
        product = FinishedProduct.query.get_or_404(product_id) if product_id else FinishedProduct()
        if request.method == "POST":
            product.sku = request.form["sku"].strip()
            product.name = request.form["name"].strip()
            product.unit = request.form["unit"].strip()
            product.current_stock = parse_float(request.form.get("current_stock"))
            product.unit_price = parse_float(request.form.get("unit_price"))
            if not product.sku or not product.name or not product.unit:
                flash("SKU, name, and unit are required.", "error")
            else:
                if product.id is None:
                    db.session.add(product)
                db.session.commit()
                flash("Product saved.", "success")
                return redirect(url_for("products_list"))
        return render_template("finished_products/form.html", product=product)

    @app.route("/products/<int:product_id>/delete", methods=["POST"])
    def products_delete(product_id):
        product = FinishedProduct.query.get_or_404(product_id)
        if Recipe.query.filter_by(product_id=product.id).first():
            flash("Cannot delete product that has a recipe.", "error")
            return redirect(url_for("products_list"))
        db.session.delete(product)
        db.session.commit()
        flash("Product deleted.", "success")
        return redirect(url_for("products_list"))

    # -----------------------------------------------------------------
    # Recipes
    # -----------------------------------------------------------------
    @app.route("/recipes")
    def recipes_list():
        recipes = Recipe.query.order_by(Recipe.name).all()
        return render_template("recipes/list.html", recipes=recipes)

    @app.route("/recipes/new", methods=["GET", "POST"])
    def recipes_new():
        if request.method == "POST":
            name = request.form["name"].strip()
            product_id = request.form.get("product_id", type=int)
            output_quantity = parse_float(request.form.get("output_quantity"))
            notes = request.form.get("notes", "").strip() or None
            if not name or not product_id or output_quantity <= 0:
                flash("Name, product, and a positive output quantity are required.", "error")
            else:
                recipe = Recipe(
                    name=name,
                    product_id=product_id,
                    output_quantity=output_quantity,
                    notes=notes,
                )
                db.session.add(recipe)
                db.session.commit()
                flash("Recipe created. Add ingredients below.", "success")
                return redirect(url_for("recipes_detail", recipe_id=recipe.id))
        products = FinishedProduct.query.order_by(FinishedProduct.name).all()
        return render_template("recipes/form.html", recipe=None, products=products)

    @app.route("/recipes/<int:recipe_id>", methods=["GET", "POST"])
    def recipes_detail(recipe_id):
        recipe = Recipe.query.get_or_404(recipe_id)
        if request.method == "POST":
            recipe.name = request.form["name"].strip()
            recipe.product_id = request.form.get("product_id", type=int)
            recipe.output_quantity = parse_float(request.form.get("output_quantity"))
            recipe.notes = request.form.get("notes", "").strip() or None
            db.session.commit()
            flash("Recipe updated.", "success")
            return redirect(url_for("recipes_detail", recipe_id=recipe.id))
        products = FinishedProduct.query.order_by(FinishedProduct.name).all()
        materials = RawMaterial.query.order_by(RawMaterial.name).all()
        return render_template(
            "recipes/detail.html", recipe=recipe, products=products, materials=materials
        )

    @app.route("/recipes/<int:recipe_id>/items/add", methods=["POST"])
    def recipes_add_item(recipe_id):
        recipe = Recipe.query.get_or_404(recipe_id)
        raw_material_id = request.form.get("raw_material_id", type=int)
        quantity = parse_float(request.form.get("quantity"))
        if not raw_material_id or quantity <= 0:
            flash("Select a raw material and a positive quantity.", "error")
        else:
            db.session.add(
                RecipeItem(
                    recipe_id=recipe.id,
                    raw_material_id=raw_material_id,
                    quantity=quantity,
                )
            )
            db.session.commit()
            flash("Ingredient added.", "success")
        return redirect(url_for("recipes_detail", recipe_id=recipe.id))

    @app.route("/recipes/<int:recipe_id>/items/<int:item_id>/delete", methods=["POST"])
    def recipes_remove_item(recipe_id, item_id):
        item = RecipeItem.query.get_or_404(item_id)
        if item.recipe_id != recipe_id:
            abort(404)
        db.session.delete(item)
        db.session.commit()
        flash("Ingredient removed.", "success")
        return redirect(url_for("recipes_detail", recipe_id=recipe_id))

    @app.route("/recipes/<int:recipe_id>/delete", methods=["POST"])
    def recipes_delete(recipe_id):
        recipe = Recipe.query.get_or_404(recipe_id)
        if ProductionBatch.query.filter_by(recipe_id=recipe.id).first():
            flash("Cannot delete recipe used in production batches.", "error")
            return redirect(url_for("recipes_list"))
        db.session.delete(recipe)
        db.session.commit()
        flash("Recipe deleted.", "success")
        return redirect(url_for("recipes_list"))

    # -----------------------------------------------------------------
    # Production batches
    # -----------------------------------------------------------------
    @app.route("/production")
    def production_list():
        batches = ProductionBatch.query.order_by(ProductionBatch.created_at.desc()).all()
        return render_template("production/list.html", batches=batches)

    @app.route("/production/new", methods=["GET", "POST"])
    def production_new():
        recipes = Recipe.query.order_by(Recipe.name).all()
        if request.method == "POST":
            batch_code = request.form["batch_code"].strip()
            recipe_id = request.form.get("recipe_id", type=int)
            planned_quantity = parse_float(request.form.get("planned_quantity"))
            notes = request.form.get("notes", "").strip() or None
            if not batch_code or not recipe_id or planned_quantity <= 0:
                flash("Batch code, recipe, and positive planned quantity required.", "error")
            elif ProductionBatch.query.filter_by(batch_code=batch_code).first():
                flash("Batch code already exists.", "error")
            else:
                batch = ProductionBatch(
                    batch_code=batch_code,
                    recipe_id=recipe_id,
                    planned_quantity=planned_quantity,
                    notes=notes,
                    status="planned",
                )
                db.session.add(batch)
                db.session.commit()
                flash("Production batch created.", "success")
                return redirect(url_for("production_detail", batch_id=batch.id))
        return render_template("production/form.html", recipes=recipes)

    @app.route("/production/<int:batch_id>")
    def production_detail(batch_id):
        batch = ProductionBatch.query.get_or_404(batch_id)
        scale = (batch.actual_quantity or batch.planned_quantity) / batch.recipe.output_quantity
        required = [
            {
                "material": item.raw_material,
                "needed": item.quantity * scale,
                "available": item.raw_material.current_stock,
            }
            for item in batch.recipe.items
        ]
        return render_template("production/detail.html", batch=batch, required=required)

    @app.route("/production/<int:batch_id>/start", methods=["POST"])
    def production_start(batch_id):
        batch = ProductionBatch.query.get_or_404(batch_id)
        if batch.status != "planned":
            flash("Only planned batches can be started.", "error")
        else:
            batch.status = "in_progress"
            batch.start_date = datetime.utcnow()
            db.session.commit()
            flash("Batch started.", "success")
        return redirect(url_for("production_detail", batch_id=batch.id))

    @app.route("/production/<int:batch_id>/complete", methods=["POST"])
    def production_complete(batch_id):
        batch = ProductionBatch.query.get_or_404(batch_id)
        if batch.status not in ("planned", "in_progress"):
            flash("Batch is not active.", "error")
            return redirect(url_for("production_detail", batch_id=batch.id))

        actual_quantity = parse_float(
            request.form.get("actual_quantity"), default=batch.planned_quantity
        )
        if actual_quantity <= 0:
            flash("Actual quantity must be positive.", "error")
            return redirect(url_for("production_detail", batch_id=batch.id))

        scale = actual_quantity / batch.recipe.output_quantity
        shortages = []
        for item in batch.recipe.items:
            needed = item.quantity * scale
            if item.raw_material.current_stock < needed:
                shortages.append(
                    f"{item.raw_material.name}: need {needed:g} {item.raw_material.unit}, "
                    f"have {item.raw_material.current_stock:g}"
                )
        if shortages:
            flash("Insufficient stock: " + "; ".join(shortages), "error")
            return redirect(url_for("production_detail", batch_id=batch.id))

        for item in batch.recipe.items:
            item.raw_material.current_stock -= item.quantity * scale
        batch.recipe.product.current_stock += actual_quantity
        batch.actual_quantity = actual_quantity
        batch.status = "completed"
        batch.end_date = datetime.utcnow()
        if not batch.start_date:
            batch.start_date = batch.end_date
        db.session.commit()
        flash("Batch completed; inventory updated.", "success")
        return redirect(url_for("production_detail", batch_id=batch.id))

    @app.route("/production/<int:batch_id>/cancel", methods=["POST"])
    def production_cancel(batch_id):
        batch = ProductionBatch.query.get_or_404(batch_id)
        if batch.status == "completed":
            flash("Completed batches cannot be cancelled.", "error")
        else:
            batch.status = "cancelled"
            db.session.commit()
            flash("Batch cancelled.", "success")
        return redirect(url_for("production_detail", batch_id=batch.id))

    @app.route("/production/<int:batch_id>/delete", methods=["POST"])
    def production_delete(batch_id):
        batch = ProductionBatch.query.get_or_404(batch_id)
        if batch.status == "completed":
            flash("Cannot delete a completed batch (inventory has moved).", "error")
            return redirect(url_for("production_detail", batch_id=batch.id))
        db.session.delete(batch)
        db.session.commit()
        flash("Batch deleted.", "success")
        return redirect(url_for("production_list"))

    # -----------------------------------------------------------------
    # Purchase orders
    # -----------------------------------------------------------------
    @app.route("/purchase-orders")
    def purchases_list():
        pos = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).all()
        return render_template("purchasing/list.html", pos=pos)

    @app.route("/purchase-orders/new", methods=["GET", "POST"])
    def purchases_new():
        suppliers = Supplier.query.order_by(Supplier.name).all()
        if request.method == "POST":
            po_number = request.form["po_number"].strip()
            supplier_id = request.form.get("supplier_id", type=int)
            order_date = parse_date(request.form.get("order_date")) or date.today()
            expected_date = parse_date(request.form.get("expected_date"))
            notes = request.form.get("notes", "").strip() or None
            if not po_number or not supplier_id:
                flash("PO number and supplier are required.", "error")
            elif PurchaseOrder.query.filter_by(po_number=po_number).first():
                flash("PO number already exists.", "error")
            else:
                po = PurchaseOrder(
                    po_number=po_number,
                    supplier_id=supplier_id,
                    order_date=order_date,
                    expected_date=expected_date,
                    notes=notes,
                    status="draft",
                )
                db.session.add(po)
                db.session.commit()
                flash("Purchase order created. Add line items below.", "success")
                return redirect(url_for("purchases_detail", po_id=po.id))
        return render_template("purchasing/form.html", suppliers=suppliers)

    @app.route("/purchase-orders/<int:po_id>", methods=["GET", "POST"])
    def purchases_detail(po_id):
        po = PurchaseOrder.query.get_or_404(po_id)
        if request.method == "POST" and po.status == "draft":
            po.supplier_id = request.form.get("supplier_id", type=int) or po.supplier_id
            po.order_date = parse_date(request.form.get("order_date")) or po.order_date
            po.expected_date = parse_date(request.form.get("expected_date"))
            po.notes = request.form.get("notes", "").strip() or None
            db.session.commit()
            flash("Purchase order updated.", "success")
            return redirect(url_for("purchases_detail", po_id=po.id))
        suppliers = Supplier.query.order_by(Supplier.name).all()
        materials = RawMaterial.query.order_by(RawMaterial.name).all()
        return render_template(
            "purchasing/detail.html", po=po, suppliers=suppliers, materials=materials
        )

    @app.route("/purchase-orders/<int:po_id>/items/add", methods=["POST"])
    def purchases_add_item(po_id):
        po = PurchaseOrder.query.get_or_404(po_id)
        if po.status != "draft":
            flash("Can only edit draft purchase orders.", "error")
            return redirect(url_for("purchases_detail", po_id=po.id))
        raw_material_id = request.form.get("raw_material_id", type=int)
        quantity = parse_float(request.form.get("quantity"))
        unit_cost = parse_float(request.form.get("unit_cost"))
        if not raw_material_id or quantity <= 0:
            flash("Select a raw material and positive quantity.", "error")
        else:
            db.session.add(
                PurchaseOrderItem(
                    po_id=po.id,
                    raw_material_id=raw_material_id,
                    quantity=quantity,
                    unit_cost=unit_cost,
                )
            )
            db.session.commit()
            flash("Line item added.", "success")
        return redirect(url_for("purchases_detail", po_id=po.id))

    @app.route("/purchase-orders/<int:po_id>/items/<int:item_id>/delete", methods=["POST"])
    def purchases_remove_item(po_id, item_id):
        item = PurchaseOrderItem.query.get_or_404(item_id)
        if item.po_id != po_id:
            abort(404)
        if item.po.status != "draft":
            flash("Can only edit draft purchase orders.", "error")
            return redirect(url_for("purchases_detail", po_id=po_id))
        db.session.delete(item)
        db.session.commit()
        flash("Line item removed.", "success")
        return redirect(url_for("purchases_detail", po_id=po_id))

    @app.route("/purchase-orders/<int:po_id>/place", methods=["POST"])
    def purchases_place(po_id):
        po = PurchaseOrder.query.get_or_404(po_id)
        if po.status != "draft":
            flash("Only draft POs can be placed.", "error")
        elif not po.items:
            flash("Add at least one line item before placing the order.", "error")
        else:
            po.status = "ordered"
            db.session.commit()
            flash("Purchase order placed.", "success")
        return redirect(url_for("purchases_detail", po_id=po.id))

    @app.route("/purchase-orders/<int:po_id>/receive", methods=["POST"])
    def purchases_receive(po_id):
        po = PurchaseOrder.query.get_or_404(po_id)
        if po.status != "ordered":
            flash("Only placed POs can be received.", "error")
        else:
            for item in po.items:
                item.raw_material.current_stock += item.quantity
            po.status = "received"
            po.received_date = date.today()
            db.session.commit()
            flash("Purchase order received; raw material stock updated.", "success")
        return redirect(url_for("purchases_detail", po_id=po.id))

    @app.route("/purchase-orders/<int:po_id>/cancel", methods=["POST"])
    def purchases_cancel(po_id):
        po = PurchaseOrder.query.get_or_404(po_id)
        if po.status == "received":
            flash("Received POs cannot be cancelled.", "error")
        else:
            po.status = "cancelled"
            db.session.commit()
            flash("Purchase order cancelled.", "success")
        return redirect(url_for("purchases_detail", po_id=po.id))

    @app.route("/purchase-orders/<int:po_id>/delete", methods=["POST"])
    def purchases_delete(po_id):
        po = PurchaseOrder.query.get_or_404(po_id)
        if po.status == "received":
            flash("Cannot delete a received PO.", "error")
            return redirect(url_for("purchases_detail", po_id=po.id))
        db.session.delete(po)
        db.session.commit()
        flash("Purchase order deleted.", "success")
        return redirect(url_for("purchases_list"))

    # -----------------------------------------------------------------
    # Sales orders
    # -----------------------------------------------------------------
    @app.route("/sales-orders")
    def sales_list():
        sos = SalesOrder.query.order_by(SalesOrder.created_at.desc()).all()
        return render_template("sales/list.html", sos=sos)

    @app.route("/sales-orders/new", methods=["GET", "POST"])
    def sales_new():
        customers = Customer.query.order_by(Customer.name).all()
        if request.method == "POST":
            so_number = request.form["so_number"].strip()
            customer_id = request.form.get("customer_id", type=int)
            order_date = parse_date(request.form.get("order_date")) or date.today()
            notes = request.form.get("notes", "").strip() or None
            if not so_number or not customer_id:
                flash("SO number and customer are required.", "error")
            elif SalesOrder.query.filter_by(so_number=so_number).first():
                flash("SO number already exists.", "error")
            else:
                so = SalesOrder(
                    so_number=so_number,
                    customer_id=customer_id,
                    order_date=order_date,
                    notes=notes,
                    status="draft",
                )
                db.session.add(so)
                db.session.commit()
                flash("Sales order created. Add line items below.", "success")
                return redirect(url_for("sales_detail", so_id=so.id))
        return render_template("sales/form.html", customers=customers)

    @app.route("/sales-orders/<int:so_id>", methods=["GET", "POST"])
    def sales_detail(so_id):
        so = SalesOrder.query.get_or_404(so_id)
        if request.method == "POST" and so.status == "draft":
            so.customer_id = request.form.get("customer_id", type=int) or so.customer_id
            so.order_date = parse_date(request.form.get("order_date")) or so.order_date
            so.notes = request.form.get("notes", "").strip() or None
            db.session.commit()
            flash("Sales order updated.", "success")
            return redirect(url_for("sales_detail", so_id=so.id))
        customers = Customer.query.order_by(Customer.name).all()
        products = FinishedProduct.query.order_by(FinishedProduct.name).all()
        return render_template(
            "sales/detail.html", so=so, customers=customers, products=products
        )

    @app.route("/sales-orders/<int:so_id>/items/add", methods=["POST"])
    def sales_add_item(so_id):
        so = SalesOrder.query.get_or_404(so_id)
        if so.status != "draft":
            flash("Can only edit draft sales orders.", "error")
            return redirect(url_for("sales_detail", so_id=so.id))
        product_id = request.form.get("finished_product_id", type=int)
        quantity = parse_float(request.form.get("quantity"))
        unit_price = parse_float(request.form.get("unit_price"))
        if not product_id or quantity <= 0:
            flash("Select a product and positive quantity.", "error")
        else:
            db.session.add(
                SalesOrderItem(
                    so_id=so.id,
                    finished_product_id=product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                )
            )
            db.session.commit()
            flash("Line item added.", "success")
        return redirect(url_for("sales_detail", so_id=so.id))

    @app.route("/sales-orders/<int:so_id>/items/<int:item_id>/delete", methods=["POST"])
    def sales_remove_item(so_id, item_id):
        item = SalesOrderItem.query.get_or_404(item_id)
        if item.so_id != so_id:
            abort(404)
        if item.so.status != "draft":
            flash("Can only edit draft sales orders.", "error")
            return redirect(url_for("sales_detail", so_id=so_id))
        db.session.delete(item)
        db.session.commit()
        flash("Line item removed.", "success")
        return redirect(url_for("sales_detail", so_id=so_id))

    @app.route("/sales-orders/<int:so_id>/confirm", methods=["POST"])
    def sales_confirm(so_id):
        so = SalesOrder.query.get_or_404(so_id)
        if so.status != "draft":
            flash("Only draft sales orders can be confirmed.", "error")
        elif not so.items:
            flash("Add at least one line item before confirming.", "error")
        else:
            so.status = "confirmed"
            db.session.commit()
            flash("Sales order confirmed.", "success")
        return redirect(url_for("sales_detail", so_id=so.id))

    @app.route("/sales-orders/<int:so_id>/ship", methods=["POST"])
    def sales_ship(so_id):
        so = SalesOrder.query.get_or_404(so_id)
        if so.status != "confirmed":
            flash("Only confirmed sales orders can be shipped.", "error")
            return redirect(url_for("sales_detail", so_id=so.id))
        shortages = []
        for item in so.items:
            if item.finished_product.current_stock < item.quantity:
                shortages.append(
                    f"{item.finished_product.name}: need {item.quantity:g} "
                    f"{item.finished_product.unit}, have {item.finished_product.current_stock:g}"
                )
        if shortages:
            flash("Insufficient finished stock: " + "; ".join(shortages), "error")
            return redirect(url_for("sales_detail", so_id=so.id))
        for item in so.items:
            item.finished_product.current_stock -= item.quantity
        so.status = "shipped"
        so.shipped_date = date.today()
        db.session.commit()
        flash("Sales order shipped; finished goods stock updated.", "success")
        return redirect(url_for("sales_detail", so_id=so.id))

    @app.route("/sales-orders/<int:so_id>/cancel", methods=["POST"])
    def sales_cancel(so_id):
        so = SalesOrder.query.get_or_404(so_id)
        if so.status == "shipped":
            flash("Shipped sales orders cannot be cancelled.", "error")
        else:
            so.status = "cancelled"
            db.session.commit()
            flash("Sales order cancelled.", "success")
        return redirect(url_for("sales_detail", so_id=so.id))

    @app.route("/sales-orders/<int:so_id>/delete", methods=["POST"])
    def sales_delete(so_id):
        so = SalesOrder.query.get_or_404(so_id)
        if so.status == "shipped":
            flash("Cannot delete a shipped sales order.", "error")
            return redirect(url_for("sales_detail", so_id=so.id))
        db.session.delete(so)
        db.session.commit()
        flash("Sales order deleted.", "success")
        return redirect(url_for("sales_list"))


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
