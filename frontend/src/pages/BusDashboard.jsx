"use client"

import { useState, useEffect } from "react"
import { MapPin, Users, AlertCircle, CheckCircle2 } from "lucide-react"
import MoviChat from "../components/MoviChat"
import { apiService } from "../services/api"

export default function BusDashboard() {
  const [selectedRoute, setSelectedRoute] = useState(0)
  const [trips, setTrips] = useState([])
  const [vehicles, setVehicles] = useState([])
  const [drivers, setDrivers] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState([
    { label: "Vehicles Not Assigned", value: "0", color: "bg-orange-100 text-orange-700" },
    { label: "Trips Not Generated", value: "0", color: "bg-blue-100 text-blue-700" },
    { label: "Employees Scheduled", value: "0", color: "bg-emerald-100 text-emerald-700" },
    { label: "Ongoing Trips", value: "0", color: "bg-purple-100 text-purple-700" },
  ])

  // Fetch data on component mount
  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [tripsResponse, vehiclesResponse, driversResponse] = await Promise.all([
        apiService.getTrips(),
        apiService.getVehicles(),
        apiService.getDrivers(),
      ])

      if (tripsResponse.success) {
        setTrips(tripsResponse.data)
      }
      if (vehiclesResponse.success) {
        setVehicles(vehiclesResponse.data)
      }
      if (driversResponse.success) {
        setDrivers(driversResponse.data)
      }

      // Calculate stats
      calculateStats(tripsResponse.data, vehiclesResponse.data, driversResponse.data)
    } catch (error) {
      console.error("Error fetching data:", error)
    } finally {
      setLoading(false)
    }
  }

  const calculateStats = (tripsData, vehiclesData, driversData) => {
    // Count vehicles not assigned
    const assignedVehicleIds = new Set(
      tripsData.filter(t => t.vehicle).map(t => t.vehicle.vehicle_id)
    )
    const unassignedVehicles = vehiclesData.filter(v => !assignedVehicleIds.has(v.vehicle_id))

    // Count trips without vehicle assignment
    const tripsNotGenerated = tripsData.filter(t => !t.vehicle).length

    // Count assigned drivers (employees scheduled)
    const assignedDriverIds = new Set(
      tripsData.filter(t => t.driver).map(t => t.driver.driver_id)
    )
    const employeesScheduled = assignedDriverIds.size

    // Count ongoing trips (trips with both vehicle and driver)
    const ongoingTrips = tripsData.filter(t => t.vehicle && t.driver && t.live_status.includes("IN")).length

    setStats([
      { label: "Vehicles Not Assigned", value: unassignedVehicles.length.toString(), color: "bg-orange-100 text-orange-700" },
      { label: "Trips Not Generated", value: tripsNotGenerated.toString(), color: "bg-blue-100 text-blue-700" },
      { label: "Employees Scheduled", value: employeesScheduled.toString(), color: "bg-emerald-100 text-emerald-700" },
      { label: "Ongoing Trips", value: ongoingTrips.toString(), color: "bg-purple-100 text-purple-700" },
    ])
  }

  // Get currently selected trip
  const selectedTrip = trips[selectedRoute] || null

  return (
    <>
      <div className="flex flex-col h-[calc(100vh-60px)] overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-border p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <input type="date" defaultValue="2025-07-11" className="px-3 py-2 border border-input rounded" />
              <select className="px-3 py-2 border border-input rounded bg-white">
                <option>Route</option>
              </select>
              <input type="text" placeholder="Search Name/Id" className="px-3 py-2 border border-input rounded flex-1" />
              <button className="px-3 py-2 border border-input rounded hover:bg-muted">Filters</button>
            </div>
            <a href="#" className="text-blue-600 text-sm hover:underline">
              Switch to Old UI
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-3">
            {stats.map((stat, i) => (
              <div key={i} className={`${stat.color} rounded p-3`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium opacity-75">{stat.label}</p>
                    <p className="text-2xl font-bold">{stat.value}</p>
                  </div>
                  <Users className="w-8 h-8 opacity-20" />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Left Sidebar - Routes List */}
          <div className="w-80 border-r border-border bg-background overflow-y-auto">
            <div className="flex gap-2 border-b border-border p-4">
              <button className="flex-1 px-3 py-2 border border-input rounded hover:bg-muted text-sm">Track Route</button>
              <button className="flex-1 px-3 py-2 border border-input rounded hover:bg-muted text-sm">
                Generate Tripsheet
              </button>
              <button className="flex-1 px-3 py-2 border border-input rounded hover:bg-muted text-sm">Merge Route</button>
              <button className="px-3 py-2 border border-input rounded hover:bg-muted">...</button>
            </div>

            <div className="p-4 space-y-2">
              {loading ? (
                <div className="text-center py-8 text-muted-foreground">Loading trips...</div>
              ) : trips.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">No trips available</div>
              ) : (
                trips.map((trip, i) => (
                  <div
                    key={trip.trip_id}
                    onClick={() => setSelectedRoute(i)}
                    className={`p-3 rounded cursor-pointer border ${
                      selectedRoute === i ? "border-blue-500 bg-blue-50" : "border-border bg-white hover:bg-muted"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <input type="checkbox" className="rounded" />
                          <p className="font-medium text-sm">{trip.display_name}</p>
                        </div>
                        <p className={`text-xs mt-1 ${trip.booking_status_percentage >= 50 ? "text-red-600" : "text-emerald-600"}`}>
                          {trip.live_status}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-blue-600 font-semibold text-sm">{Math.round(trip.booking_status_percentage)}%</p>
                        <p className="text-xs text-muted-foreground">booked</p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="p-4 border-t border-border flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Rows per page:</span>
              <select className="border border-input rounded px-2 py-1 text-sm">
                <option>25</option>
                <option>50</option>
                <option>100</option>
              </select>
            </div>
          </div>

          {/* Right Content */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-8">
              {/* Route Header */}
              {loading ? (
                <div className="text-center py-12 text-muted-foreground">Loading trip details...</div>
              ) : !selectedTrip ? (
                <div className="text-center py-12 text-muted-foreground">Select a trip to view details</div>
              ) : (
                <>
                  <div className="flex items-start justify-between mb-8">
                    <div className="flex-1">
                      <h2 className="text-3xl font-bold mb-2">{selectedTrip.display_name}</h2>
                      <p className="text-muted-foreground mb-4">Status: {selectedTrip.live_status}</p>
                      <div className="text-sm text-muted-foreground mb-4">
                        Booking: {Math.round(selectedTrip.booking_status_percentage)}%
                      </div>

                      <div className="flex gap-8 mb-6">
                        <div className="flex items-center gap-2">
                          <Users className="w-5 h-5 text-blue-600" />
                          <span className="text-sm">{selectedTrip.vehicle ? "1" : "0"} Vehicle</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-5 h-5 text-blue-600" />
                          <span className="text-sm">{selectedTrip.driver ? "1" : "0"} Driver</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className={`w-5 h-5 ${selectedTrip.vehicle && selectedTrip.driver ? "text-emerald-600" : "text-gray-400"}`} />
                          <span className="text-sm">{selectedTrip.vehicle && selectedTrip.driver ? "Ready" : "Not Ready"}</span>
                        </div>
                      </div>

                      <div className="flex gap-3">
                        <button 
                          onClick={() => fetchData()}
                          className="px-6 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
                        >
                          Refresh Data
                        </button>
                        <button className="px-6 py-2 border border-input rounded hover:bg-muted">Manage Bookings</button>
                      </div>
                    </div>

                    <div className="w-80">
                      <div className="bg-gray-200 rounded h-40 flex items-center justify-center mb-4">
                        <MapPin className="w-8 h-8 text-gray-400" />
                      </div>
                      <div className="text-sm space-y-2">
                        {selectedTrip.vehicle && (
                          <div className="p-2 bg-emerald-50 rounded">
                            <p className="font-semibold text-emerald-900">Vehicle Assigned</p>
                            <p className="text-emerald-700">{selectedTrip.vehicle.license_plate}</p>
                            <p className="text-xs text-emerald-600">{selectedTrip.vehicle.type}</p>
                          </div>
                        )}
                        {selectedTrip.driver && (
                          <div className="p-2 bg-blue-50 rounded">
                            <p className="font-semibold text-blue-900">Driver Assigned</p>
                            <p className="text-blue-700">{selectedTrip.driver.name}</p>
                            <p className="text-xs text-blue-600">{selectedTrip.driver.phone_number}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Vehicle Not Assigned */}
                  {!selectedTrip.vehicle && (
                    <div className="bg-gray-50 rounded-lg p-12 text-center">
                      <div className="flex flex-col items-center gap-4">
                        <div className="w-20 h-20 bg-gray-300 rounded-lg flex items-center justify-center">
                          <MapPin className="w-10 h-10 text-gray-400" />
                        </div>
                        <p className="text-gray-500 font-medium">Vehicle not assigned yet</p>
                        <p className="text-sm text-gray-400">Use the chat to assign a vehicle and driver</p>
                      </div>
                    </div>
                  )}
                </>
              )}

              <div className="mt-8 flex items-center justify-between">
                <button className="text-blue-600 hover:underline text-sm flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" /> History
                </button>
                <div className="flex gap-2 text-sm">
                  <button className="px-3 py-1 border border-input rounded hover:bg-muted">1</button>
                  <button className="px-3 py-1 border border-input rounded hover:bg-muted">2</button>
                  <button className="px-3 py-1 border border-input rounded hover:bg-muted">›</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Buttons */}
        <div className="absolute bottom-6 right-6 flex gap-3">
          <button className="px-4 py-2 border border-red-600 text-red-600 rounded hover:bg-red-50">
            Pause Operations
          </button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2">
            Download
          </button>
        </div>
      </div>

      {/* MoviChat Component */}
      <MoviChat currentPage="busDashboard" />
    </>
  )
}

