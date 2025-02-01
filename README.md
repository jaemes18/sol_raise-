# Solana-Integrated Crowdfunding Backend

## 🌟 Overview  
This is the backend for a **crowdfunding platform** that integrates with **Solana** to **verify transactions and retrieve transaction amounts**. Built with **Django** and **PostgreSQL**, it ensures secure and reliable fundraising operations.  

Base API URL: http://127.0.0.1:8000/api/


## 🔧 Tech Stack  
- **Backend:** Django (Python)  
- **Database:** PostgreSQL  
- **Blockchain Integration:** Solana (for transaction verification)  

## 🛠 Features  
✅ **Transaction Verification** – Validate transactions made on Solana.  
✅ **Fetch Transaction Amounts** – Retrieve and display donation amounts.  
✅ **Campaign Management** – Backend logic to handle fundraising campaigns.  
✅ **Secure Database** – Store verified transaction records in **PostgreSQL**.  

## 🛂 Setup & Installation  

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/jaemes18/sol_raise-.git
   cd sol_raise-
   ```  
2. **Create & Activate Virtual Environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate  # Windows
   ```  
3. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```  
4. **Set Up Environment Variables**  
   - Configure **PostgreSQL** database settings in `settings.py`.  
   - Add **Solana RPC endpoint** for transaction verification.  

5. **Apply Migrations**  
   ```bash
   python manage.py migrate
   ```  
6. **Run the Server**  
   ```bash
   python manage.py runserver
   ```  

---

# 🔑 Authentication Endpoints  
### **Register** (`POST` → `/register/`)  
- Fields:  
  - `username` (unique)  
  - `email` (valid format)  
  - `password`  
  - `role` (`backer` or `creator`)  
  - `contact_address`  
  - `first_name`, `last_name`  
  - `national_id` (file upload)  

### **Login** (`POST` → `/login/`)  
- Options:  
  1. Username/Password  
     - `username`  
     - `password`  
  2. Wallet Address (Creators Only)  
     - `wallet_address`  

### **Token Refresh** (`POST` → `/token/refresh/`)  
- Requires a valid refresh token  

---

# 🏦 Project Endpoints  
### **List/Create Projects** (`GET`/`POST` → `/projects/`)  
- `GET`: List approved projects  
- `POST`: Create a project (Authenticated, one per user)  

### **Project Details** (`GET`/`PUT`/`PATCH`/`DELETE` → `/projects/<project_id>/`)  
- `GET`: Retrieve project details  
- `PUT`/`PATCH`: Update project (Creator only)  
- `DELETE`: Remove project (Creator only)  

---

# 🏅 Contribution Endpoints  
### **Verify Payment** (`POST` → `/verify_pay/`)  
- Fields:  
  - `transaction_hash` (Solana transaction)  
  - `project_id`  
  - `backer_id`  
- **Platform Fee**: 0.09% of contribution amount  

### **Contributions**  
- `GET` → `/contributions/<int:pk>/` → Get a contribution  
- `GET` → `/contributions/` → List all contributions  

---

# 👤 User Profile Endpoints  
### **Update Profile** (`PUT`/`PATCH` → `/update_profile/`)  
- Updatable Fields:  
  - `first_name`, `last_name`  
  - `contact_address`  
- **Restricted Fields**: Cannot update `wallet_address` or `national_id`  

---

# 📨 Messaging Endpoints  
### **Chat Reasons** (`GET`/`POST` → `/chat_reason/`)  
- `GET`: List reasons  
- `POST`: Create reason (Authenticated)  

### **Messages** (`GET`/`POST` → `/messages/`)  
- `GET`: List messages  
- `POST`: Send message (Authenticated)  

---

# 🔓 Authentication Requirements  
- Most endpoints require JWT authentication  
- Use `Authorization: Bearer <access_token>` in headers  
- Tokens are obtained from the login endpoint  

---

# 🚀 Roadmap  
🚀 **Expand Solana Integration** – Support more transaction details.  
📊 **Campaign Statistics** – Provide analytics on donations.  
🔗 **Frontend Development** – Build a user-friendly interface.  

---

# 👨‍💻 Developed By  
**Jaemes18** – Backend Developer  

