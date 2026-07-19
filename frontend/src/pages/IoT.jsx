import React from "react";
import { Thermometer, Droplets, Gauge, Wind, Radio, AlertCircle } from "lucide-react";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { iotData } from "../mockData";

export default function IoT() {
  const metrics = [
    { label: "Avg Temperature", value: "24.3°C", change: "+1.2°C", icon: Thermometer, color: "text-orange-500", bg: "bg-orange-50" },
    { label: "Avg Humidity", value: "61.4%", change: "+3.1%", icon: Droplets, color: "text-blue-500", bg: "bg-blue-50" },
    { label: "Avg Pressure", value: "1013 hPa", change: "-0.3 hPa", icon: Gauge, color: "text-purple-500", bg: "bg-purple-50" },
    { label: "Water Flow", value: "2.7 m³/s", change: "+0.4 m³/s", icon: Wind, color: "text-cyan-500", bg: "bg-cyan-50" },
    { label: "Sensors Online", value: "1,241/1,247", change: "99.5%", icon: Radio, color: "text-emerald-600", bg: "bg-emerald-50" },
    { label: "Alerts Active", value: "3", change: "!medium", icon: AlertCircle, color: "text-red-500", bg: "bg-red-50" },
  ];

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full scrollbar-hide">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">IoT Monitoring Dashboard</h2>
          <p className="text-sm text-muted-foreground">1,247 sensors across 23 stations · Real-time streaming</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-emerald-700 font-semibold bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl">
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          Live Stream Active
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {metrics.map(m => (
          <div key={m.label} className={`${m.bg} border border-border rounded-2xl p-4`}>
            <m.icon size={20} className={`${m.color} mb-2`} />
            <div className="text-xl font-bold text-foreground font-jakarta">{m.value}</div>
            <div className="text-[10px] text-muted-foreground mt-0.5">{m.label}</div>
            <div className="text-[10px] font-semibold mt-1 text-muted-foreground">{m.change}</div>
          </div>
        ))}
      </div>

      {/* Time series charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-card border border-border rounded-2xl p-5">
          <h3 className="font-bold text-foreground font-jakarta mb-4">Temperature & Humidity (24h)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={iotData.slice(0, 24)}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="h" tick={{ fontSize: 9 }} stroke="none" interval={3} />
              <YAxis tick={{ fontSize: 9 }} stroke="none" />
              <Tooltip contentStyle={{ borderRadius: 10, fontSize: 11 }} />
              <Area type="monotone" dataKey="temp" name="Temp (°C)" stroke="#F97316" fill="rgba(249,115,22,0.1)" strokeWidth={2} />
              <Area type="monotone" dataKey="humidity" name="Humidity (%)" stroke="#3B82F6" fill="rgba(59,130,246,0.08)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-card border border-border rounded-2xl p-5">
          <h3 className="font-bold text-foreground font-jakarta mb-4">Water Flow Rate (24h)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={iotData.slice(0, 24)}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="h" tick={{ fontSize: 9 }} stroke="none" interval={3} />
              <YAxis tick={{ fontSize: 9 }} stroke="none" />
              <Tooltip contentStyle={{ borderRadius: 10, fontSize: 11 }} />
              <Bar dataKey="flow" name="Flow (m³/s)" fill="#0B6E4F" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Alerts */}
      <div className="bg-card border border-border rounded-2xl p-5">
        <h3 className="font-bold text-foreground font-jakarta mb-4">Active Alerts</h3>
        <div className="space-y-3">
          {[
            { id: "SN-142", type: "Temperature Spike", msg: "Temperature exceeded threshold by 4.2°C at Station Marrakech-Nord", severity: "high", time: "28m ago" },
            { id: "SN-089", type: "Data Gap", msg: "No reading received for 47 minutes - possible connectivity issue", severity: "medium", time: "1h ago" },
            { id: "SN-231", type: "Battery Low", msg: "Battery at 8% - scheduled replacement needed within 48h", severity: "low", time: "3h ago" },
          ].map(a => (
            <div key={a.id} className={`flex flex-col sm:flex-row sm:items-start gap-3 p-3 rounded-xl border
              ${a.severity === "high" ? "bg-red-50 border-red-200" : a.severity === "medium" ? "bg-amber-50 border-amber-200" : "bg-blue-50 border-blue-200"}`}>
              <div className="hidden sm:block">
                <AlertCircle size={16} className={a.severity === "high" ? "text-red-500 mt-0.5" : a.severity === "medium" ? "text-amber-500 mt-0.5" : "text-blue-500 mt-0.5"} />
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2 mb-0.5">
                  <div className="sm:hidden"><AlertCircle size={14} className={a.severity === "high" ? "text-red-500" : a.severity === "medium" ? "text-amber-500" : "text-blue-500"} /></div>
                  <span className="text-xs font-bold text-foreground">{a.type}</span>
                  <span className="text-[10px] text-muted-foreground">Sensor {a.id}</span>
                  <span className="text-[10px] text-muted-foreground ml-auto">{a.time}</span>
                </div>
                <p className="text-xs text-muted-foreground">{a.msg}</p>
              </div>
              <button className="text-[10px] font-semibold text-primary bg-white border border-border px-2 py-1 rounded-lg hover:bg-primary hover:text-white transition-colors shrink-0 sm:mt-0 mt-2 self-start sm:self-auto">
                Resolve
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
