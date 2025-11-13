#!/usr/bin/env python3
"""
Data Seeding Script for Sexto Andar API
Creates fictional users, properties, visits, and proposals
Can be run locally or inside Docker container
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import random
from typing import Optional, Dict, List

# Configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://sexto-andar-auth:8001")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# Color codes for terminal output
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'


class DataSeeder:
    """Handles data seeding for the application"""
    
    def __init__(self):
        self.auth_url = AUTH_SERVICE_URL
        self.api_url = API_BASE_URL
        self.created_users = []
        self.created_properties = []
        self.tokens = {}
        
    def log(self, message: str, color: str = RESET):
        """Print colored log message"""
        print(f"{color}{message}{RESET}")
    
    def log_success(self, message: str):
        """Print success message"""
        self.log(f"✅ {message}", GREEN)
    
    def log_error(self, message: str):
        """Print error message"""
        self.log(f"❌ {message}", RED)
    
    def log_info(self, message: str):
        """Print info message"""
        self.log(f"ℹ️  {message}", BLUE)
    
    def log_warning(self, message: str):
        """Print warning message"""
        self.log(f"⚠️  {message}", YELLOW)
    
    def create_user_in_auth(self, username: str, email: str, password: str, full_name: str, phone: str, role: str = "USER") -> Optional[Dict]:
        """Create a user in the auth service"""
        try:
            # Different endpoints for different roles
            if role == "PROPERTY_OWNER":
                url = f"{self.auth_url}/auth/register/property-owner"
            else:
                url = f"{self.auth_url}/auth/register/user"
            
            data = {
                "username": username,
                "fullName": full_name,
                "email": email,
                "phoneNumber": phone,
                "password": password
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 201:
                user_data = response.json()
                self.log_success(f"Created {role}: {full_name} ({username})")
                return user_data
            elif response.status_code == 400 and "already exists" in response.text.lower():
                self.log_warning(f"User already exists: {username}")
                return {"username": username, "email": email, "fullName": full_name, "role": role}
            else:
                self.log_error(f"Failed to create user {username}: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            self.log_error(f"Cannot connect to auth service at {self.auth_url}")
            self.log_info("Make sure the auth service is running")
            return None
        except Exception as e:
            self.log_error(f"Error creating user: {str(e)}")
            return None
    
    def login(self, username: str, password: str) -> Optional[str]:
        """Login and get JWT token"""
        try:
            url = f"{self.auth_url}/auth/login"
            data = {
                "username": username,
                "password": password
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                token_data = response.json()
                token = token_data.get("access_token")
                self.tokens[username] = token
                self.log_success(f"Logged in: {username}")
                return token
            else:
                self.log_error(f"Failed to login {username}: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_error(f"Error logging in: {str(e)}")
            return None
    
    def create_property(self, token: str, property_type: str, data: Dict) -> Optional[Dict]:
        """Create a property (house or apartment)"""
        try:
            endpoint = "houses" if property_type == "house" else "apartments"
            url = f"{self.api_url}/properties/{endpoint}"
            cookies = {"access_token": token}
            
            response = requests.post(url, json=data, cookies=cookies)
            
            if response.status_code == 201:
                property_data = response.json()
                self.log_success(f"Created {property_type}: {data['description'][:50]}...")
                return property_data
            else:
                self.log_error(f"Failed to create property: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_error(f"Error creating property: {str(e)}")
            return None
    
    def create_visit(self, token: str, property_id: str, visit_date: str, notes: str = None) -> Optional[Dict]:
        """Create a visit"""
        try:
            url = f"{self.api_url}/visits/"
            cookies = {"access_token": token}
            data = {
                "idProperty": property_id,
                "visitDate": visit_date,
                "notes": notes
            }
            
            response = requests.post(url, json=data, cookies=cookies)
            
            if response.status_code == 201:
                visit_data = response.json()
                self.log_success(f"Created visit for property {property_id[:8]}... on {visit_date}")
                return visit_data
            else:
                self.log_error(f"Failed to create visit: {response.status_code} - {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log_error(f"Error creating visit: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_proposal(self, token: str, property_id: str, value: float, message: str = None) -> Optional[Dict]:
        """Create a proposal"""
        try:
            url = f"{self.api_url}/proposals/"
            cookies = {"access_token": token}
            data = {
                "idProperty": property_id,
                "proposalValue": value,
                "message": message
            }
            
            response = requests.post(url, json=data, cookies=cookies)
            
            if response.status_code == 201:
                proposal_data = response.json()
                self.log_success(f"Created proposal for property {property_id[:8]}... - ${value:,.2f}")
                return proposal_data
            else:
                self.log_error(f"Failed to create proposal: {response.status_code} - {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log_error(f"Error creating proposal: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def seed_users(self) -> bool:
        """Create fictional users and property owners"""
        self.log(f"\n{BOLD}{'='*80}{RESET}")
        self.log(f"{BOLD}STEP 1: Creating Users in Auth Service{RESET}")
        self.log(f"{BOLD}{'='*80}{RESET}\n")
        
        # Property Owners (username, email, password, full_name, phone, role)
        owners = [
            ("johndoe", "john.doe@email.com", "senha123", "John Doe", "+5511999990001", "PROPERTY_OWNER"),
            ("mariasilva", "maria.silva@email.com", "senha123", "Maria Silva", "+5521999990002", "PROPERTY_OWNER"),
            ("carlossantos", "carlos.santos@email.com", "senha123", "Carlos Santos", "+5531999990003", "PROPERTY_OWNER"),
        ]
        
        # Regular Users (username, email, password, full_name, phone, role)
        users = [
            ("alicejohnson", "alice.johnson@email.com", "senha123", "Alice Johnson", "+5511999990004", "USER"),
            ("bobsmith", "bob.smith@email.com", "senha123", "Bob Smith", "+5521999990005", "USER"),
            ("carolwhite", "carol.white@email.com", "senha123", "Carol White", "+5531999990006", "USER"),
            ("davidbrown", "david.brown@email.com", "senha123", "David Brown", "+5541999990007", "USER"),
        ]
        
        all_users = owners + users
        success_count = 0
        
        for username, email, password, full_name, phone, role in all_users:
            user = self.create_user_in_auth(username, email, password, full_name, phone, role)
            if user:
                self.created_users.append({
                    "username": username,
                    "email": email,
                    "password": password,
                    "fullName": full_name,
                    "phoneNumber": phone,
                    "role": role
                })
                success_count += 1
        
        self.log_info(f"\nCreated/verified {success_count}/{len(all_users)} users")
        return success_count > 0
    
    def seed_properties(self) -> bool:
        """Create fictional properties"""
        self.log(f"\n{BOLD}{'='*80}{RESET}")
        self.log(f"{BOLD}STEP 2: Creating Properties{RESET}")
        self.log(f"{BOLD}{'='*80}{RESET}\n")
        
        # Login property owners
        owners = [u for u in self.created_users if u["role"] == "PROPERTY_OWNER"]
        
        if not owners:
            self.log_error("No property owners found")
            return False
        
        for owner in owners:
            token = self.login(owner["username"], owner["password"])
            if not token:
                continue
            
            owner["token"] = token
        
        # Property data
        houses = [
            {
                "address": {
                    "street": "Main Street",
                    "number": "123",
                    "city": "São Paulo",
                    "postal_code": "01234-567",
                    "country": "Brazil"
                },
                "propertySize": 250.5,
                "description": "Beautiful 3-bedroom house with large backyard and garage",
                "propertyValue": 450000.00,
                "salesType": "sale",
                "landPrice": 200000.00,
                "isSingleHouse": True
            },
            {
                "address": {
                    "street": "Oak Avenue",
                    "number": "456",
                    "city": "Rio de Janeiro",
                    "postal_code": "20000-000",
                    "country": "Brazil"
                },
                "propertySize": 180.0,
                "description": "Cozy 2-bedroom house near the beach, perfect for families",
                "propertyValue": 2500.00,
                "salesType": "rent",
                "landPrice": 150000.00,
                "isSingleHouse": False
            }
        ]
        
        apartments = [
            {
                "address": {
                    "street": "Paulista Avenue",
                    "number": "1000",
                    "city": "São Paulo",
                    "postal_code": "01310-100",
                    "country": "Brazil"
                },
                "propertySize": 85.5,
                "description": "Modern 2-bedroom apartment in downtown with amazing city view",
                "propertyValue": 3500.00,
                "salesType": "rent",
                "condominiumFee": 800.00,
                "commonArea": True,
                "floor": 15,
                "isPetAllowed": True
            },
            {
                "address": {
                    "street": "Atlantic Avenue",
                    "number": "2000",
                    "city": "Rio de Janeiro",
                    "postal_code": "22000-000",
                    "country": "Brazil"
                },
                "propertySize": 120.0,
                "description": "Luxury 3-bedroom apartment with ocean view and pool",
                "propertyValue": 650000.00,
                "salesType": "sale",
                "condominiumFee": 1200.00,
                "commonArea": True,
                "floor": 20,
                "isPetAllowed": False
            },
            {
                "address": {
                    "street": "Central Park",
                    "number": "500",
                    "city": "Belo Horizonte",
                    "postal_code": "30000-000",
                    "country": "Brazil"
                },
                "propertySize": 65.0,
                "description": "Compact studio apartment perfect for students or singles",
                "propertyValue": 1800.00,
                "salesType": "rent",
                "condominiumFee": 400.00,
                "commonArea": False,
                "floor": 5,
                "isPetAllowed": True
            }
        ]
        
        # Create properties
        for i, house in enumerate(houses):
            owner = owners[i % len(owners)]
            if "token" in owner:
                property_data = self.create_property(owner["token"], "house", house)
                if property_data:
                    self.created_properties.append(property_data)
        
        for i, apartment in enumerate(apartments):
            owner = owners[i % len(owners)]
            if "token" in owner:
                property_data = self.create_property(owner["token"], "apartment", apartment)
                if property_data:
                    self.created_properties.append(property_data)
        
        self.log_info(f"\nCreated {len(self.created_properties)} properties")
        return len(self.created_properties) > 0
    
    def seed_visits(self) -> bool:
        """Create fictional visits"""
        self.log(f"\n{BOLD}{'='*80}{RESET}")
        self.log(f"{BOLD}STEP 3: Creating Visits{RESET}")
        self.log(f"{BOLD}{'='*80}{RESET}\n")
        
        if not self.created_properties:
            self.log_error("No properties available for visits")
            return False
        
        # Login regular users
        users = [u for u in self.created_users if u["role"] == "USER"]
        
        if not users:
            self.log_error("No regular users found")
            return False
        
        for user in users:
            token = self.login(user["username"], user["password"])
            if token:
                user["token"] = token
        
        # Create visits
        visit_notes = [
            "Very interested in this property!",
            "Looking for a place to move next month",
            "Would like to see the kitchen and bedrooms",
            "Interested in the neighborhood and surroundings",
            "Planning to visit with my family",
        ]
        
        created_visits = 0
        base_date = datetime.now() + timedelta(days=1)
        
        for i, property_data in enumerate(self.created_properties):
            # Create 1-3 visits per property
            num_visits = random.randint(1, min(3, len(users)))
            selected_users = random.sample([u for u in users if "token" in u], num_visits)
            
            for j, user in enumerate(selected_users):
                visit_date = (base_date + timedelta(days=i*2 + j)).isoformat()
                notes = random.choice(visit_notes)
                
                visit = self.create_visit(
                    user["token"],
                    property_data["id"],
                    visit_date,
                    notes
                )
                
                if visit:
                    created_visits += 1
        
        self.log_info(f"\nCreated {created_visits} visits")
        return created_visits > 0
    
    def seed_proposals(self) -> bool:
        """Create fictional proposals"""
        self.log(f"\n{BOLD}{'='*80}{RESET}")
        self.log(f"{BOLD}STEP 4: Creating Proposals{RESET}")
        self.log(f"{BOLD}{'='*80}{RESET}\n")
        
        if not self.created_properties:
            self.log_error("No properties available for proposals")
            return False
        
        # Get regular users with tokens
        users = [u for u in self.created_users if u["role"] == "USER" and "token" in u]
        
        if not users:
            self.log_error("No regular users with tokens found")
            return False
        
        # Create proposals
        proposal_messages = [
            "I'm very interested in this property. Is this price negotiable?",
            "This is my dream home! Can we discuss payment terms?",
            "I'd like to make an offer. Looking forward to your response.",
            "Great property! I'm ready to close the deal quickly.",
            "Interested buyer here. Please consider my offer.",
        ]
        
        created_proposals = 0
        
        for i, property_data in enumerate(self.created_properties):
            # Create 1-2 proposals per property
            num_proposals = random.randint(1, min(2, len(users)))
            selected_users = random.sample(users, num_proposals)
            
            for user in selected_users:
                original_value = float(property_data["propertyValue"])
                # Propose 90-110% of original value
                proposal_value = original_value * random.uniform(0.90, 1.10)
                message = random.choice(proposal_messages)
                
                proposal = self.create_proposal(
                    user["token"],
                    property_data["id"],
                    proposal_value,
                    message
                )
                
                if proposal:
                    created_proposals += 1
        
        self.log_info(f"\nCreated {created_proposals} proposals")
        return created_proposals > 0
    
    def run(self):
        """Run the complete seeding process"""
        self.log(f"\n{BOLD}{GREEN}{'='*80}{RESET}")
        self.log(f"{BOLD}{GREEN}Sexto Andar API - Data Seeding Script{RESET}")
        self.log(f"{BOLD}{GREEN}{'='*80}{RESET}\n")
        
        self.log_info(f"Auth Service: {self.auth_url}")
        self.log_info(f"API Service: {self.api_url}\n")
        
        # Run seeding steps
        if not self.seed_users():
            self.log_error("Failed to seed users. Aborting.")
            return False
        
        if not self.seed_properties():
            self.log_error("Failed to seed properties. Aborting.")
            return False
        
        if not self.seed_visits():
            self.log_warning("Failed to seed visits (continuing...)")
        
        if not self.seed_proposals():
            self.log_warning("Failed to seed proposals (continuing...)")
        
        # Summary
        self.log(f"\n{BOLD}{GREEN}{'='*80}{RESET}")
        self.log(f"{BOLD}{GREEN}SEEDING COMPLETED SUCCESSFULLY!{RESET}")
        self.log(f"{BOLD}{GREEN}{'='*80}{RESET}\n")
        
        self.log_info("📊 Summary:")
        self.log_info(f"   Users created: {len(self.created_users)}")
        self.log_info(f"   Properties created: {len(self.created_properties)}")
        
        self.log(f"\n{BOLD}🔑 Test Credentials (username / senha123):{RESET}")
        self.log("   Property Owners:")
        for user in self.created_users:
            if user["role"] == "PROPERTY_OWNER":
                self.log(f"      • {user['username']} ({user['email']})")
        
        self.log("\n   Regular Users:")
        for user in self.created_users:
            if user["role"] == "USER":
                self.log(f"      • {user['username']} ({user['email']})")
        
        self.log(f"\n{BOLD}📚 Documentation:{RESET}")
        self.log(f"   API Docs: {self.api_url.replace('/api', '/api/docs')}")
        self.log(f"   Auth Docs: {self.auth_url}/docs\n")
        
        return True


def main():
    """Main entry point"""
    seeder = DataSeeder()
    
    try:
        success = seeder.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        seeder.log_warning("\n\nSeeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        seeder.log_error(f"\n\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
