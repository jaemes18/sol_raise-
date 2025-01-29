# Got it! Here's a refined README that focuses on verifying transactions and fetching transaction amounts from Solana.  

---

# Solana-Integrated Crowdfunding Backend  

## 🌟 Overview  
This is the backend for a **crowdfunding platform** that integrates with **Solana** to **verify transactions and retrieve transaction amounts**. Built with **Django** and **PostgreSQL**, it ensures secure and reliable fundraising operations.  

## 🔧 Tech Stack  
- **Backend:** Django (Python)  
- **Database:** PostgreSQL  
- **Blockchain Integration:** Solana (for transaction verification)  

## 🛠 Features  
✅ **Transaction Verification** – Validate transactions made on Solana.  
✅ **Fetch Transaction Amounts** – Retrieve and display donation amounts.  
✅ **Campaign Management** – Backend logic to handle fundraising campaigns.  
✅ **Secure Database** – Store verified transaction records in **PostgreSQL**.  

## 📦 Setup & Installation  

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

## 🔮 Roadmap  
🚀 **Expand Solana Integration** – Support more transaction details.  
📊 **Campaign Statistics** – Provide analytics on donations.  
🔗 **Frontend Development** – Build a user-friendly interface.  

## 👨‍💻 Developed By  
**Jaemes18** – Backend Developer  

---

