import os
import sys
# Add backend root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from sqlmodel import Session
from src.acuifero_vigia.db.database import init_db, edge_engine, central_engine
from src.acuifero_vigia.models.domain import Site, SiteCalibration

def seed():
    print("Initializing databases...")
    init_db()
    
    with Session(edge_engine) as session:
        # Check if sites exist
        existing = session.query(Site).first()
        if not existing:
            print("Seeding sites...")
            site1 = Site(
                id="puente-arroyo-01",
                name="Puente Arroyo 01",
                region="Litoral Sur",
                lat=-32.9468,
                lng=-60.6393,
                description="Puente principal en ruta provincial",
                is_active=True
            )
            site2 = Site(
                id="calle-baja-02",
                name="Calle Baja 02",
                region="Litoral Norte",
                lat=-32.9568,
                lng=-60.6493,
                description="Vado inundable frecuente",
                is_active=True
            )
            session.add(site1)
            session.add(site2)
            
            print("Seeding calibration...")
            cal1 = SiteCalibration(
                site_id="puente-arroyo-01",
                roi_polygon="[[10, 10], [200, 10], [200, 200], [10, 200]]",
                critical_line="[[10, 150], [200, 150]]",
                reference_line="[[10, 180], [200, 180]]"
            )
            session.add(cal1)
            session.commit()
            print("Seeding complete.")
        else:
            print("Data already seeded.")

if __name__ == "__main__":
    seed()
