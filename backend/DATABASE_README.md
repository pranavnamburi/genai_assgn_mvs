# Movi Transport Management Database

## Overview

This database implements the complete data layer for the Movi transport management system, following the **Stop → Path → Route → Trip** data flow model.

## Database Schema

### Layer 1: Static Assets (manageRoute page)

#### 1. **Stops** Table
- `stop_id` (Primary Key)
- `name` (Unique)
- `latitude`
- `longitude`

**Purpose**: Physical stop locations (e.g., "Gavipuram", "Peenya")

#### 2. **Paths** Table
- `path_id` (Primary Key)
- `path_name` (Unique)
- `ordered_list_of_stop_ids` (JSON array)

**Purpose**: Ordered sequences of stops

#### 3. **Routes** Table
- `route_id` (Primary Key)
- `path_id` (Foreign Key → Paths)
- `route_display_name` (e.g., "Path-1 - 07:00")
- `shift_time` (e.g., "07:00")
- `direction` (Inbound/Outbound/Circular)
- `start_point`
- `end_point`
- `status` (active/deactivated)

**Purpose**: Combines a Path with timing information

### Layer 2: Dynamic Operations (busDashboard page)

#### 4. **Vehicles** Table
- `vehicle_id` (Primary Key)
- `license_plate` (Unique)
- `type` (Bus/Cab)
- `capacity`

**Purpose**: Fleet vehicles

#### 5. **Drivers** Table
- `driver_id` (Primary Key)
- `name`
- `phone_number`

**Purpose**: Driver information

#### 6. **DailyTrips** Table
- `trip_id` (Primary Key)
- `route_id` (Foreign Key → Routes)
- `display_name` (e.g., "Bulk - 00:01")
- `booking_status_percentage` (0-100)
- `live_status` (e.g., "DEPLOYED", "EN ROUTE")

**Purpose**: Daily trip instances shown in busDashboard

#### 7. **Deployments** Table
- `deployment_id` (Primary Key)
- `trip_id` (Foreign Key → DailyTrips)
- `vehicle_id` (Foreign Key → Vehicles, nullable)
- `driver_id` (Foreign Key → Drivers, nullable)

**Purpose**: Links vehicles and drivers to trips

## Files

### `database.py`
Defines SQLAlchemy models and provides database initialization functions:
- `init_db(db_path)` - Creates database and tables
- `get_session(db_path)` - Returns a database session

### `seed.py`
Populates the database with realistic dummy data:
- **14 stops** across Bangalore
- **5 paths** with logical stop sequences
- **8 routes** with various timings
- **10 vehicles** (7 buses, 3 cabs)
- **10 drivers**
- **8 daily trips** with varying booking statuses
- **8 deployments** (some trips are unassigned)

### `verify_db.py`
Verification script to check database contents and relationships

## Key Data Points

### Critical: "Bulk - 00:01" Trip
This trip is **essential for the demo** as it demonstrates the "Consequence Flow":
- **Display Name**: "Bulk - 00:01"
- **Booking Status**: 25% (triggers warning when removing vehicle)
- **Assigned Vehicle**: KA-01-AB-1234
- **Assigned Driver**: Amit Kumar
- **Live Status**: "00:01 IN"

When Movi is asked to remove the vehicle from this trip, the langgraph agent should detect the 25% booking status and warn the user about consequences.

### Sample Data for Testing

#### Paths with Routes:
- **Path-1**: Gavipuram → Temple → Koramangala → MG Road
  - Routes: 07:00 (Inbound), 19:00 (Outbound)
- **Path-2**: Peenya → Whitefield → Marathahalli → Indiranagar
  - Routes: 08:30 (Inbound), 19:45 (Outbound)

#### Unassigned Resources:
- **Vehicles**: 4 unassigned (available for deployment)
- **Drivers**: 4 unassigned (available for deployment)
- **Trips**: 2 trips without deployments ("Path Path - 00:02", "Path-1 Extra - 07:15")

## Usage

### Create Database and Seed Data
```bash
cd backend
python3 seed.py
```

### Verify Database
```bash
python3 verify_db.py
```

### Use in Python Code
```python
from database import get_session, DailyTrip, Vehicle, Deployment

# Get a session
session = get_session()

# Query trips
trips = session.query(DailyTrip).all()

# Find "Bulk - 00:01"
bulk_trip = session.query(DailyTrip).filter_by(display_name="Bulk - 00:01").first()
print(f"Booking: {bulk_trip.booking_status_percentage}%")

# Check deployment
deployment = session.query(Deployment).filter_by(trip_id=bulk_trip.trip_id).first()
if deployment.vehicle_id:
    vehicle = session.query(Vehicle).filter_by(vehicle_id=deployment.vehicle_id).first()
    print(f"Vehicle: {vehicle.license_plate}")

session.close()
```

## Database File

The SQLite database is stored as: `movi_transport.db` (44KB)

## Technology Stack

- **SQLAlchemy 2.0.44** - ORM
- **SQLite 3** - Database engine
- **Python 3.12** - Runtime

## Schema Relationships

```
Stops (1) ←── (many) Path.ordered_list_of_stop_ids
Paths (1) ←── (many) Routes
Routes (1) ←── (many) DailyTrips
Vehicles (1) ←── (many) Deployments
Drivers (1) ←── (many) Deployments
DailyTrips (1) ←── (many) Deployments
```

## Notes

- The schema follows the exact requirements from the assignment specification
- All relationships are properly defined with foreign keys
- JSON is used for storing ordered stop lists in Paths table
- The database supports all required operations for Movi's 10+ actions
- Data is structured to enable the "Tribal Knowledge" consequence checking logic

