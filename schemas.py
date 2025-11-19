"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date

# Core domain schemas for the Hantverkar Dashboard

class Customer(BaseModel):
    name: str = Field(..., description="Fullständigt namn")
    email: Optional[EmailStr] = Field(None, description="E-postadress")
    phone: Optional[str] = Field(None, description="Telefonnummer")
    address: Optional[str] = Field(None, description="Adress")
    company: Optional[str] = Field(None, description="Företag (om företagskund)")
    notes: Optional[str] = Field(None, description="Anteckningar")

class Installer(BaseModel):
    name: str = Field(..., description="Montörens namn")
    email: Optional[EmailStr] = Field(None, description="E-postadress")
    phone: Optional[str] = Field(None, description="Telefonnummer")
    skills: Optional[List[str]] = Field(default_factory=list, description="Kompetenser")
    active: bool = Field(True, description="Aktiv montör")

class Material(BaseModel):
    sku: str = Field(..., description="Artikelnummer")
    name: str = Field(..., description="Materialnamn")
    unit: str = Field("st", description="Enhet (t.ex. st, m, kg)")
    price: float = Field(0, ge=0, description="Pris per enhet (SEK)")
    stock: int = Field(0, ge=0, description="Lagersaldo")
    supplier: Optional[str] = Field(None, description="Leverantör")

class OrderItem(BaseModel):
    material_id: str = Field(..., description="Referens till materialets ID")
    quantity: float = Field(..., gt=0, description="Beställd mängd")
    unit_price: Optional[float] = Field(None, ge=0, description="Pris per enhet vid order")

class Order(BaseModel):
    customer_id: str = Field(..., description="Kundens ID")
    installer_id: Optional[str] = Field(None, description="Montörens ID")
    items: List[OrderItem] = Field(default_factory=list, description="Orderrader")
    status: str = Field("ny", description="Status: ny, planerad, pågår, klar, fakturerad")
    scheduled_date: Optional[date] = Field(None, description="Planerat datum")
    total: Optional[float] = Field(None, ge=0, description="Totalt orderbelopp")
    notes: Optional[str] = Field(None, description="Anteckningar")

# Example schemas (kept for reference but not used by the app)
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
