# app/models/address.py
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from app.database.connection import BaseModel
import uuid
import re


class Address(BaseModel):
    """
    Address class - Property addresses
    """

    __tablename__ = "addresses"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )

    street = Column(String(200), nullable=False)

    number = Column(String(20), nullable=False)

    city = Column(String(100), nullable=False)

    postal_code = Column(String(20), nullable=False)

    country = Column(String(100), nullable=False, default="Brazil")

    # 1:1 relationship with Property
    property = relationship("Property", uselist=False)

    # Validations
    @validates("street")
    def validate_street(self, key, street):
        if not street or not street.strip():
            raise ValueError("Street is required")
        return street.strip()

    @validates("number")
    def validate_number(self, key, number):
        if not number or not number.strip():
            raise ValueError("Number is required")
        return number.strip()

    @validates("city")
    def validate_city(self, key, city):
        if not city or not city.strip():
            raise ValueError("City is required")
        return city.strip()

    @validates("postal_code")
    def validate_postal_code(self, key, postal_code):
        if not postal_code:
            raise ValueError("Postal code is required")

        # Remove non-numeric characters
        clean_cep = re.sub(r"\D", "", postal_code)
        if len(clean_cep) != 8:
            raise ValueError("Postal code must have 8 digits")

        return postal_code

    def get_formatted_address(self) -> str:
        """Returns formatted address"""
        return f"{self.street}, {self.number} - {self.city}, {self.postal_code} - {self.country}"

    def __repr__(self):
        return f"<Address(id={self.id}, street='{self.street}', city='{self.city}')>"

    def __str__(self):
        return self.get_formatted_address()
