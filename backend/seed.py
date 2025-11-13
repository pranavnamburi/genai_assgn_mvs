"""
Seed script to populate the Movi Transport Management database with realistic dummy data
"""

from database import (
    init_db, Stop, Path, Route, Vehicle, Driver, DailyTrip, Deployment
)
import json


def seed_database(db_path='sqlite:///movi_transport.db'):
    """Populate database with comprehensive dummy data"""
    
    print("Initializing database...")
    engine, SessionLocal = init_db(db_path)
    session = SessionLocal()
    
    try:
        # Clear existing data (for re-seeding)
        print("Clearing existing data...")
        session.query(Deployment).delete()
        session.query(DailyTrip).delete()
        session.query(Route).delete()
        session.query(Path).delete()
        session.query(Stop).delete()
        session.query(Vehicle).delete()
        session.query(Driver).delete()
        session.commit()
        
        # =============================================================================
        # SEED STATIC ASSETS (Layer 1)
        # =============================================================================
        
        print("\n🚏 Seeding Stops...")
        stops_data = [
            {"name": "Gavipuram", "latitude": 12.9350, "longitude": 77.5850},
            {"name": "Peenya", "latitude": 13.0330, "longitude": 77.5200},
            {"name": "Temple", "latitude": 12.9480, "longitude": 77.5820},
            {"name": "Electronic City", "latitude": 12.8450, "longitude": 77.6600},
            {"name": "Whitefield", "latitude": 12.9698, "longitude": 77.7499},
            {"name": "Marathahalli", "latitude": 12.9591, "longitude": 77.6974},
            {"name": "Koramangala", "latitude": 12.9352, "longitude": 77.6245},
            {"name": "HSR Layout", "latitude": 12.9121, "longitude": 77.6446},
            {"name": "Indiranagar", "latitude": 12.9784, "longitude": 77.6408},
            {"name": "JP Nagar", "latitude": 12.9082, "longitude": 77.5855},
            {"name": "BTM Layout", "latitude": 12.9165, "longitude": 77.6101},
            {"name": "Jayanagar", "latitude": 12.9250, "longitude": 77.5937},
            {"name": "MG Road", "latitude": 12.9750, "longitude": 77.6060},
            {"name": "Bangalore Airport", "latitude": 13.1986, "longitude": 77.7066},
        ]
        
        stops = []
        for stop_data in stops_data:
            stop = Stop(**stop_data)
            session.add(stop)
            stops.append(stop)
        
        session.commit()
        print(f"   ✓ Created {len(stops)} stops")
        
        # Refresh to get IDs
        for stop in stops:
            session.refresh(stop)
        
        # =============================================================================
        print("\n🛤️  Seeding Paths...")
        paths_data = [
            {
                "path_name": "Path-1",
                "ordered_list_of_stop_ids": [1, 3, 7, 13]  # Gavipuram -> Temple -> Koramangala -> MG Road
            },
            {
                "path_name": "Path-2",
                "ordered_list_of_stop_ids": [2, 5, 6, 9]  # Peenya -> Whitefield -> Marathahalli -> Indiranagar
            },
            {
                "path_name": "Tech-Park-Route",
                "ordered_list_of_stop_ids": [4, 11, 12, 10]  # Electronic City -> BTM -> Jayanagar -> JP Nagar
            },
            {
                "path_name": "Airport-Express",
                "ordered_list_of_stop_ids": [14, 13, 9, 5]  # Airport -> MG Road -> Indiranagar -> Whitefield
            },
            {
                "path_name": "South-Loop",
                "ordered_list_of_stop_ids": [7, 8, 11, 10, 1]  # Koramangala -> HSR -> BTM -> JP Nagar -> Gavipuram
            },
        ]
        
        paths = []
        for path_data in paths_data:
            path = Path(**path_data)
            session.add(path)
            paths.append(path)
        
        session.commit()
        print(f"   ✓ Created {len(paths)} paths")
        
        # Refresh to get IDs
        for path in paths:
            session.refresh(path)
        
        # =============================================================================
        print("\n🗺️  Seeding Routes...")
        
        # Helper function to get stop names
        def get_stop_name(stop_id):
            return session.query(Stop).filter_by(stop_id=stop_id).first().name
        
        routes_data = []
        
        # Routes for Path-1
        path1 = paths[0]
        routes_data.extend([
            {
                "path_id": path1.path_id,
                "route_display_name": "Path-1 - 07:00",
                "shift_time": "07:00",
                "direction": "Inbound",
                "start_point": get_stop_name(path1.ordered_list_of_stop_ids[0]),
                "end_point": get_stop_name(path1.ordered_list_of_stop_ids[-1]),
                "status": "active"
            },
            {
                "path_id": path1.path_id,
                "route_display_name": "Path-1 - 19:00",
                "shift_time": "19:00",
                "direction": "Outbound",
                "start_point": get_stop_name(path1.ordered_list_of_stop_ids[-1]),
                "end_point": get_stop_name(path1.ordered_list_of_stop_ids[0]),
                "status": "active"
            },
        ])
        
        # Routes for Path-2
        path2 = paths[1]
        routes_data.extend([
            {
                "path_id": path2.path_id,
                "route_display_name": "Path-2 - 08:30",
                "shift_time": "08:30",
                "direction": "Inbound",
                "start_point": get_stop_name(path2.ordered_list_of_stop_ids[0]),
                "end_point": get_stop_name(path2.ordered_list_of_stop_ids[-1]),
                "status": "active"
            },
            {
                "path_id": path2.path_id,
                "route_display_name": "Path-2 - 19:45",
                "shift_time": "19:45",
                "direction": "Outbound",
                "start_point": get_stop_name(path2.ordered_list_of_stop_ids[-1]),
                "end_point": get_stop_name(path2.ordered_list_of_stop_ids[0]),
                "status": "active"
            },
        ])
        
        # Routes for other paths
        path3 = paths[2]
        routes_data.append({
            "path_id": path3.path_id,
            "route_display_name": "Tech-Park-Route - 09:00",
            "shift_time": "09:00",
            "direction": "Inbound",
            "start_point": get_stop_name(path3.ordered_list_of_stop_ids[0]),
            "end_point": get_stop_name(path3.ordered_list_of_stop_ids[-1]),
            "status": "active"
        })
        
        path4 = paths[3]
        routes_data.append({
            "path_id": path4.path_id,
            "route_display_name": "Airport-Express - 05:30",
            "shift_time": "05:30",
            "direction": "Inbound",
            "start_point": get_stop_name(path4.ordered_list_of_stop_ids[0]),
            "end_point": get_stop_name(path4.ordered_list_of_stop_ids[-1]),
            "status": "active"
        })
        
        path5 = paths[4]
        routes_data.extend([
            {
                "path_id": path5.path_id,
                "route_display_name": "South-Loop - 06:45",
                "shift_time": "06:45",
                "direction": "Circular",
                "start_point": get_stop_name(path5.ordered_list_of_stop_ids[0]),
                "end_point": get_stop_name(path5.ordered_list_of_stop_ids[-1]),
                "status": "active"
            },
            {
                "path_id": path5.path_id,
                "route_display_name": "South-Loop - 18:00",
                "shift_time": "18:00",
                "direction": "Circular",
                "start_point": get_stop_name(path5.ordered_list_of_stop_ids[0]),
                "end_point": get_stop_name(path5.ordered_list_of_stop_ids[-1]),
                "status": "deactivated"
            },
        ])
        
        routes = []
        for route_data in routes_data:
            route = Route(**route_data)
            session.add(route)
            routes.append(route)
        
        session.commit()
        print(f"   ✓ Created {len(routes)} routes")
        
        # Refresh to get IDs
        for route in routes:
            session.refresh(route)
        
        # =============================================================================
        # SEED DYNAMIC ASSETS (Layer 2)
        # =============================================================================
        
        print("\n🚌 Seeding Vehicles...")
        vehicles_data = [
            {"license_plate": "KA-01-AB-1234", "type": "Bus", "capacity": 40},
            {"license_plate": "KA-02-CD-5678", "type": "Bus", "capacity": 45},
            {"license_plate": "KA-03-EF-9012", "type": "Bus", "capacity": 40},
            {"license_plate": "MH-12-3456", "type": "Bus", "capacity": 50},
            {"license_plate": "KA-05-GH-3456", "type": "Bus", "capacity": 40},
            {"license_plate": "KA-06-IJ-7890", "type": "Cab", "capacity": 6},
            {"license_plate": "KA-07-KL-1234", "type": "Cab", "capacity": 4},
            {"license_plate": "KA-08-MN-5678", "type": "Cab", "capacity": 6},
            {"license_plate": "KA-09-OP-9012", "type": "Bus", "capacity": 40},
            {"license_plate": "KA-10-QR-3456", "type": "Bus", "capacity": 45},
        ]
        
        vehicles = []
        for vehicle_data in vehicles_data:
            vehicle = Vehicle(**vehicle_data)
            session.add(vehicle)
            vehicles.append(vehicle)
        
        session.commit()
        print(f"   ✓ Created {len(vehicles)} vehicles")
        
        # Refresh to get IDs
        for vehicle in vehicles:
            session.refresh(vehicle)
        
        # =============================================================================
        print("\n👨‍✈️ Seeding Drivers...")
        drivers_data = [
            {"name": "Amit Kumar", "phone_number": "+91-9876543210"},
            {"name": "Rajesh Singh", "phone_number": "+91-9876543211"},
            {"name": "Suresh Patel", "phone_number": "+91-9876543212"},
            {"name": "Vijay Sharma", "phone_number": "+91-9876543213"},
            {"name": "Prakash Reddy", "phone_number": "+91-9876543214"},
            {"name": "Deepak Rao", "phone_number": "+91-9876543215"},
            {"name": "Ravi Kumar", "phone_number": "+91-9876543216"},
            {"name": "Anil Verma", "phone_number": "+91-9876543217"},
            {"name": "Manoj Gupta", "phone_number": "+91-9876543218"},
            {"name": "Sandeep Jain", "phone_number": "+91-9876543219"},
        ]
        
        drivers = []
        for driver_data in drivers_data:
            driver = Driver(**driver_data)
            session.add(driver)
            drivers.append(driver)
        
        session.commit()
        print(f"   ✓ Created {len(drivers)} drivers")
        
        # Refresh to get IDs
        for driver in drivers:
            session.refresh(driver)
        
        # =============================================================================
        print("\n🚦 Seeding Daily Trips...")
        
        daily_trips_data = [
            # CRITICAL: "Bulk - 00:01" trip with 25% booking status (as required)
            {
                "route_id": routes[0].route_id,  # Path-1 - 07:00
                "display_name": "Bulk - 00:01",
                "booking_status_percentage": 25.0,
                "live_status": "00:01 IN"
            },
            {
                "route_id": routes[1].route_id,  # Path-1 - 19:00
                "display_name": "Path-1 Evening - 19:00",
                "booking_status_percentage": 60.0,
                "live_status": "DEPLOYED"
            },
            {
                "route_id": routes[2].route_id,  # Path-2 - 08:30
                "display_name": "Path Path - 00:02",
                "booking_status_percentage": 0.0,
                "live_status": "NOT STARTED"
            },
            {
                "route_id": routes[3].route_id,  # Path-2 - 19:45
                "display_name": "Path-2 Evening - 19:45",
                "booking_status_percentage": 45.0,
                "live_status": "DEPLOYED"
            },
            {
                "route_id": routes[4].route_id,  # Tech-Park-Route - 09:00
                "display_name": "Tech-Park Morning",
                "booking_status_percentage": 80.0,
                "live_status": "EN ROUTE"
            },
            {
                "route_id": routes[5].route_id,  # Airport-Express - 05:30
                "display_name": "Airport Express - 05:30",
                "booking_status_percentage": 30.0,
                "live_status": "DEPLOYED"
            },
            {
                "route_id": routes[6].route_id,  # South-Loop - 06:45
                "display_name": "South Circular - Morning",
                "booking_status_percentage": 15.0,
                "live_status": "READY"
            },
            {
                "route_id": routes[0].route_id,  # Additional trip on Path-1 - 07:00
                "display_name": "Path-1 Extra - 07:15",
                "booking_status_percentage": 0.0,
                "live_status": "NOT STARTED"
            },
        ]
        
        daily_trips = []
        for trip_data in daily_trips_data:
            trip = DailyTrip(**trip_data)
            session.add(trip)
            daily_trips.append(trip)
        
        session.commit()
        print(f"   ✓ Created {len(daily_trips)} daily trips")
        print(f"   ⚠️  CRITICAL: 'Bulk - 00:01' trip created with 25% booking status")
        
        # Refresh to get IDs
        for trip in daily_trips:
            session.refresh(trip)
        
        # =============================================================================
        print("\n🔗 Seeding Deployments...")
        
        deployments_data = [
            # Bulk - 00:01 has deployment (vehicle + driver)
            {
                "trip_id": daily_trips[0].trip_id,  # Bulk - 00:01
                "vehicle_id": vehicles[0].vehicle_id,  # KA-01-AB-1234
                "driver_id": drivers[0].driver_id  # Amit Kumar
            },
            # Path-1 Evening - 19:00 has deployment
            {
                "trip_id": daily_trips[1].trip_id,
                "vehicle_id": vehicles[1].vehicle_id,  # KA-02-CD-5678
                "driver_id": drivers[1].driver_id  # Rajesh Singh
            },
            # Path Path - 00:02 has NO deployment (unassigned)
            {
                "trip_id": daily_trips[2].trip_id,
                "vehicle_id": None,
                "driver_id": None
            },
            # Path-2 Evening - 19:45 has deployment
            {
                "trip_id": daily_trips[3].trip_id,
                "vehicle_id": vehicles[2].vehicle_id,  # KA-03-EF-9012
                "driver_id": drivers[2].driver_id  # Suresh Patel
            },
            # Tech-Park Morning has deployment
            {
                "trip_id": daily_trips[4].trip_id,
                "vehicle_id": vehicles[3].vehicle_id,  # MH-12-3456
                "driver_id": drivers[3].driver_id  # Vijay Sharma
            },
            # Airport Express has deployment
            {
                "trip_id": daily_trips[5].trip_id,
                "vehicle_id": vehicles[4].vehicle_id,  # KA-05-GH-3456
                "driver_id": drivers[4].driver_id  # Prakash Reddy
            },
            # South Circular has deployment (cab)
            {
                "trip_id": daily_trips[6].trip_id,
                "vehicle_id": vehicles[5].vehicle_id,  # KA-06-IJ-7890 (Cab)
                "driver_id": drivers[5].driver_id  # Deepak Rao
            },
            # Path-1 Extra - 07:15 has NO deployment
            {
                "trip_id": daily_trips[7].trip_id,
                "vehicle_id": None,
                "driver_id": None
            },
        ]
        
        deployments = []
        for deployment_data in deployments_data:
            deployment = Deployment(**deployment_data)
            session.add(deployment)
            deployments.append(deployment)
        
        session.commit()
        print(f"   ✓ Created {len(deployments)} deployments")
        
        # =============================================================================
        # SUMMARY
        # =============================================================================
        
        print("\n" + "="*70)
        print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"📊 Summary:")
        print(f"   • Stops: {len(stops)}")
        print(f"   • Paths: {len(paths)}")
        print(f"   • Routes: {len(routes)}")
        print(f"   • Vehicles: {len(vehicles)}")
        print(f"   • Drivers: {len(drivers)}")
        print(f"   • Daily Trips: {len(daily_trips)}")
        print(f"   • Deployments: {len(deployments)}")
        print()
        print(f"🎯 Key Data Points:")
        print(f"   • 'Bulk - 00:01' trip: ✓ Created (ID: {daily_trips[0].trip_id})")
        print(f"   • Booking Status: {daily_trips[0].booking_status_percentage}%")
        print(f"   • Assigned Vehicle: {vehicles[0].license_plate}")
        print(f"   • Assigned Driver: {drivers[0].name}")
        print()
        print(f"   • Unassigned vehicles: {len(vehicles) - len([d for d in deployments if d.vehicle_id])}")
        print(f"   • Unassigned drivers: {len(drivers) - len([d for d in deployments if d.driver_id])}")
        print()
        print(f"💾 Database: {db_path}")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()

