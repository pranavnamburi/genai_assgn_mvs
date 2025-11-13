"use client"

import { useState, useEffect } from "react"
import { Edit2, MoreVertical, History, Download, ChevronDown } from "lucide-react"
import MoviChat from "../components/MoviChat"
import { apiService } from "../services/api"

export default function ManageRoute() {
  const [activeTab, setActiveTab] = useState("active")
  const [routes, setRoutes] = useState([])
  const [loading, setLoading] = useState(true)

  // Fetch routes on component mount
  useEffect(() => {
    fetchRoutes()
  }, [])

  const fetchRoutes = async () => {
    try {
      setLoading(true)
      const response = await apiService.getRoutes()
      if (response.success) {
        setRoutes(response.data)
      }
    } catch (error) {
      console.error("Error fetching routes:", error)
    } finally {
      setLoading(false)
    }
  }

  // Filter routes based on active tab
  const filteredRoutes = routes.filter(route => {
    if (activeTab === "active") {
      return route.status === "active"
    } else {
      return route.status === "deactivated"
    }
  })

  return (
    <>
      <div className="bg-background min-h-screen">
        {/* Header */}
        <div className="bg-white border-b border-border p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4 flex-1">
              <input
                type="text"
                placeholder="Search route name or ID"
                className="px-3 py-2 border border-input rounded flex-1 max-w-xs"
              />
              <button className="px-3 py-2 border border-input rounded hover:bg-muted text-sm">Filters</button>
            </div>
            <div className="flex items-center gap-3">
              <button className="flex items-center gap-2 px-3 py-2 border border-input rounded hover:bg-muted text-sm">
                <History className="w-4 h-4" />
                History
              </button>
              <button className="flex items-center gap-2 px-3 py-2 border border-input rounded hover:bg-muted text-sm">
                <Download className="w-4 h-4" />
                Download
              </button>
              <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">
                Routes
                <ChevronDown className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab("active")}
              className={`pb-3 border-b-2 font-medium transition ${
                activeTab === "active"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              Active Routes
            </button>
            <button
              onClick={() => setActiveTab("deactivated")}
              className={`pb-3 border-b-2 font-medium transition ${
                activeTab === "deactivated"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              Deactivated Routes
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto bg-white m-4 rounded-lg border border-border">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-6 py-3 text-left text-sm font-semibold text-foreground">Route ID</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-foreground">Route Name</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-foreground">Direction</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-foreground">
                  <div className="flex items-center gap-2">
                    Shift Time
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-foreground">Route Start Point</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-foreground">Route End Point</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-foreground">
                  <div className="flex items-center gap-2">
                    Capacity
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-foreground">
                  <div className="flex items-center gap-2">
                    Allowed Waitlist
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-foreground">Action</th>
              </tr>
            </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="9" className="px-6 py-12 text-center text-muted-foreground">
                  Loading routes...
                </td>
              </tr>
            ) : filteredRoutes.length === 0 ? (
              <tr>
                <td colSpan="9" className="px-6 py-12 text-center text-muted-foreground">
                  No {activeTab} routes found
                </td>
              </tr>
            ) : (
              filteredRoutes.map((route, idx) => (
                <tr key={route.route_id} className="border-b border-border hover:bg-muted/30 transition">
                  <td className="px-6 py-4 text-sm text-foreground">{route.route_id}</td>
                  <td className="px-6 py-4 text-sm text-foreground">{route.route_display_name}</td>
                  <td className="px-6 py-4 text-sm text-foreground">{route.direction}</td>
                  <td className="px-6 py-4 text-sm text-foreground">{route.shift_time}</td>
                  <td className="px-6 py-4 text-sm text-foreground">{route.start_point}</td>
                  <td className="px-6 py-4 text-sm text-foreground">{route.end_point}</td>
                  <td className="px-6 py-4 text-sm text-foreground">
                    <div className="flex items-center gap-2">
                      N/A
                      <button className="p-1 hover:bg-muted rounded">
                        <Edit2 className="w-4 h-4 text-gray-400" />
                      </button>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-foreground">
                    <div className="flex items-center gap-2">
                      N/A
                      <button className="p-1 hover:bg-muted rounded">
                        <Edit2 className="w-4 h-4 text-gray-400" />
                      </button>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <button 
                      onClick={() => alert(`Action menu for route ${route.route_display_name}`)}
                      className="p-1 hover:bg-muted rounded"
                    >
                      <MoreVertical className="w-4 h-4 text-gray-400" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
          </table>
        </div>

        {/* Footer Pagination */}
        <div className="bg-white border-t border-border p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button 
              onClick={fetchRoutes}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium"
            >
              Refresh Data
            </button>
            <span className="text-sm text-muted-foreground">
              Total: {filteredRoutes.length} {activeTab} routes
            </span>
          </div>
          <div className="text-sm text-muted-foreground">
            Showing {filteredRoutes.length} of {routes.length} total routes
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              Active: {routes.filter(r => r.status === 'active').length} | 
              Deactivated: {routes.filter(r => r.status === 'deactivated').length}
            </span>
          </div>
        </div>
      </div>

      {/* MoviChat Component */}
      <MoviChat currentPage="manageRoute" />
    </>
  )
}

