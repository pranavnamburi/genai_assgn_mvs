"""
Database utility functions for Movi tools
Handles all database queries and operations
"""

from database import get_session, Stop, Path, Route, Vehicle, Driver, DailyTrip, Deployment
from sqlalchemy import and_, or_
from typing import Dict, List, Optional


# ============================================================================
# READ OPERATIONS - TRIPS
# ============================================================================

def query_trip_status(trip_name: str) -> str:
    """Get status information for a trip"""
    session = get_session()
    try:
        trip = session.query(DailyTrip).filter_by(display_name=trip_name).first()
        
        if not trip:
            return f"Trip '{trip_name}' not found."
        
        # Get deployment info
        deployment = session.query(Deployment).filter_by(trip_id=trip.trip_id).first()
        vehicle_info = ""
        driver_info = ""
        
        if deployment:
            if deployment.vehicle_id:
                vehicle = session.query(Vehicle).filter_by(vehicle_id=deployment.vehicle_id).first()
                vehicle_info = f", Vehicle: {vehicle.license_plate}" if vehicle else ""
            if deployment.driver_id:
                driver = session.query(Driver).filter_by(driver_id=deployment.driver_id).first()
                driver_info = f", Driver: {driver.name}" if driver else ""
        
        return (f"Trip '{trip_name}': "
                f"Status: {trip.live_status}, "
                f"Booking: {trip.booking_status_percentage}%"
                f"{vehicle_info}{driver_info}")
    
    finally:
        session.close()


def query_trip_booking_details(trip_name: str) -> str:
    """Get detailed booking information"""
    session = get_session()
    try:
        trip = session.query(DailyTrip).filter_by(display_name=trip_name).first()
        
        if not trip:
            return f"Trip '{trip_name}' not found."
        
        return f"Trip '{trip_name}' is {trip.booking_status_percentage}% booked."
    
    finally:
        session.close()


def check_trip_has_bookings(trip_name: str) -> Dict:
    """Check if a trip has bookings (for consequence checking)"""
    session = get_session()
    try:
        trip = session.query(DailyTrip).filter_by(display_name=trip_name).first()
        
        if not trip:
            return {"has_bookings": False, "percentage": 0}
        
        return {
            "has_bookings": trip.booking_status_percentage > 0,
            "percentage": trip.booking_status_percentage
        }
    
    finally:
        session.close()


# ============================================================================
# READ OPERATIONS - VEHICLES
# ============================================================================

def query_unassigned_vehicles() -> str:
    """Get list of unassigned vehicles"""
    session = get_session()
    try:
        # Get all vehicles
        all_vehicles = session.query(Vehicle).all()
        
        # Get assigned vehicle IDs
        assigned_ids = [d.vehicle_id for d in session.query(Deployment).all() if d.vehicle_id]
        
        # Filter unassigned
        unassigned = [v for v in all_vehicles if v.vehicle_id not in assigned_ids]
        
        if not unassigned:
            return "All vehicles are currently assigned."
        
        vehicle_list = ", ".join([f"{v.license_plate} ({v.type})" for v in unassigned])
        return f"Unassigned vehicles ({len(unassigned)}): {vehicle_list}"
    
    finally:
        session.close()


def query_vehicle_details(license_plate: str) -> str:
    """Get details about a specific vehicle"""
    session = get_session()
    try:
        vehicle = session.query(Vehicle).filter_by(license_plate=license_plate).first()
        
        if not vehicle:
            return f"Vehicle '{license_plate}' not found."
        
        # Check if assigned
        deployment = session.query(Deployment).filter_by(vehicle_id=vehicle.vehicle_id).first()
        assignment_status = "Not assigned"
        
        if deployment:
            trip = session.query(DailyTrip).filter_by(trip_id=deployment.trip_id).first()
            if trip:
                assignment_status = f"Assigned to trip '{trip.display_name}'"
        
        return (f"Vehicle {vehicle.license_plate}: "
                f"Type: {vehicle.type}, Capacity: {vehicle.capacity}, "
                f"Status: {assignment_status}")
    
    finally:
        session.close()


# ============================================================================
# READ OPERATIONS - DRIVERS
# ============================================================================

def query_drivers(assigned_only: bool = False) -> str:
    """Get list of drivers"""
    session = get_session()
    try:
        all_drivers = session.query(Driver).all()
        
        if assigned_only:
            assigned_ids = [d.driver_id for d in session.query(Deployment).all() if d.driver_id]
            drivers = [d for d in all_drivers if d.driver_id in assigned_ids]
        else:
            drivers = all_drivers
        
        if not drivers:
            return "No drivers found."
        
        driver_list = ", ".join([f"{d.name} ({d.phone_number})" for d in drivers[:10]])
        if len(drivers) > 10:
            driver_list += f", ... and {len(drivers) - 10} more"
        
        return f"Drivers ({len(drivers)}): {driver_list}"
    
    finally:
        session.close()


# ============================================================================
# READ OPERATIONS - PATHS & ROUTES
# ============================================================================

def query_stops_for_path(path_name: str) -> str:
    """Get ordered stops for a path"""
    session = get_session()
    try:
        path = session.query(Path).filter_by(path_name=path_name).first()
        
        if not path:
            return f"Path '{path_name}' not found."
        
        # Get stop names
        stop_names = []
        for stop_id in path.ordered_list_of_stop_ids:
            stop = session.query(Stop).filter_by(stop_id=stop_id).first()
            if stop:
                stop_names.append(stop.name)
        
        return f"Path '{path_name}' stops: {' → '.join(stop_names)}"
    
    finally:
        session.close()


def query_routes_for_path(path_name: str) -> str:
    """Get all routes using a path"""
    session = get_session()
    try:
        path = session.query(Path).filter_by(path_name=path_name).first()
        
        if not path:
            return f"Path '{path_name}' not found."
        
        routes = session.query(Route).filter_by(path_id=path.path_id).all()
        
        if not routes:
            return f"No routes found for path '{path_name}'."
        
        route_list = ", ".join([f"{r.route_display_name} ({r.status})" for r in routes])
        return f"Routes for '{path_name}' ({len(routes)}): {route_list}"
    
    finally:
        session.close()


def query_all_routes(status: Optional[str] = None) -> str:
    """Get all routes, optionally filtered by status"""
    session = get_session()
    try:
        query = session.query(Route)
        
        if status:
            query = query.filter_by(status=status)
        
        routes = query.all()
        
        if not routes:
            return f"No routes found{' with status ' + status if status else ''}."
        
        route_list = "\n".join([
            f"- {r.route_display_name}: {r.start_point} → {r.end_point} ({r.status})"
            for r in routes[:10]
        ])
        
        if len(routes) > 10:
            route_list += f"\n... and {len(routes) - 10} more routes"
        
        return f"Routes ({len(routes)}):\n{route_list}"
    
    finally:
        session.close()


def check_route_has_active_trips(route_name: str) -> Dict:
    """Check if a route has active trips (for consequence checking)"""
    session = get_session()
    try:
        route = session.query(Route).filter_by(route_display_name=route_name).first()
        
        if not route:
            return {"has_trips": False, "count": 0}
        
        trips = session.query(DailyTrip).filter_by(route_id=route.route_id).all()
        
        return {
            "has_trips": len(trips) > 0,
            "count": len(trips)
        }
    
    finally:
        session.close()


# ============================================================================
# CREATE OPERATIONS
# ============================================================================

def create_stop(stop_name: str, latitude: float, longitude: float) -> str:
    """Create a new stop"""
    session = get_session()
    try:
        # Check if stop already exists
        existing = session.query(Stop).filter_by(name=stop_name).first()
        if existing:
            return f"Stop '{stop_name}' already exists."
        
        new_stop = Stop(name=stop_name, latitude=latitude, longitude=longitude)
        session.add(new_stop)
        session.commit()
        session.refresh(new_stop)
        
        return f"✅ Created stop '{stop_name}' (ID: {new_stop.stop_id}) at ({latitude}, {longitude})"
    
    except Exception as e:
        session.rollback()
        return f"❌ Error creating stop: {str(e)}"
    finally:
        session.close()


def create_path(path_name: str, stop_names: List[str]) -> str:
    """Create a new path from stop names"""
    session = get_session()
    try:
        # Check if path exists
        existing = session.query(Path).filter_by(path_name=path_name).first()
        if existing:
            return f"Path '{path_name}' already exists."
        
        # Get stop IDs
        stop_ids = []
        for stop_name in stop_names:
            stop = session.query(Stop).filter_by(name=stop_name).first()
            if not stop:
                return f"❌ Stop '{stop_name}' not found. Please create it first."
            stop_ids.append(stop.stop_id)
        
        new_path = Path(path_name=path_name, ordered_list_of_stop_ids=stop_ids)
        session.add(new_path)
        session.commit()
        session.refresh(new_path)
        
        return f"✅ Created path '{path_name}' (ID: {new_path.path_id}) with {len(stop_ids)} stops"
    
    except Exception as e:
        session.rollback()
        return f"❌ Error creating path: {str(e)}"
    finally:
        session.close()


def create_route(path_name: str, shift_time: str, direction: str) -> str:
    """Create a new route"""
    session = get_session()
    try:
        # Get path
        path = session.query(Path).filter_by(path_name=path_name).first()
        if not path:
            return f"❌ Path '{path_name}' not found."
        
        # Get start and end points
        if path.ordered_list_of_stop_ids:
            start_stop = session.query(Stop).filter_by(stop_id=path.ordered_list_of_stop_ids[0]).first()
            end_stop = session.query(Stop).filter_by(stop_id=path.ordered_list_of_stop_ids[-1]).first()
            start_point = start_stop.name if start_stop else "Unknown"
            end_point = end_stop.name if end_stop else "Unknown"
        else:
            start_point = end_point = "Unknown"
        
        route_display_name = f"{path_name} - {shift_time}"
        
        new_route = Route(
            path_id=path.path_id,
            route_display_name=route_display_name,
            shift_time=shift_time,
            direction=direction,
            start_point=start_point,
            end_point=end_point,
            status='active'
        )
        session.add(new_route)
        session.commit()
        session.refresh(new_route)
        
        return f"✅ Created route '{route_display_name}' (ID: {new_route.route_id})"
    
    except Exception as e:
        session.rollback()
        return f"❌ Error creating route: {str(e)}"
    finally:
        session.close()


def create_daily_trip(route_name: str, display_name: str, booking_percentage: float = 0.0, live_status: str = "NOT STARTED") -> str:
    """Create a new daily trip for a route"""
    session = get_session()
    try:
        # Get route
        route = session.query(Route).filter_by(route_display_name=route_name).first()
        if not route:
            return f"❌ Route '{route_name}' not found."
        
        # Check if trip with same display name already exists
        existing = session.query(DailyTrip).filter_by(display_name=display_name).first()
        if existing:
            return f"❌ Trip '{display_name}' already exists."
        
        # Validate booking percentage
        if not (0 <= booking_percentage <= 100):
            return f"❌ Booking percentage must be between 0 and 100."
        
        # Create new daily trip
        new_trip = DailyTrip(
            route_id=route.route_id,
            display_name=display_name,
            booking_status_percentage=booking_percentage,
            live_status=live_status
        )
        session.add(new_trip)
        session.commit()
        session.refresh(new_trip)
        
        # Create empty deployment for this trip
        new_deployment = Deployment(
            trip_id=new_trip.trip_id,
            vehicle_id=None,
            driver_id=None
        )
        session.add(new_deployment)
        session.commit()
        
        return f"✅ Created daily trip '{display_name}' (ID: {new_trip.trip_id}) for route '{route_name}'"
    
    except Exception as e:
        session.rollback()
        return f"❌ Error creating daily trip: {str(e)}"
    finally:
        session.close()


def create_deployment(trip_name: str, vehicle_license: str, driver_name: str) -> str:
    """Assign vehicle and driver to a trip"""
    session = get_session()
    try:
        # Get trip
        trip = session.query(DailyTrip).filter_by(display_name=trip_name).first()
        if not trip:
            return f"❌ Trip '{trip_name}' not found."
        
        # Get vehicle
        vehicle = session.query(Vehicle).filter_by(license_plate=vehicle_license).first()
        if not vehicle:
            return f"❌ Vehicle '{vehicle_license}' not found."
        
        # Get driver
        driver = session.query(Driver).filter_by(name=driver_name).first()
        if not driver:
            return f"❌ Driver '{driver_name}' not found."
        
        # Check if deployment exists
        existing = session.query(Deployment).filter_by(trip_id=trip.trip_id).first()
        
        if existing:
            # Update existing
            existing.vehicle_id = vehicle.vehicle_id
            existing.driver_id = driver.driver_id
            action = "Updated"
        else:
            # Create new
            new_deployment = Deployment(
                trip_id=trip.trip_id,
                vehicle_id=vehicle.vehicle_id,
                driver_id=driver.driver_id
            )
            session.add(new_deployment)
            action = "Created"
        
        session.commit()
        
        return f"✅ {action} deployment: {vehicle_license} with driver {driver_name} assigned to '{trip_name}'"
    
    except Exception as e:
        session.rollback()
        return f"❌ Error creating deployment: {str(e)}"
    finally:
        session.close()


# ============================================================================
# DELETE/UPDATE OPERATIONS
# ============================================================================

def delete_daily_trip(trip_name: str) -> str:
    """Delete a daily trip and its deployment
    
    Note: This function performs the actual deletion. 
    Consequence checking (for bookings) is handled by the agent's check_consequences node.
    """
    session = get_session()
    try:
        # Get trip
        trip = session.query(DailyTrip).filter_by(display_name=trip_name).first()
        if not trip:
            return f"❌ Trip '{trip_name}' not found."
        
        # Get deployment info for better messaging
        deployment = session.query(Deployment).filter_by(trip_id=trip.trip_id).first()
        has_vehicle = deployment and deployment.vehicle_id is not None
        has_driver = deployment and deployment.driver_id is not None
        
        # Store trip info before deletion
        trip_id = trip.trip_id
        booking_percentage = trip.booking_status_percentage
        
        # Delete deployment first (due to foreign key constraint)
        if deployment:
            session.delete(deployment)
        
        # Delete trip
        session.delete(trip)
        session.commit()
        
        # Build success message
        assignment_info = ""
        if has_vehicle or has_driver:
            assignment_info = " (freed up assigned vehicle/driver)"
        
        booking_info = ""
        if booking_percentage > 0:
            booking_info = f" [had {booking_percentage}% bookings]"
        
        return f"✅ Deleted daily trip '{trip_name}' (ID: {trip_id}){assignment_info}{booking_info}"
    
    except Exception as e:
        session.rollback()
        return f"❌ Error deleting daily trip: {str(e)}"
    finally:
        session.close()


def delete_vehicle_from_trip(trip_name: str) -> str:
    """Remove vehicle from a trip (keeps driver)"""
    session = get_session()
    try:
        trip = session.query(DailyTrip).filter_by(display_name=trip_name).first()
        if not trip:
            return f"❌ Trip '{trip_name}' not found."
        
        deployment = session.query(Deployment).filter_by(trip_id=trip.trip_id).first()
        if not deployment or not deployment.vehicle_id:
            return f"No vehicle assigned to trip '{trip_name}'."
        
        vehicle = session.query(Vehicle).filter_by(vehicle_id=deployment.vehicle_id).first()
        vehicle_name = vehicle.license_plate if vehicle else "Unknown"
        
        # Remove vehicle (set to None)
        deployment.vehicle_id = None
        session.commit()
        
        return f"✅ Removed vehicle {vehicle_name} from trip '{trip_name}'"
    
    except Exception as e:
        session.rollback()
        return f"❌ Error removing vehicle: {str(e)}"
    finally:
        session.close()


def deactivate_route(route_name: str) -> str:
    """Deactivate a route"""
    session = get_session()
    try:
        route = session.query(Route).filter_by(route_display_name=route_name).first()
        if not route:
            return f"❌ Route '{route_name}' not found."
        
        if route.status == 'deactivated':
            return f"Route '{route_name}' is already deactivated."
        
        route.status = 'deactivated'
        session.commit()
        
        return f"✅ Route '{route_name}' has been deactivated"
    
    except Exception as e:
        session.rollback()
        return f"❌ Error deactivating route: {str(e)}"
    finally:
        session.close()

