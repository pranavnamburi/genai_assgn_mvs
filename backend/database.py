"""
Database schema for Movi Transport Management System
Defines SQLAlchemy models for all static and dynamic assets
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

# =============================================================================
# STATIC ASSETS (Layer 1 - manageRoute page)
# =============================================================================

class Stop(Base):
    """Represents a physical stop location"""
    __tablename__ = 'stops'
    
    stop_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<Stop(id={self.stop_id}, name='{self.name}')>"


class Path(Base):
    """Represents an ordered sequence of stops"""
    __tablename__ = 'paths'
    
    path_id = Column(Integer, primary_key=True, autoincrement=True)
    path_name = Column(String(100), nullable=False, unique=True)
    ordered_list_of_stop_ids = Column(JSON, nullable=False)  # Stored as JSON array [1, 2, 3]
    
    # Relationship
    routes = relationship("Route", back_populates="path")
    
    def __repr__(self):
        return f"<Path(id={self.path_id}, name='{self.path_name}')>"


class Route(Base):
    """Combines a Path with timing information"""
    __tablename__ = 'routes'
    
    route_id = Column(Integer, primary_key=True, autoincrement=True)
    path_id = Column(Integer, ForeignKey('paths.path_id'), nullable=False)
    route_display_name = Column(String(100), nullable=False)  # e.g., "Path2 - 19:45"
    shift_time = Column(String(10), nullable=False)  # e.g., "19:45"
    direction = Column(String(50))  # e.g., "Inbound", "Outbound"
    start_point = Column(String(100))  # Name of first stop
    end_point = Column(String(100))  # Name of last stop
    status = Column(String(20), default='active')  # 'active' or 'deactivated'
    
    # Relationships
    path = relationship("Path", back_populates="routes")
    daily_trips = relationship("DailyTrip", back_populates="route")
    
    def __repr__(self):
        return f"<Route(id={self.route_id}, name='{self.route_display_name}', status='{self.status}')>"


# =============================================================================
# DYNAMIC ASSETS & OPERATIONS (Layer 2 - busDashboard page)
# =============================================================================

class Vehicle(Base):
    """Represents a transport vehicle (Bus or Cab)"""
    __tablename__ = 'vehicles'
    
    vehicle_id = Column(Integer, primary_key=True, autoincrement=True)
    license_plate = Column(String(20), nullable=False, unique=True)
    type = Column(String(20), nullable=False)  # 'Bus' or 'Cab'
    capacity = Column(Integer, nullable=False)
    
    # Relationship
    deployments = relationship("Deployment", back_populates="vehicle")
    
    def __repr__(self):
        return f"<Vehicle(id={self.vehicle_id}, plate='{self.license_plate}', type='{self.type}')>"


class Driver(Base):
    """Represents a driver"""
    __tablename__ = 'drivers'
    
    driver_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(15), nullable=False)
    
    # Relationship
    deployments = relationship("Deployment", back_populates="driver")
    
    def __repr__(self):
        return f"<Driver(id={self.driver_id}, name='{self.name}')>"


class DailyTrip(Base):
    """Represents a daily trip instance (appears in left panel of busDashboard)"""
    __tablename__ = 'daily_trips'
    
    trip_id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(Integer, ForeignKey('routes.route_id'), nullable=False)
    display_name = Column(String(100), nullable=False)  # e.g., "Bulk - 00:01"
    booking_status_percentage = Column(Float, default=0.0)  # 0-100
    live_status = Column(String(50))  # e.g., "00:01 IN", "DEPLOYED", "NOT STARTED"
    
    # Relationships
    route = relationship("Route", back_populates="daily_trips")
    deployments = relationship("Deployment", back_populates="trip", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DailyTrip(id={self.trip_id}, name='{self.display_name}', booking={self.booking_status_percentage}%)>"


class Deployment(Base):
    """Links vehicles and drivers to daily trips"""
    __tablename__ = 'deployments'
    
    deployment_id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(Integer, ForeignKey('daily_trips.trip_id'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.vehicle_id'), nullable=True)
    driver_id = Column(Integer, ForeignKey('drivers.driver_id'), nullable=True)
    
    # Relationships
    trip = relationship("DailyTrip", back_populates="deployments")
    vehicle = relationship("Vehicle", back_populates="deployments")
    driver = relationship("Driver", back_populates="deployments")
    
    def __repr__(self):
        return f"<Deployment(id={self.deployment_id}, trip_id={self.trip_id}, vehicle_id={self.vehicle_id}, driver_id={self.driver_id})>"


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def init_db(db_path='sqlite:///movi_transport.db'):
    """
    Initialize the database and create all tables
    
    Args:
        db_path: SQLite database path (default: 'sqlite:///movi_transport.db')
    
    Returns:
        tuple: (engine, SessionLocal)
    """
    engine = create_engine(db_path, echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    
    return engine, SessionLocal


def get_session(db_path='sqlite:///movi_transport.db'):
    """
    Get a database session
    
    Args:
        db_path: SQLite database path
    
    Returns:
        Session object
    """
    engine = create_engine(db_path, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


if __name__ == "__main__":
    # Test database creation
    print("Creating database schema...")
    engine, SessionLocal = init_db()
    print(f"✓ Database created successfully!")
    print(f"✓ Tables: {', '.join(Base.metadata.tables.keys())}")

