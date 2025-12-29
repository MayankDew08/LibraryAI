import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi.testclient import TestClient
from app.main import app
import time

client = TestClient(app)

def test_student_registration_success():
    email = f"student{int(time.time())}@example.com"
    otp_response= client.post(
        "/otp/generate",
        json={"identifier": email} 
    )
    assert otp_response.status_code in [200, 202]
    otp_code = otp_response.json().get("otp")  
    registration_data = {
        "name": "Test Student",
        "email": email,
        "password": "securepassword",
        "otp": otp_code
    }
    response = client.post(
        "/auth/student/register",
        json=registration_data
    )
    assert response.status_code == 201
    assert response.json().get("message") == "User registered successfully"

def test_student_registration_invalid_otp():
    email = f"student{int(time.time())}@example.com"
    otp_response= client.post(
        "/otp/generate",
        json={"identifier": email} 
    )
    assert otp_response.status_code in [200, 202]
    registration_data = {
        "name": "Test Student",
        "email": email,
        "password": "securepassword",
        "otp": "000000"  
    }
    response = client.post(
        "/auth/student/register",
        json=registration_data
    )
    assert response.status_code == 401
    assert response.json().get("detail") == "Invalid OTP. 2 attempts remaining."
    
def test_student_registratioin_expired_otp():
    email = f"student{int(time.time())}@example.com"
    otp_response= client.post(
        "/otp/generate",
        json={"identifier": email} 
    )
    assert otp_response.status_code in [200, 202]
    otp_code = otp_response.json().get("otp")  
    time.sleep(6 * 60)  
    registration_data = {
        "name": "Test Student",
        "email": email,
        "password": "securepassword",
        "otp": otp_code
    }
    response = client.post(
        "/auth/student/register",
        json=registration_data
    )
    assert response.status_code == 401
    assert response.json().get("detail") == "OTP has expired. Please request a new OTP."
    

def test_student_login_success():
    email = f"student{int(time.time())}@example.com"
    otp_response= client.post(
        "/otp/generate",
        json={"identifier": email} 
    )
    assert otp_response.status_code in [200, 202]
    otp_code = otp_response.json().get("otp")  
    registration_data = {
        "name": "Test Student",
        "email": email,
        "password": "securepassword",
        "otp": otp_code
    }
    reg_response = client.post(
        "/auth/student/register",
        json=registration_data
    )
    assert reg_response.status_code == 201
    # Generate new OTP for login
    otp_response2 = client.post(
        "/otp/generate",
        json={"identifier": email} 
    )
    assert otp_response2.status_code in [200, 202]
    otp_code2 = otp_response2.json().get("otp")
    login_data = {
        "email": email,
        "password": "securepassword",
        "otp": otp_code2
    }
    response = client.post(
        "/auth/student/login",
        json=login_data
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    
def test_student_login_fail():
    email = f"student{int(time.time())}@example.com"
    otp_response= client.post(
        "/otp/generate",
        json={"identifier": email} 
    )
    assert otp_response.status_code in [200, 202]
    otp_code = otp_response.json().get("otp")
    login_data = {
        "email": email,
        "password": "wrongpassword",
        "otp": otp_code
    }
    response = client.post(
        "/auth/student/login",
        json=login_data
    )
    assert response.status_code == 401
    assert response.json().get("detail") == "Invalid email or password"

def test_admin_registration_success():
    email = f"admin{int(time.time())}@example.com"
    otp_response= client.post(
        "/otp/generate",
        json={"identifier": email} 
    )
    assert otp_response.status_code in [200, 202]
    otp_code = otp_response.json().get("otp")  
    registration_data = {
        "name": "Test Admin",
        "email": email,
        "password": "Admin@123",
        "otp": otp_code
    }
    response = client.post(
        "/auth/admin/register",
        json=registration_data
    )
    assert response.status_code == 201
    assert response.json().get("message") == "Admin registered successfully"
    
def test_admin_registration_invalid_password():
    email = f"admin{int(time.time())}@example.com"
    otp_response= client.post(
        "/otp/generate",
        json={"identifier": email} 
    )
    assert otp_response.status_code in [200, 202]
    otp_code = otp_response.json().get("otp")  
    registration_data = {
        "name": "Test Admin",
        "email": email,
        "password": "123",  
        "otp": otp_code
    }
    response = client.post(
        "/auth/admin/register",
        json=registration_data
    )
    assert response.status_code == 422
    assert response.json().get("detail")[0].get("msg") == "Value error, Invalid admin password"