# ERP System

A lightweight, Flask-based Enterprise Resource Planning (ERP) application for managing inventory, production, purchasing, and sales. This system helps you track raw materials, finished products, production recipes, and business transactions with suppliers and customers.

## Features

- **Dashboard**: Overview of key metrics, low stock alerts, and recent activities.
- **Inventory Management**:
  - Track **Raw Materials** and **Finished Products**.
  - Monitor stock levels and reorder limits.
- **Production Management**:
  - Create **Recipes** mapping finished products to required raw materials.
  - Manage **Production Batches** (planning, starting, completing, or cancelling).
  - Automatically deduct raw materials and increase finished goods upon completion.
- **Purchasing**:
  - Manage **Suppliers**.
  - Create and track **Purchase Orders** (draft, ordered, received).
  - Automatically update raw material inventory upon receipt.
- **Sales**:
  - Manage **Customers**.
  - Create and track **Sales Orders** (draft, confirmed, shipped).
  - Automatically update finished product inventory upon shipment.

## Requirements

- Python 3.8+
- Flask (`Flask==3.0.3`)
- Flask-SQLAlchemy (`Flask-SQLAlchemy==3.1.1`)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Initialize and run the application:**
   ```bash
   python app.py
   ```
   The application will automatically create an SQLite database (`erp.db`) on startup.

2. **Access the application:**
   Open your web browser and navigate to `http://127.0.0.1:5000`.

## Project Structure

- `app.py`: The main Flask application containing routing and business logic.
- `models.py`: SQLAlchemy database models.
- `requirements.txt`: Python package dependencies.
- `templates/`: HTML templates for the application UI.
- `static/`: Static assets (CSS, JS, images, etc.).
