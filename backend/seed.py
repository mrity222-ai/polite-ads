"""
Idempotent Database Seed Script for PolitiAds
Seeds Demo Candidate (usr_demo), Candidate Directory, Plans, and Settings.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal, init_db
from entities import (
    User, CandidateProfile, Campaign, Review, SubscriptionPlan, PlatformSetting
)
from security import hash_password

def seed_database():
    from config import APP_ENV
    if APP_ENV == "production":
        raise RuntimeError("Demo seeding is disabled in production. Use create_admin.py.")
    init_db()
    db = SessionLocal()
    try:
        # Administrators are created/reset privately through create_admin.py.

        # 2. Demo Candidate Account (usr_demo / Rajesh Kumar Sharma)
        demo_user = db.query(User).filter(User.id == "usr_demo").first()
        if not demo_user:
            demo_user = User(
                id="usr_demo",
                full_name="Rajesh Kumar Sharma",
                email="rajesh@campaign.in",
                mobile="9876543210",
                password_hash=hash_password("secret123"),
                role="candidate",
                status="active"
            )
            db.add(demo_user)
            db.flush()

            # Profile for Demo Candidate
            demo_profile = CandidateProfile(
                id="prof_demo",
                user_id="usr_demo",
                candidate_name="Rajesh Kumar Sharma",
                contesting_post="Ward Councillor / Corporator",
                gaon_ward="Rampur, Ward No. 12",
                area_block="Sadabad Block",
                pincode="281306",
                lat="27.4482",
                lng="78.0416",
                accuracy_m=25,
                symbol_name="Car",
                default_slogan="काम किया है, काम करेंगे - वार्ड 12 को नंबर 1 बनाएंगे!",
                disclaimer_text="चुनाव आयोग द्वारा प्रमाणित विज्ञापन। सौजन्य: राजेश शर्मा चुनाव प्रचार समिति",
                is_meta_connected=True,
                onboarding_completed=True
            )
            db.add(demo_profile)

            # Live Campaign (ad_101)
            ad_101 = Campaign(
                id="ad_101",
                owner_id="usr_demo",
                title="Sadabad Ward 12 Vikas Yatra",
                slogan="वार्ड 12 के सर्वांगीण विकास के लिए कर्मठ प्रत्याशी को वोट दें!",
                budget_paise=50000,  # ₹500
                radius_km=8.0,
                reach=16000,
                spent_paise=240000,  # ₹2400
                clicks=420,
                status="Live 🟢",
                badge="✨ PolitiAds Team Enhanced & Live",
                template_id=1,
                meta_ad_id="meta_ad_883921"
            )
            db.add(ad_101)

            # Pending Review Campaign (ad_102)
            ad_102 = Campaign(
                id="ad_102",
                owner_id="usr_demo",
                title="Youth Sports Ground Demand Rally",
                slogan="युवाओं के खेल मैदान और ओपन जिम के निर्माण हेतु भारी मतों से विजयी बनाएं।",
                budget_paise=80000,  # ₹800
                radius_km=10.0,
                reach=0,
                spent_paise=0,
                clicks=0,
                status="Under Company Review ⏳",
                badge="⏳ Experts Reviewing & Enhancing",
                template_id=2
            )
            db.add(ad_102)
            db.flush()

            # Review item for ad_102
            rev_102 = Review(
                id="rev_102",
                campaign_id="ad_102",
                original_slogan="युवाओं के खेल मैदान और ओपन जिम के निर्माण हेतु भारी मतों से विजयी बनाएं।",
                enhanced_slogan="वार्ड 12 के युवाओं का संकल्प: नया खेल मैदान और आधुनिक ओपन जिम। वोट करें कर्मठ साथी को!",
                status="Pending Admin Review 🟡"
            )
            db.add(rev_102)
            print("[SEED] Created Demo Candidate (usr_demo) with profile, campaigns, and review queue item")

        # 3. Candidate Directory Users (USR-102 to USR-118)
        raw_candidates = [
            {"id": "usr_102", "name": "Sanjay Yadav", "phone": "9812345678", "email": "sanjay@bithoor.in", "post": "Gram Pradhan Candidate", "ward": "Bithoor, Ward 3", "pincode": "209217", "status": "active", "symbol": "Tractor", "lat": "26.6139", "lng": "80.2743"},
            {"id": "usr_103", "name": "Priya Chaudhary", "phone": "9723456789", "email": "priya@noida.in", "post": "Nagar Palika President", "ward": "Sector 14, Ward 8", "pincode": "201301", "status": "active", "symbol": "Kite", "lat": "28.5355", "lng": "77.3910"},
            {"id": "usr_104", "name": "Amitabh Shukla", "phone": "9634567890", "email": "shukla@kanpur.in", "post": "Vidhan Sabha MLA Candidate", "ward": "Sadabad Assembly 07", "pincode": "281306", "status": "active", "symbol": "Cricket Bat", "lat": "27.4421", "lng": "78.0433"},
            {"id": "usr_105", "name": "Meena Devi", "phone": "9545678901", "email": "meena@patna.in", "post": "Gram Pradhan Candidate", "ward": "Phulwari Sharif Block", "pincode": "801505", "status": "pending", "symbol": "Cup & Saucer", "lat": "25.5788", "lng": "85.0833"},
            {"id": "usr_106", "name": "Harish Patel", "phone": "9456789012", "email": "harish@gujarat.in", "post": "Ward Councillor / Corporator", "ward": "Ghatlodia Ward 11", "pincode": "380061", "status": "active", "symbol": "Key", "lat": "23.0734", "lng": "72.5408"},
            {"id": "usr_107", "name": "Mohammad Rizwan", "phone": "9367890123", "email": "rizwan@lucknow.in", "post": "Nagar Nigam Corporator", "ward": "Old City Ward 22", "pincode": "226003", "status": "active", "symbol": "Lantern", "lat": "26.8467", "lng": "80.9462"},
            {"id": "usr_108", "name": "Kavita Rani", "phone": "9278901234", "email": "kavita@haryana.in", "post": "Zila Parishad Member", "ward": "Sonipat Ward 5", "pincode": "131001", "status": "active", "symbol": "Book", "lat": "28.9931", "lng": "77.0151"},
            {"id": "usr_109", "name": "Balwinder Singh", "phone": "9189012345", "email": "balwinder@punjab.in", "post": "Sarpanch Candidate", "ward": "Amritsar Rural", "pincode": "143001", "status": "suspended", "symbol": "Hand Pump", "lat": "31.6340", "lng": "74.8723"},
            {"id": "usr_110", "name": "Deepak Verma", "phone": "9090123456", "email": "verma@bhopal.in", "post": "Ward Councillor / Corporator", "ward": "Arera Colony Ward 4", "pincode": "462016", "status": "active", "symbol": "Clock", "lat": "23.2132", "lng": "77.4358"},
            {"id": "usr_111", "name": "Sunita Rawat", "phone": "9001234567", "email": "sunita@dehradun.in", "post": "Gram Pradhan Candidate", "ward": "Doiwala Block", "pincode": "248140", "status": "active", "symbol": "Flower Pot", "lat": "30.1742", "lng": "78.1189"},
            {"id": "usr_112", "name": "Mahesh Joshi", "phone": "9112345678", "email": "joshi@jaipur.in", "post": "Nagar Palika President", "ward": "Mansarovar Ward 9", "pincode": "302020", "status": "active", "symbol": "Kite", "lat": "26.8524", "lng": "75.7684"},
            {"id": "usr_113", "name": "Anita Soren", "phone": "9223456789", "email": "anita@ranchi.in", "post": "Mukhiya Candidate", "ward": "Kanke Ward 2", "pincode": "834006", "status": "active", "symbol": "Bow & Arrow", "lat": "23.4326", "lng": "85.3218"},
            {"id": "usr_114", "name": "Nitin Gadve", "phone": "9334567890", "email": "nitin@nagpur.in", "post": "Corporator Candidate", "ward": "Dharampeth Ward 15", "pincode": "440010", "status": "active", "symbol": "Torch", "lat": "21.1458", "lng": "79.0623"},
            {"id": "usr_115", "name": "Gita Banerjee", "phone": "9445678901", "email": "gita@kolkata.in", "post": "Councillor Candidate", "ward": "Bhowanipore Ward 70", "pincode": "700025", "status": "active", "symbol": "Fish", "lat": "22.5298", "lng": "88.3444"},
            {"id": "usr_116", "name": "Rameshwar Reddy", "phone": "9556789012", "email": "reddy@hyderabad.in", "post": "GHMC Corporator Candidate", "ward": "Kukatpally Ward 118", "pincode": "500072", "status": "active", "symbol": "Car", "lat": "17.4875", "lng": "78.3953"},
            {"id": "usr_117", "name": "Karthik Subramanian", "phone": "9667890123", "email": "karthik@chennai.in", "post": "Corporator Candidate", "ward": "Mylapore Ward 124", "pincode": "600004", "status": "active", "symbol": "Ceiling Fan", "lat": "13.0339", "lng": "80.2687"},
            {"id": "usr_118", "name": "Virendra Singh Rathore", "phone": "9778901234", "email": "rathore@rajasthan.in", "post": "Vidhan Sabha MLA Candidate", "ward": "Ajmer North Assembly", "pincode": "305001", "status": "active", "symbol": "Sword", "lat": "26.4499", "lng": "74.6399"}
        ]

        pwd_hash = hash_password("candidate123")
        created_cand_count = 0
        for c in raw_candidates:
            if not db.query(User).filter(User.id == c["id"]).first():
                u = User(
                    id=c["id"],
                    full_name=c["name"],
                    email=c["email"],
                    mobile=c["phone"],
                    password_hash=pwd_hash,
                    role="candidate",
                    status=c["status"]
                )
                db.add(u)
                db.flush()

                p = CandidateProfile(
                    id=f"prof_{c['id']}",
                    user_id=c["id"],
                    candidate_name=c["name"],
                    contesting_post=c["post"],
                    gaon_ward=c["ward"],
                    area_block=c["ward"].split(",")[0],
                    pincode=c["pincode"],
                    lat=c["lat"],
                    lng=c["lng"],
                    accuracy_m=25,
                    symbol_name=c["symbol"],
                    default_slogan=f"Vote for {c['name']}!",
                    disclaimer_text="ECI Compliant Campaign",
                    is_meta_connected=True,
                    onboarding_completed=True
                )
                db.add(p)
                created_cand_count += 1
        if created_cand_count > 0:
            print(f"[SEED] Seeded {created_cand_count} Candidate Directory accounts and profiles")

        # 4. Subscription Plans
        plans_data = [
            {
                "id": "plan_panchayat",
                "name": "Gram Panchayat Starter",
                "price_paise": 99900,  # ₹999
                "daily_ad_cap_paise": 50000,  # ₹500
                "badge": "Popular",
                "features": ["3km Geo-radius targeting", "Company Slogan Polish", "WhatsApp Lead Alerts", "ECI Compliance Check"]
            },
            {
                "id": "plan_ward",
                "name": "Ward Councillor Pro",
                "price_paise": 249900,  # ₹2,499
                "daily_ad_cap_paise": 150000,  # ₹1,500
                "badge": "Best Value",
                "features": ["8km Geo-radius targeting", "Meta Ad Library Opponent Spy", "Unlimited Ad Revisions", "24x7 Priority Support", "Voter WhatsApp Automation"]
            },
            {
                "id": "plan_mla",
                "name": "Vidhan Sabha MLA War-Room",
                "price_paise": 999900,  # ₹9,999
                "daily_ad_cap_paise": 1000000,  # ₹10,000
                "badge": "Elite",
                "features": ["Constituency Wide (40km)", "4-Tier Chess Counter-Attacks", "Dedicated Campaign Manager", "Ground Sentiment Reports", "Unlimited Meta Push"]
            }
        ]

        for p_data in plans_data:
            existing_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == p_data["id"]).first()
            if not existing_plan:
                sp = SubscriptionPlan(
                    id=p_data["id"],
                    name=p_data["name"],
                    price_paise=p_data["price_paise"],
                    daily_ad_cap_paise=p_data["daily_ad_cap_paise"],
                    badge=p_data["badge"],
                    features=p_data["features"],
                    is_active=True
                )
                db.add(sp)
                print(f"[SEED] Seeded Subscription Plan: {p_data['name']}")

        # 5. Platform Settings (e.g. Commission)
        comm = db.query(PlatformSetting).filter(PlatformSetting.key == "company_commission_pct").first()
        if not comm:
            comm = PlatformSetting(
                key="company_commission_pct",
                value="20.0"
            )
            db.add(comm)
            print("[SEED] Seeded Platform Setting: company_commission_pct = 20.0%")

        db.commit()
        print("[SUCCESS] Database seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
