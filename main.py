import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Customer, Installer, Material, Order, OrderItem

app = FastAPI(title="Hantverkar Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hantverkar Dashboard Backend"}

@app.get("/schema")
def get_schema():
    # The viewer can use these for dynamic CRUD
    return {
        "collections": [
            "customer", "installer", "material", "order"
        ]
    }

# Utility to safely cast string id to ObjectId

def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Ogiltigt ID")

# ----------------------------- Customers -----------------------------
@app.post("/customers")
def create_customer(payload: Customer):
    inserted_id = create_document("customer", payload)
    return {"id": inserted_id}

@app.get("/customers")
def list_customers(q: Optional[str] = None):
    filter_q = {}
    if q:
        # Simple case-insensitive search on name or company
        filter_q = {
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"company": {"$regex": q, "$options": "i"}}
            ]
        }
    docs = get_documents("customer", filter_q)
    return [serialize(doc) for doc in docs]

# ----------------------------- Installers -----------------------------
@app.post("/installers")
def create_installer(payload: Installer):
    inserted_id = create_document("installer", payload)
    return {"id": inserted_id}

@app.get("/installers")
def list_installers(active: Optional[bool] = None):
    filter_q = {}
    if active is not None:
        filter_q["active"] = active
    docs = get_documents("installer", filter_q)
    return [serialize(doc) for doc in docs]

# ----------------------------- Materials -----------------------------
@app.post("/materials")
def create_material(payload: Material):
    inserted_id = create_document("material", payload)
    return {"id": inserted_id}

@app.get("/materials")
def list_materials(search: Optional[str] = None):
    filter_q = {}
    if search:
        filter_q = {"$or": [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}}
        ]}
    docs = get_documents("material", filter_q)
    return [serialize(doc) for doc in docs]

# ----------------------------- Orders -----------------------------
@app.post("/orders")
def create_order(payload: Order):
    # Compute totals if not supplied
    total = 0.0
    for item in payload.items:
        # When creating order, fetch material price if unit_price not provided
        if item.unit_price is None:
            mat = db["material"].find_one({"_id": oid(item.material_id)})
            if not mat:
                raise HTTPException(status_code=404, detail=f"Material saknas: {item.material_id}")
            item.unit_price = float(mat.get("price", 0))
        total += float(item.unit_price) * float(item.quantity)
    payload.total = round(total, 2)

    inserted_id = create_document("order", payload)
    return {"id": inserted_id, "total": payload.total}

@app.get("/orders")
def list_orders(status: Optional[str] = None, customer_id: Optional[str] = None):
    filter_q = {}
    if status:
        filter_q["status"] = status
    if customer_id:
        filter_q["customer_id"] = customer_id
    docs = get_documents("order", filter_q)
    # Enrich with customer and installer names
    enriched = []
    for doc in docs:
        cust = db["customer"].find_one({"_id": doc.get("customer_id") and oid(doc["customer_id"])}) if doc.get("customer_id") else None
        inst = db["installer"].find_one({"_id": doc.get("installer_id") and oid(doc["installer_id"])}) if doc.get("installer_id") else None
        doc_serial = serialize(doc)
        doc_serial["customer_name"] = cust.get("name") if cust else None
        doc_serial["installer_name"] = inst.get("name") if inst else None
        enriched.append(doc_serial)
    return enriched

# ----------------------------- Helpers -----------------------------

def serialize(doc: dict):
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    # Convert nested item material ids to strings
    if doc.get("items"):
        for item in doc["items"]:
            if isinstance(item.get("material_id"), ObjectId):
                item["material_id"] = str(item["material_id"])
    return doc


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
