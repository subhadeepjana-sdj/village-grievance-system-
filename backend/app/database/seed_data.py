import os
import datetime
import logging
from sqlalchemy.orm import Session
from app.database.session import SessionLocal, engine, Base
from app.models import (
    User, UserRole, Village, Department,
    Complaint, ComplaintStatus, ComplaintPriority, ComplaintStatusHistory,
    Document, AIQuery, AIResponse, Evidence, VerificationResult, ResearchMetric
)
from app.utils.security import get_password_hash
from app.services.document_parser import document_parser_service

logger = logging.getLogger("uvicorn.error")

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Create Village
        village = db.query(Village).filter(Village.name == "Gram Panchayat Chandanpur").first()
        if not village:
            village = Village(
                name="Gram Panchayat Chandanpur",
                district="South 24 Parganas",
                state="West Bengal",
                pincode="743368"
            )
            db.add(village)
            db.commit()
            db.refresh(village)
            logger.info("Seeded Gram Panchayat Chandanpur village.")

        # 2. Create Departments
        depts_data = [
            {"name": "Village Water Department", "description": "Handles drinking water supply, pipeline leaks, tube wells.", "contact": "+91 98765 11111"},
            {"name": "Roads & Infrastructure", "description": "Manages village roads, streetlights, drainage systems.", "contact": "+91 98765 22222"},
            {"name": "Sanitation & Waste Management", "description": "Manages waste collection, public toilets, cleanliness.", "contact": "+91 98765 33333"},
            {"name": "Electricity & Power", "description": "Manages transformer repairs, power cuts, village electrical lines.", "contact": "+91 98765 44444"},
            {"name": "Public Health & Schemes", "description": "Oversees health centers, housing schemes, welfare benefits.", "contact": "+91 98765 55555"}
        ]

        dept_objs = {}
        for d in depts_data:
            existing = db.query(Department).filter(Department.name == d["name"]).first()
            if not existing:
                existing = Department(name=d["name"], description=d["description"], contact_information=d["contact"])
                db.add(existing)
                db.commit()
                db.refresh(existing)
            dept_objs[d["name"]] = existing
        logger.info("Seeded village departments.")

        # 3. Create Users
        pass_hash = get_password_hash("Password123!")
        users_data = [
            {"name": "Rajesh Kumar", "email": "citizen@village.gov.in", "role": UserRole.CITIZEN, "phone": "+91 98000 00001", "dept": None},
            {"name": "Panchayat Staff Anjali", "email": "staff@village.gov.in", "role": UserRole.PANCHAYAT_STAFF, "phone": "+91 98000 00002", "dept": None},
            {"name": "Water Dept Officer Vikram", "email": "official@water.gov.in", "role": UserRole.DEPARTMENT_OFFICIAL, "phone": "+91 98000 00003", "dept": dept_objs["Village Water Department"].id},
            {"name": "System Administrator", "email": "admin@village.gov.in", "role": UserRole.ADMIN, "phone": "+91 98000 00004", "dept": None},
            {"name": "Dr. Sunita Sharma", "email": "researcher@village.gov.in", "role": UserRole.RESEARCHER, "phone": "+91 98000 00005", "dept": None}
        ]

        user_objs = {}
        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                existing = User(
                    name=u["name"],
                    email=u["email"],
                    password_hash=pass_hash,
                    role=u["role"],
                    phone=u["phone"],
                    village_id=village.id,
                    department_id=u["dept"]
                )
                db.add(existing)
                db.commit()
                db.refresh(existing)
            user_objs[u["email"]] = existing
        logger.info("Seeded default users (Citizen, Staff, Official, Admin, Researcher).")

        # 4. Seed Demo Complaints
        complaints_seed = [
            {
                "number": "GRV-2026-001024",
                "user": user_objs["citizen@village.gov.in"],
                "dept": dept_objs["Village Water Department"],
                "category": "Water Supply",
                "title": "Dirty Tap Water Supply in Ward 4",
                "description": "Drinking water coming from the main overhead pipeline in Ward 4 has high turbidity and brownish odor since yesterday morning.",
                "location": "Ward 4, Near Temple Lane",
                "status": ComplaintStatus.UNDER_REVIEW,
                "priority": ComplaintPriority.HIGH,
                "history": [
                    ("Submitted", "SUBMITTED", "Citizen Rajesh Kumar", "Grievance lodged on portal."),
                    ("SUBMITTED", "ACKNOWLEDGED", "Staff Anjali", "Grievance acknowledged by Gram Panchayat."),
                    ("ACKNOWLEDGED", "ASSIGNED", "Staff Anjali", "Assigned to Village Water Department."),
                    ("ASSIGNED", "UNDER_REVIEW", "Officer Vikram", "Inspection team dispatched to Ward 4 pipeline.")
                ]
            },
            {
                "number": "GRV-2026-001025",
                "user": user_objs["citizen@village.gov.in"],
                "dept": dept_objs["Roads & Infrastructure"],
                "category": "Roads",
                "title": "Broken Potholes near Village Main Market",
                "description": "Large potholes formed near the main market entrance after heavy rains, causing traffic congestion and scooter accidents.",
                "location": "Chandanpur Main Market Gate 2",
                "status": ComplaintStatus.IN_PROGRESS,
                "priority": ComplaintPriority.MEDIUM,
                "history": [
                    ("Submitted", "SUBMITTED", "Citizen Rajesh Kumar", "Grievance lodged."),
                    ("SUBMITTED", "ASSIGNED", "Staff Anjali", "Assigned to Roads & Infrastructure."),
                    ("ASSIGNED", "IN_PROGRESS", "Road Inspector", "Bitumen patching work ongoing.")
                ]
            },
            {
                "number": "GRV-2026-001026",
                "user": user_objs["citizen@village.gov.in"],
                "dept": dept_objs["Sanitation & Waste Management"],
                "category": "Sanitation",
                "title": "Garbage Overflow near Primary School",
                "description": "Waste bins near Primary School Ward 2 haven't been cleared for 3 days.",
                "location": "Primary School Ward 2",
                "status": ComplaintStatus.RESOLVED,
                "priority": ComplaintPriority.MEDIUM,
                "history": [
                    ("Submitted", "SUBMITTED", "Citizen Rajesh Kumar", "Grievance submitted."),
                    ("SUBMITTED", "RESOLVED", "Sanitation Supervisor", "Bin emptied and area disinfected.")
                ]
            }
        ]

        for cs in complaints_seed:
            c_existing = db.query(Complaint).filter(Complaint.complaint_number == cs["number"]).first()
            if not c_existing:
                c_existing = Complaint(
                    complaint_number=cs["number"],
                    user_id=cs["user"].id,
                    village_id=village.id,
                    department_id=cs["dept"].id,
                    category=cs["category"],
                    title=cs["title"],
                    description=cs["description"],
                    location=cs["location"],
                    status=cs["status"],
                    priority=cs["priority"]
                )
                db.add(c_existing)
                db.commit()
                db.refresh(c_existing)

                for h_old, h_new, h_by, h_rem in cs["history"]:
                    hist = ComplaintStatusHistory(
                        complaint_id=c_existing.id,
                        old_status=h_old,
                        new_status=h_new,
                        changed_by=h_by,
                        remarks=h_rem
                    )
                    db.add(hist)
                db.commit()

        logger.info("Seeded demo complaints and audit histories.")

        # 5. Seed Knowledge Base Documents (Text & PDF indexing)
        docs_seed = [
            {
                "title": "Gram Panchayat Water Supply Guidelines 2026",
                "dept": "Village Water Department",
                "category": "Water Supply",
                "content": (
                    "GRAM PANCHAYAT CHANDANPUR OFFICIAL WATER SUPPLY CITIZEN CHARTER 2026\n\n"
                    "1. Service Timings: Drinking water is supplied twice daily from 6:00 AM to 9:00 AM and 5:00 PM to 7:00 PM.\n"
                    "2. Complaint Resolution SLA: Drinking water contamination or supply breakdown complaints must be inspected within 24 hours and resolved within 48 hours by the Village Water Department.\n"
                    "3. Pipeline Leaks: Citizens can report major main-line leaks directly to Officer Vikram (+91 98765 11111).\n"
                    "4. Water Testing: Gram Panchayat conducts bi-weekly water quality testing at Ward 1, Ward 2, Ward 3, and Ward 4 public taps."
                )
            },
            {
                "title": "Gramin Housing Scheme Guidelines 2026",
                "dept": "Public Health & Schemes",
                "category": "Government Schemes",
                "content": (
                    "GRAMIN HOUSING SCHEME (PMAY-G) VILLAGE IMPLEMENTATION GUIDELINES 2026\n\n"
                    "1. Financial Assistance: Financial subsidy of Rs 1,20,000 is provided for plain areas and Rs 1,30,000 for hilly areas for pucca house construction.\n"
                    "2. Eligibility: Homeless households and families living in zero, one, or two-room kucha houses as per SECC 2011 data.\n"
                    "3. Application Procedure: Eligible citizens must register at the Gram Panchayat office with Aadhaar card, Job Card number, and bank account details.\n"
                    "4. Installments: Fund transfer is disbursed in 3 direct bank transfer installments linked to construction milestone geotagging."
                )
            },
            {
                "title": "Village Sanitation and Garbage Collection Charter",
                "dept": "Sanitation & Waste Management",
                "category": "Sanitation",
                "content": (
                    "GRAM PANCHAYAT CHANDANPUR SANITATION & WASTE MANAGEMENT RULES\n\n"
                    "1. Waste Collection Schedule: Door-to-door waste collection operates daily between 7:00 AM and 10:00 AM in all wards.\n"
                    "2. Segregation: Citizens must separate wet organic waste (green bin) from dry recyclable waste (blue bin).\n"
                    "3. Overflow Bins SLA: Complaints regarding overflowing public waste bins will be attended to within 12 hours of lodging."
                )
            }
        ]

        from app.config import settings
        data_dir = os.path.join(settings.UPLOAD_DIR, "documents")
        os.makedirs(data_dir, exist_ok=True)

        for ds in docs_seed:
            existing_doc = db.query(Document).filter(Document.title == ds["title"]).first()
            if not existing_doc:
                file_name = ds["title"].lower().replace(" ", "_") + ".txt"
                file_path = os.path.join(data_dir, file_name)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(ds["content"])

                rel_path = f"uploads/documents/{file_name}"
                doc = Document(
                    title=ds["title"],
                    file_path=rel_path,
                    document_type="TXT",
                    source="Gram Panchayat Secretariat",
                    department=ds["dept"],
                    village="Gram Panchayat Chandanpur",
                    version="1.0",
                    uploaded_by="System Seeder"
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)

                # Index into Qdrant
                document_parser_service.process_and_index_document(
                    file_path=file_path,
                    document_id=doc.id,
                    title=ds["title"],
                    department=ds["dept"],
                    village="Gram Panchayat Chandanpur",
                    source="Gram Panchayat Secretariat",
                    category=ds["category"],
                    version="1.0"
                )

        logger.info("Database seeding completed successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
