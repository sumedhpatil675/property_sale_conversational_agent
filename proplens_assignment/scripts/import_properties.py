import os
import sys
import pandas as pd
from decimal import Decimal
import django
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from agent.models import Property

def clean_price(value):
    if pd.isna(value):
        return None
    try:
        # Remove chars like $ or ,
        s = str(value).replace('$', '').replace(',', '').strip()
        return Decimal(s)
    except:
        return None

def run():
    # Hardcoded absolute path for safety in this environment
    csv_path = "/Users/roundcircle/assignment/updated_assignment_instructions/Property sales agent - Challenge.csv"
    
    if not os.path.exists(csv_path):
        print(f"CSV not found at {csv_path}")
        return

    print(f"Reading properties from: {csv_path}")
    
    try:
        # Load CSV
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Clear existing
    Property.objects.all().delete()
    print("Cleared existing properties.")

    count = 0
    for _, row in df.iterrows():
        try:
            if pd.isna(row.get('Project name')):
                continue

            # Handle bedrooms safely (float -> int)
            raw_beds = row.get('No of bedrooms')
            beds = None
            if pd.notna(raw_beds):
                try:
                    beds = int(float(raw_beds))
                except:
                    pass
            
            # Handle bathrooms
            raw_baths = row.get('bathrooms')
            baths = None
            if pd.notna(raw_baths):
                try:
                    baths = int(float(raw_baths))
                except:
                    pass

            p = Property(
                name=row.get('Project name'),
                bedrooms=beds,
                bathrooms=baths,
                completion_status=row.get('Completion status (off plan/available)'),
                unit_type=row.get('unit type'),
                developer_name=row.get('developer name'),
                price=clean_price(row.get('Price (USD)')),
                area_sq_mtrs=float(row.get('Area (sq mtrs)')) if pd.notna(row.get('Area (sq mtrs)')) else None,
                property_type=row.get('Property type (apartment/villa)'),
                city=row.get('city'),
                country=row.get('country'),
                completion_date=str(row.get('completion_date')) if pd.notna(row.get('completion_date')) else None,
                features=row.get('features'),
                facilities=row.get('facilities'),
                description=row.get('Project description')
            )
            p.save()
            count += 1

            
            if count % 100 == 0:
                print(f"Imported {count}...")
                
        except Exception as e:
            # print(f"Skipping row due to error: {e}")
            pass

    print(f"Successfully imported {count} properties.")

if __name__ == "__main__":
    run()

