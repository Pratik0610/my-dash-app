import dash
from dash import html, dcc, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import datetime
import random
import copy
import numpy as np
from datetime import datetime
from dash.exceptions import PreventUpdate
from abc import ABC, abstractmethod
import copy
import os  # Add this import

# Initialize the app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css",
        "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap"
    ],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True
)
app.title = "KPI Dashboard"
server = app.server

# ====================== KPI CONFIGURATION ======================
TARGETS = {
    "OEE": 85.0,  # Overall Equipment Effectiveness
    "CO2/km": 95.0,  # Emissions per kilometer (g/km)
    "PM Risk": 30.0,  # Preventive Maintenance Risk Index
    "SC Resilience": 0.85,  # Supply Chain Resilience Score
    "TVR": 0.12,  # Throughput Variability Rate
    "Batt Efficiency": 92.5,  # Battery Production Efficiency
    "Chg Utilization": 78.0,  # Charging Station Utilization
    "Security": 0.0  # Security Incidents (0 is ideal)
}

ICONS = {
    "OEE": "speedometer2",
    "CO2/km": "cloud-fog2",
    "PM Risk": "tools",
    "SC Resilience": "truck",
    "TVR": "graph-up",
    "Batt Efficiency": "battery-charging",
    "Chg Utilization": "lightning-charge",
    "Security": "shield-lock"
}

# Production lines configuration
PRODUCTION_LINES = {
    "line1": {
        "name": "Assembly Line 1",
        "color": "#4facfe",
        "icon": "gear",
        "assets": 42,
        "avg_output": 120
    },
    "line2": {
        "name": "Battery Line",
        "color": "#00f2fe",
        "icon": "battery-charging",
        "assets": 28,
        "avg_output": 95
    },
    "line3": {
        "name": "Paint Shop",
        "color": "#ff7de9",
        "icon": "paint-bucket",
        "assets": 18,
        "avg_output": 110
    },
    "line4": {
        "name": "Final Assembly",
        "color": "#ff9a3c",
        "icon": "check2-circle",
        "assets": 35,
        "avg_output": 105
    }
}

# Update frequencies in seconds
UPDATE_FREQUENCIES = {
    "OEE": 30,
    "CO2/km": 120,
    "PM Risk": 300,
    "SC Resilience": 600,
    "TVR": 60,
    "Batt Efficiency": 45,
    "Chg Utilization": 90,
    "Security": 1800
}

# Failure prediction model weights (based on KPI relationships)
FAILURE_WEIGHTS = {
    "OEE": -0.4,
    "PM Risk": 0.7,
    "TVR": 0.5,
    "Batt Efficiency": -0.3,
    "Chg Utilization": 0.2
}

# NEW: Component failure probabilities by line
COMPONENT_FAILURE_PROBABILITIES = {
    "line1": {
        "Robotic Arms": 0.35,
        "Conveyor System": 0.25,
        "Control Electronics": 0.15,
        "Sensor Network": 0.10,
        "Vision Systems": 0.15
    },
    "line2": {
        "Cell Assembly": 0.30,
        "Electrolyte Filling": 0.25,
        "Testing Station": 0.20,
        "Welding System": 0.15,
        "Quality Sensors": 0.10
    },
    "line3": {
        "Paint Sprayers": 0.40,
        "Drying Chamber": 0.20,
        "Ventilation": 0.15,
        "Mixing Systems": 0.15,
        "Filter Units": 0.10
    },
    "line4": {
        "Door Fitting": 0.20,
        "Interior Assembly": 0.25,
        "Electrical Systems": 0.30,
        "Quality Testing": 0.15,
        "Packaging System": 0.10
    }
}

# NEW: Critical component matrix - which KPIs affect which components
COMPONENT_KPI_MATRIX = {
    "Robotic Arms": {"OEE": 0.7, "PM Risk": 0.9, "TVR": 0.5},
    "Conveyor System": {"OEE": 0.8, "PM Risk": 0.6, "TVR": 0.7},
    "Control Electronics": {"OEE": 0.3, "PM Risk": 0.5, "Batt Efficiency": 0.6},
    "Sensor Network": {"OEE": 0.4, "PM Risk": 0.3, "TVR": 0.8},
    "Vision Systems": {"OEE": 0.2, "PM Risk": 0.4, "TVR": 0.3},

    "Cell Assembly": {"OEE": 0.6, "PM Risk": 0.7, "Batt Efficiency": 0.9},
    "Electrolyte Filling": {"OEE": 0.5, "PM Risk": 0.8, "Batt Efficiency": 0.7},
    "Testing Station": {"OEE": 0.3, "PM Risk": 0.4, "Batt Efficiency": 0.5},
    "Welding System": {"OEE": 0.7, "PM Risk": 0.6, "Batt Efficiency": 0.4},
    "Quality Sensors": {"OEE": 0.2, "PM Risk": 0.3, "TVR": 0.6},

    "Paint Sprayers": {"OEE": 0.8, "PM Risk": 0.9, "TVR": 0.4},
    "Drying Chamber": {"OEE": 0.5, "PM Risk": 0.6, "TVR": 0.3},
    "Ventilation": {"OEE": 0.3, "PM Risk": 0.7, "CO2/km": 0.8},
    "Mixing Systems": {"OEE": 0.6, "PM Risk": 0.5, "TVR": 0.7},
    "Filter Units": {"OEE": 0.2, "PM Risk": 0.8, "CO2/km": 0.9},

    "Door Fitting": {"OEE": 0.7, "PM Risk": 0.5, "TVR": 0.4},
    "Interior Assembly": {"OEE": 0.6, "PM Risk": 0.4, "TVR": 0.5},
    "Electrical Systems": {"OEE": 0.5, "PM Risk": 0.7, "Batt Efficiency": 0.6},
    "Quality Testing": {"OEE": 0.3, "PM Risk": 0.2, "TVR": 0.8},
    "Packaging System": {"OEE": 0.4, "PM Risk": 0.3, "TVR": 0.2}
}

# NEW: Maintenance schedule recommendations based on component
MAINTENANCE_RECOMMENDATIONS = {
    "Robotic Arms": "Schedule calibration every 168 hours, full servicing every 720 hours",
    "Conveyor System": "Inspect belts weekly, lubricate bearings every 240 hours",
    "Control Electronics": "Diagnostic tests daily, thermal imaging monthly",
    "Sensor Network": "Calibration every 72 hours, replace sensors every 8,640 hours",
    "Vision Systems": "Clean lenses daily, calibration weekly",

    "Cell Assembly": "Check alignment daily, full service every 360 hours",
    "Electrolyte Filling": "Clean nozzles every 48 hours, pressure test weekly",
    "Testing Station": "Calibrate instruments daily, software update monthly",
    "Welding System": "Replace electrodes every 96 hours, clean/inspect daily",
    "Quality Sensors": "Calibration every 24 hours, validation tests weekly",

    "Paint Sprayers": "Clean nozzles after each shift, replace every 720 hours",
    "Drying Chamber": "Inspect heating elements weekly, clean interior daily",
    "Ventilation": "Replace filters weekly, inspect fans every 720 hours",
    "Mixing Systems": "Clean tanks daily, calibrate sensors every 168 hours",
    "Filter Units": "Replace primary filters every 72 hours, secondary monthly",

    "Door Fitting": "Calibrate alignment tools daily, inspect fixtures weekly",
    "Interior Assembly": "Tool maintenance daily, workstation inspection weekly",
    "Electrical Systems": "Testing after each shift, full diagnostic weekly",
    "Quality Testing": "Calibrate instruments daily, validate test cases weekly",
    "Packaging System": "Inspect packaging materials daily, maintain seals weekly"
}


# ====================== HELPER FUNCTIONS ======================
def get_kpi_status(value, target):
    """Determine status with intelligent thresholds"""
    if target == 0.0:  # Security KPI special case
        if value == 0:
            return "excellent", "#2ECC40", "bi-shield-check"
        return "critical", "#FF4136", "bi-shield-exclamation"

    ratio = value / target
    if ratio >= 1.0:
        return "excellent", "#2ECC40", "bi-arrow-up"
    elif ratio >= 0.9:
        return "good", "#FFDC00", "bi-dash"
    else:
        return "critical", "#FF4136", "bi-arrow-down"


def create_kpi_card(title, value, target, last_updated):
    status, color, trend_icon = get_kpi_status(value, target)

    # Special formatting for Security KPI
    if title == "Security":
        status_text = "0 Incidents" if value == 0 else f"{int(value)} Incident{'s' if value > 1 else ''}"
        target_text = "Target: 0"
        value_text = f"{int(value)}"
    else:
        delta = value - target
        status_text = f"(+{delta:.1f})" if delta >= 0 else f"({delta:.1f})"
        target_text = f"Target: {target}"
        value_text = f"{value:.1f}"

    # Time since last update
    if isinstance(last_updated, (int, float)):
        last_updated = datetime.fromtimestamp(last_updated)
    update_diff = (datetime.now() - last_updated).total_seconds()
    minutes_ago = int(update_diff // 60)
    seconds_ago = int(update_diff % 60)
    update_text = f"Updated: {minutes_ago}m {seconds_ago}s ago"

    return dbc.Card([
        dbc.CardBody([
            html.Div([
                # Status indicator
                html.Div(style={
                    "position": "absolute",
                    "left": 0,
                    "top": 0,
                    "bottom": 0,
                    "width": "4px",
                    "background": color,
                    "borderRadius": "4px 0 0 4px"
                }),

                # Main content
                html.Div([
                    html.I(className=f"bi bi-{ICONS[title]} me-2"),
                    html.Span(title, className="kpi-title")
                ], className="d-flex align-items-center mb-2"),

                html.Div([
                    html.Span(value_text, className="kpi-value me-2"),
                    html.I(className=f"bi {trend_icon}", style={"color": color})
                ], className="d-flex align-items-center mb-1"),

                html.Div([
                    html.Span(target_text, className="me-1"),
                    html.Span(status_text, className="kpi-delta", style={"color": color})
                ], className="kpi-target"),

                html.Div(update_text, className="kpi-update text-muted mt-1")
            ], className="position-relative h-100", style={"paddingLeft": "10px"})
        ])
    ], className="kpi-card shadow-lg", style={
        "background": "linear-gradient(135deg, #1e1e1e, #2a2a2a)",
        "border": "none",
        "minHeight": "170px",  # Increased card height
        "overflow": "hidden"
    })


def generate_kpi_value(kpi_name, current_value, line_id):
    """Generate realistic KPI values with different update behaviors"""
    now = datetime.now()
    new_value = current_value

    # Base values vary by production line
    if line_id == "line1":  # Assembly Line
        base_oe = 82
        base_em = 100
        base_risk = 35
    elif line_id == "line2":  # Battery Line
        base_oe = 88
        base_em = 90
        base_risk = 25
    elif line_id == "line3":  # Paint Shop
        base_oe = 85
        base_em = 110
        base_risk = 40
    else:  # Final Assembly
        base_oe = 87
        base_em = 95
        base_risk = 30

    if kpi_name == "OEE":
        fluctuation = random.gauss(0, 0.8)
        new_value = max(60, min(95, base_oe + fluctuation))
    elif kpi_name == "CO2/km":
        fluctuation = random.gauss(0, 1.5)
        new_value = max(80, min(150, base_em + fluctuation))
    elif kpi_name == "PM Risk":
        if random.random() < 0.05:  # 5% chance of spike
            new_value = min(95, current_value + random.uniform(5, 15))
        else:
            fluctuation = random.gauss(0, 2)
            new_value = max(10, min(95, base_risk + fluctuation))
    elif kpi_name == "SC Resilience":
        fluctuation = random.gauss(0, 0.02)
        new_value = max(0.4, min(0.95, current_value + fluctuation))
    elif kpi_name == "TVR":
        fluctuation = random.gauss(0, 0.005)
        new_value = max(0.05, min(0.3, current_value + fluctuation))
    elif kpi_name == "Batt Efficiency":
        fluctuation = random.gauss(0, 0.3)
        new_value = max(85, min(98, current_value + fluctuation))
    elif kpi_name == "Chg Utilization":
        hour = now.hour
        base_util = 75 + (10 if 8 <= hour < 18 else -5)
        fluctuation = random.gauss(0, 2)
        new_value = max(65, min(90, base_util + fluctuation))
    elif kpi_name == "Security":
        if random.random() < 0.01:  # 1% chance of incident
            new_value = random.randint(1, 2)
        else:
            new_value = 0

    return new_value, now.timestamp()


def generate_initial_data(line_id):
    """Generate realistic starting values for KPIs for a specific line"""
    now = datetime.now()
    return {
        "OEE": random.uniform(80, 90),
        "CO2/km": random.uniform(90, 110),
        "PM Risk": random.uniform(20, 40),
        "SC Resilience": random.uniform(0.75, 0.85),
        "TVR": random.uniform(0.10, 0.15),
        "Batt Efficiency": random.uniform(90, 94),
        "Chg Utilization": 75 + (10 if 8 <= now.hour < 18 else -5),
        "Security": 0,
        "last_updated": {k: now.timestamp() for k in TARGETS.keys()}
    }


# ====================== FACTORY ADAPTER FRAMEWORK ======================
class DataAdapter(ABC):
    def __init__(self, line_id):
        self.line_id = line_id
        self.connected = False

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def read_kpi(self, kpi_name):
        pass

    @abstractmethod
    def get_status(self):
        pass


class VirtualAdapter(DataAdapter):
    """Simulation adapter for development"""

    def __init__(self, line_id):
        super().__init__(line_id)
        # Will be initialized later in callback
        self.last_values = None

    def connect(self):
        self.connected = True
        return True

    def read_kpi(self, kpi_name):
        if self.last_values is None:
            self.last_values = generate_initial_data(self.line_id)

        current_value = self.last_values[kpi_name]
        new_value, timestamp = generate_kpi_value(
            kpi_name,
            current_value,
            self.line_id
        )
        self.last_values[kpi_name] = new_value
        self.last_values["last_updated"][kpi_name] = timestamp
        return new_value, timestamp

    def get_status(self):
        line_name = PRODUCTION_LINES[self.line_id]["name"]
        return {
            "status": "Connected",
            "mode": "Simulation",
            "message": f"Virtual factory data for {line_name}",
            "last_update": datetime.now().strftime("%H:%M:%S")
        }


class OPCUAAdapter(DataAdapter):
    """Stub for real factory connection"""

    def __init__(self, line_id):
        super().__init__(line_id)
        self.last_update = None

    def connect(self):
        try:
            # Security implementation would go here
            # self.client.set_security(SecurityPolicyTypes.Basic256Sha256_SignAndEncrypt)
            self.connected = True
            self.last_update = datetime.now().strftime("%H:%M:%S")
            return True
        except Exception:
            self.connected = False
            return False

    def read_kpi(self, kpi_name):
        if not self.connected:
            self.connect()

        # Simulate reading from real equipment
        value = random.uniform(80, 95)  # Placeholder
        return value, datetime.now().timestamp()

    def get_status(self):
        status = "Connected" if self.connected else "Disconnected"
        return {
            "status": status,
            "mode": "Production",
            "message": "OPC-UA to factory equipment",
            "last_update": self.last_update or "Never"
        }


# Initialize adapters for all lines (using virtual for now)
ADAPTERS = {
    line_id: VirtualAdapter(line_id)
    for line_id in PRODUCTION_LINES
}

# Initialize adapters for all lines (using virtual for now)
ADAPTERS = {
    line_id: VirtualAdapter(line_id)
    for line_id in PRODUCTION_LINES
}

# NEW: Adapter management system
ADAPTER_INSTANCES = {}
def get_adapter(line_id, mode):
    """Get or create adapter instance for a line in specified mode"""
    if line_id not in ADAPTER_INSTANCES:
        ADAPTER_INSTANCES[line_id] = {
            'virtual': VirtualAdapter(line_id),
            'production': OPCUAAdapter(line_id)
        }
    return ADAPTER_INSTANCES[line_id][mode]

# ====================== PREDICTIVE ANALYTICS FUNCTIONS ======================
def predict_kpi_trend(current_value, target):
    """Predict KPI trend for next 24 hours based on current trajectory"""
    # Simple linear projection with random fluctuation
    if current_value >= target:
        trend = current_value - random.uniform(0.1, 0.5)
    else:
        trend = current_value + random.uniform(0.2, 1.0)

    # Cap values within reasonable range
    return max(target * 0.7, min(target * 1.3, trend))


def calculate_failure_probability(data):
    """Calculate machine failure probability based on multiple KPIs"""
    # Weighted combination of relevant KPIs
    score = 0
    total_weight = 0

    for kpi, weight in FAILURE_WEIGHTS.items():
        # Normalize KPI values to 0-1 range
        normalized = data[kpi] / TARGETS[kpi] if TARGETS[kpi] > 0 else data[kpi]
        score += normalized * weight
        total_weight += abs(weight)

    # Scale to 0-100 probability
    probability = max(0, min(100, (score / total_weight) * 100))
    return probability


# NEW: Enhanced component failure prediction function
def predict_component_failures(data, line_id):
    """Calculate specific component failure probabilities based on KPIs"""
    component_risks = {}
    base_components = COMPONENT_FAILURE_PROBABILITIES[line_id]

    for component, base_prob in base_components.items():
        # Get KPI influences for this component
        kpi_influences = COMPONENT_KPI_MATRIX.get(component, {})

        # Calculate weighted risk based on current KPI values
        if kpi_influences:
            risk_modifier = 0
            for kpi, influence in kpi_influences.items():
                # Compare current KPI to target - higher risk if worse performance
                if kpi in data and kpi in TARGETS:
                    if TARGETS[kpi] == 0:  # Handle security case
                        kpi_risk = data[kpi] * 10  # Each incident adds significant risk
                    else:
                        ratio = data[kpi] / TARGETS[kpi]
                        # Invert ratio for metrics where lower is better (PM Risk, CO2, TVR)
                        if kpi in ["PM Risk", "CO2/km", "TVR"]:
                            kpi_risk = (ratio * 50) if ratio > 1 else 0
                        else:  # For metrics where higher is better (OEE, SC Resilience, etc.)
                            kpi_risk = 50 * (1 - ratio) if ratio < 1 else 0

                    risk_modifier += kpi_risk * influence

            # Calculate final risk with modifiers
            final_risk = base_prob * 100 * (1 + risk_modifier / 100)
            component_risks[component] = min(99.9, max(5, final_risk))  # Cap between 5% and 99.9%
        else:
            # Fallback to base probability if no influences defined
            component_risks[component] = base_prob * 100

    # Sort by risk (highest first)
    sorted_risks = sorted(component_risks.items(), key=lambda x: x[1], reverse=True)

    # Calculate hours until likely failure based on risk
    failure_predictions = []
    for component, risk in sorted_risks:
        # Higher risk = shorter time to failure
        hours_to_failure = int(max(1, (100 - risk) * 1.2))
        failure_predictions.append({
            "component": component,
            "risk": risk,
            "hours": hours_to_failure,
            "recommendation": MAINTENANCE_RECOMMENDATIONS.get(component, "Schedule maintenance check")
        })

    return failure_predictions


def predict_bottlenecks(utilization):
    """Identify predicted resource bottlenecks"""
    bottlenecks = []
    for i, util in enumerate(utilization):
        # Project utilization for next shift (8 hours)
        projected = util * (1 + random.uniform(0.05, 0.15))

        if projected > 85:
            bottlenecks.append({
                "resource": i,
                "current": util,
                "projected": projected,
                "severity": min(100, (projected - 85) * 5)  # Scale severity
            })
    return bottlenecks


def calculate_optimal_maintenance(data, risk_levels):
    """Calculate optimal maintenance windows based on cost-risk analysis"""
    optimal_windows = []
    current_risk = data["PM Risk"]
    oee_value = data["OEE"]

    for day, risk in enumerate(risk_levels):
        # Calculate cost of maintenance at this risk level
        if risk < 40:
            cost = 2000
        elif risk < 70:
            cost = 4000
        else:
            cost = 12000

        # Opportunity cost (lost production)
        production_loss = (100 - oee_value) * 100  # Simplified model

        # Total cost
        total_cost = cost + production_loss

        # Optimal if in low-risk and low-production-loss window
        if risk < 50 and production_loss < 3000:
            optimal_windows.append(day)

    return optimal_windows


# ====================== APP LAYOUT ======================
app.layout = dbc.Container(fluid=True, children=[
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='kpi-data', data=generate_initial_data('line1')),
    dcc.Interval(id='interval', interval=5 * 1000, n_intervals=0),
    dcc.Store(id='fullscreen-store', data={'is_fullscreen': False}),

    # NEW: Add this store for tracking adapter modes
    dcc.Store(
        id='adapter-modes-store',
        data={line_id: 'virtual' for line_id in PRODUCTION_LINES}
    ),

    # Navigation Sidebar
    dbc.Row([
        dbc.Col(
            dbc.Nav(
                [
                    dbc.NavLink(
                        [
                            html.I(className="bi bi-speedometer2 me-2"),
                            "Dashboard"
                        ],
                        href="/",
                        active="exact",
                        className="py-3"
                    ),
                    dbc.NavLink(
                        [
                            html.I(className="bi bi-graph-up me-2"),
                            "Production Analytics"
                        ],
                        href="/analytics",
                        active="exact",
                        className="py-3"
                    )
                ],
                vertical=True,
                pills=True,
                className="sidebar bg-dark"
            ),
            width=2,
            className="p-0"
        ),

        # Main Content
        dbc.Col(
            id="main-content",
            children=[
                # Header
dbc.Row([
    dbc.Col(
        html.Div([
            html.H1("KPI Dashboard", className="display-4 fw-bold mb-0"),
            html.Small("Real-time Production Monitoring", className="text-muted"),
            dbc.Select(
                id="line-selector",
                options=[
                    {"label": f"{PRODUCTION_LINES[line]['name']}", "value": line}
                    for line in PRODUCTION_LINES
                ],
                value="line1",
                className="mt-2 w-100",
                size="sm"
            )
        ]),
        width=8  # Changed from 10 to 8
    ),
    dbc.Col(
        html.Div([  # New wrapper Div
            # Production mode toggle switch
            dbc.Switch(
                id="production-mode-toggle",
                label="Production Mode",
                value=False,
                className="mb-2"  # Margin bottom
            ),
            # Existing fullscreen button
            dbc.Button(
                html.I(className="bi bi-arrows-fullscreen"),
                id="fullscreen-btn",
                color="link",
                className="p-2",  # Removed mt-4
                style={"zIndex": 1000}
            )
        ], className="d-flex flex-column align-items-end"),  # Vertical alignment
        width=4,  # Changed from 2 to 4
        className="d-flex align-items-center justify-content-end"
    )
], className="mb-4 p-3 header-bg"),

                # Page Content
                html.Div(id='page-content', className="mt-3"),

                # Footer
                dbc.Row(dbc.Col(
                    html.Div([
                        html.Hr(className="mb-2"),
                        html.P([
                            "Designed by ",
                            html.Strong("Pratik Sonavane",
                                        style={"background": "linear-gradient(45deg, #4facfe, #00f2fe)",
                                               "-webkit-background-clip": "text",
                                               "color": "transparent"}),
                            " - Production Intelligence System"
                        ], className="text-center"),
                        html.P("© 2025 AUTOVISTA - Real-time Production Monitoring",
                               className="text-center text-muted")
                    ], className="p-3")
                ))
            ],
            width=10,
            style={"padding": "0 20px", "height": "100vh"}
        )
    ], className="g-0"),
], style={
    "backgroundColor": "#0d1117",
    "color": "#f0f6fc",
    "fontFamily": "'Roboto', sans-serif",
    "minHeight": "100vh",
    "margin": "0",
    "padding": "0"
})


# ====================== PAGE LAYOUTS ======================
def dashboard_layout():
    return html.Div([
        # KPI Grid with unique IDs and loading indicators
        dbc.Row([
            dbc.Col(id='kpi-card-oee', width=3, className="mb-3"),
            dbc.Col(id='kpi-card-co2', width=3, className="mb-3"),
            dbc.Col(id='kpi-card-pm-risk', width=3, className="mb-3"),
            dbc.Col(id='kpi-card-sc-resilience', width=3, className="mb-3"),
        ], className="g-3 mb-2"),

        dbc.Row([
            dbc.Col(id='kpi-card-tvr', width=3, className="mb-3"),
            dbc.Col(id='kpi-card-batt-eff', width=3, className="mb-3"),
            dbc.Col(id='kpi-card-chg-util', width=3, className="mb-3"),
            dbc.Col(id='kpi-card-security', width=3, className="mb-3"),
        ], className="g-3 mb-4"),

        # Decision Insights Section with initial content
        dbc.Row(
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Performance Insights & Recommendations", className="fw-bold fs-5"),
                    dbc.CardBody(
                        html.Div(id="dashboard-insights", children=[
                            dbc.Alert("Loading insights...", color="info")
                        ]),
                        style={"maxHeight": "300px", "overflowY": "auto"}
                    )
                ], className="shadow-lg")
            )
        ),

        # Factory Connection Status Panel
        dbc.Row(
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Factory Connection Status"),
                    dbc.CardBody(id="factory-status-panel")
                ], className="mt-3 shadow-sm")
            )
        )
    ])


def analytics_layout():
    return html.Div([
        # First row: Performance Forecast (full width)
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="bi bi-graph-up me-2"),
                        "Performance Forecast"
                    ], className="fw-bold fs-5 d-flex align-items-center"),
                    dbc.CardBody(
                        dcc.Graph(id="efficiency-forecast", config={"displayModeBar": False},
                                  style={"height": "500px"})  # Increased height
                    )
                ], className="shadow-lg mb-4", style={
                    "background": "linear-gradient(135deg, #1a1a2e, #16213e)",
                    "border": "1px solid #2a3a5a"
                }),
                width=12
            )
        ]),

        # Second row: Production Trends and Resource Utilization (half width each)
        dbc.Row([
            # Production Trends
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="bi bi-speedometer me-2"),
                        "Production Trends"
                    ], className="fw-bold fs-5 d-flex align-items-center"),
                    dbc.CardBody(
                        dcc.Graph(id="production-trends", config={"displayModeBar": False},
                                  style={"height": "400px"})
                    )
                ], className="shadow-lg mb-4", style={
                    "background": "linear-gradient(135deg, #1a1a2e, #0f3460)",
                    "border": "1px solid #2a3a5a"
                }),
                width=6
            ),

            # Resource Utilization
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="bi bi-cpu me-2"),
                        "Resource Utilization"
                    ], className="fw-bold fs-5 d-flex align-items-center"),
                    dbc.CardBody(
                        dcc.Graph(id="resource-utilization", config={"displayModeBar": False},
                                  style={"height": "400px"})
                    )
                ], className="shadow-lg mb-4", style={
                    "background": "linear-gradient(135deg, #1a1a2e, #0f3460)",
                    "border": "1px solid #2a3a5a"
                }),
                width=6
            )
        ]),

        # Third row: Predictive Maintenance (full width)
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="bi bi-tools me-2"),
                        "Predictive Maintenance Planner"
                    ], className="fw-bold fs-5 d-flex align-items-center"),
                    dbc.CardBody([
                        html.Div(id="maintenance-forecast", className="maintenance-planner")
                    ], style={"padding": "20px"})
                ], className="shadow-lg mb-4", style={
                    "background": "linear-gradient(135deg, #1a1a2e, #1b1b2f)",
                    "border": "1px solid #2a3a5a"
                }),
                width=12
            )
        ]),

        # Fourth row: Component Failure Prediction (full width)
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="bi bi-exclamation-triangle me-2"),
                        "Component Failure Prediction"
                    ], className="fw-bold fs-5 d-flex align-items-center"),
                    dbc.CardBody(
                        html.Div(id="anomaly-detection", className="component-failure")
                    )
                ], className="shadow-lg", style={
                    "background": "linear-gradient(135deg, #1a1a2e, #1b1b2f)",
                    "border": "1px solid #2a3a5a"
                }),
                width=12
            )
        ])
    ])


# ====================== CALLBACKS ======================
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def render_page_content(pathname):
    if pathname == "/":
        return dashboard_layout()
    elif pathname == "/analytics":
        return analytics_layout()
    return dashboard_layout()


@app.callback(
    Output('kpi-data', 'data'),
    [Input('interval', 'n_intervals'),
     Input('line-selector', 'value')],
    [State('kpi-data', 'data'),
     State('adapter-modes-store', 'data')]  # Add adapter modes state
)
def update_kpi_data(n, line_id, current_data, adapter_modes):
    # Get mode for current line
    mode = adapter_modes.get(line_id, 'virtual')

    # Get adapter for selected production line and mode
    adapter = get_adapter(line_id, mode)

    # If we don't have data yet, initialize from adapter
    if current_data is None:
        # For the first run, we need to simulate initial data
        # We'll read all KPIs to initialize
        initial_data = generate_initial_data(line_id)
        # But we also want to set the adapter's last_values
        if hasattr(adapter, 'last_values'):
            adapter.last_values = copy.deepcopy(initial_data)
        return initial_data

    # Create a deep copy to avoid mutation issues
    new_data = copy.deepcopy(current_data)

    # Update KPIs using the adapter
    now = datetime.now().timestamp()
    for kpi, freq in UPDATE_FREQUENCIES.items():
        last_update = new_data["last_updated"][kpi]
        time_diff = now - last_update

        if time_diff >= freq:
            try:
                # Use the adapter to get updated value
                new_value, update_time = adapter.read_kpi(kpi)
                new_data[kpi] = new_value
                new_data["last_updated"][kpi] = update_time

                # For virtual adapter, update its internal state
                if mode == 'virtual' and hasattr(adapter, 'last_values'):
                    adapter.last_values[kpi] = new_value
                    adapter.last_values["last_updated"][kpi] = update_time

            except Exception as e:
                print(f"Error updating {kpi}: {str(e)}")
                # If there's an error, just keep the current value
                # but update the timestamp to now to avoid repeated errors
                new_data["last_updated"][kpi] = now

    return new_data


# Create callbacks for each KPI card
kpi_callbacks = {
    "OEE": "kpi-card-oee",
    "CO2/km": "kpi-card-co2",
    "PM Risk": "kpi-card-pm-risk",
    "SC Resilience": "kpi-card-sc-resilience",
    "TVR": "kpi-card-tvr",
    "Batt Efficiency": "kpi-card-batt-eff",
    "Chg Utilization": "kpi-card-chg-util",
    "Security": "kpi-card-security"
}

for kpi, card_id in kpi_callbacks.items():
    @app.callback(
        Output(card_id, 'children'),
        [Input('kpi-data', 'data')]
    )
    def update_card(data, kpi=kpi):
        if data is None:
            return create_kpi_card(kpi, 0, TARGETS[kpi], datetime.now())
        last_updated = data["last_updated"].get(kpi, datetime.now().timestamp())
        return create_kpi_card(kpi, data[kpi], TARGETS[kpi], last_updated)


@app.callback(
    Output('dashboard-insights', 'children'),
    [Input('kpi-data', 'data'),
     Input('line-selector', 'value'),
     Input('url', 'pathname')],
    prevent_initial_call=False
)
def update_dashboard_insights(data, line_id, pathname):
    # Only update if we're on the dashboard page
    if pathname != "/":
        raise PreventUpdate

    if data is None:
        return dbc.Alert("Waiting for initial data...", color="warning")

    line_info = PRODUCTION_LINES[line_id]

    # Performance insights - DECISION-ORIENTED DESIGN
    insights = []

    # Calculate all statuses first
    statuses = {}
    for kpi in TARGETS:
        status, color, _ = get_kpi_status(data[kpi], TARGETS[kpi])
        statuses[kpi] = {"status": status, "color": color, "value": data[kpi]}

    # Critical alerts
    critical_insights = []
    for kpi in statuses:
        if statuses[kpi]["status"] == "critical":
            critical_insights.append(
                dbc.Alert(
                    [
                        html.Div([
                            html.I(className=f"bi bi-{ICONS[kpi]} me-2"),
                            html.Span(f"{kpi}: ", className="fw-bold"),
                            html.Span(f"{statuses[kpi]['value']:.1f}"),
                            dbc.Badge("CRITICAL", color="danger", className="ms-2")
                        ], className="d-flex align-items-center"),
                        html.Div(
                            f"Action: {get_action_recommendation(kpi)}",
                            className="text-dark mt-1 small"
                        )
                    ],
                    color="danger",
                    className="mb-3 p-3"
                )
            )

    # Warning alerts
    warning_insights = []
    for kpi in statuses:
        if statuses[kpi]["status"] == "good":
            warning_insights.append(
                dbc.Alert(
                    [
                        html.Div([
                            html.I(className=f"bi bi-{ICONS[kpi]} me-2"),
                            html.Span(f"{kpi}: ", className="fw-bold"),
                            html.Span(f"{statuses[kpi]['value']:.1f}"),
                            dbc.Badge("WARNING", color="warning", className="ms-2")
                        ], className="d-flex align-items-center"),
                        html.Div(
                            f"Action: {get_action_recommendation(kpi)}",
                            className="text-dark mt-1 small"
                        )
                    ],
                    color="warning",
                    className="mb-3 p-3"
                )
            )

    # Positive statuses
    positive_insights = []
    for kpi in statuses:
        if statuses[kpi]["status"] == "excellent":
            positive_insights.append(
                dbc.Alert(
                    [
                        html.Div([
                            html.I(className=f"bi bi-{ICONS[kpi]} me-2"),
                            html.Span(f"{kpi}: ", className="fw-bold"),
                            html.Span(f"{statuses[kpi]['value']:.1f}"),
                            dbc.Badge("OPTIMAL", color="success", className="ms-2")
                        ], className="d-flex align-items-center"),
                        html.Div("Maintain current performance", className="text-dark mt-1 small")
                    ],
                    color="success",
                    className="mb-3 p-3"
                )
            )

    # Combine insights - critical first, then warnings, then positives
    all_insights = critical_insights + warning_insights + positive_insights

    # If no insights, show a success message
    if not all_insights:
        all_insights = [
            dbc.Alert(
                [
                    html.Div([
                        html.I(className="bi bi-check-circle me-2"),
                        html.Span("All KPIs are performing optimally", className="fw-bold")
                    ], className="d-flex align-items-center"),
                    html.Div("Continue monitoring for potential improvements", className="text-dark mt-1 small")
                ],
                color="success",
                className="mb-3 p-3"
            )
        ]

    return all_insights


def get_action_recommendation(kpi):
    """Return decision-focused recommendations for each KPI"""
    recommendations = {
        "OEE": "Optimize workflow to eliminate bottlenecks and reduce downtime",
        "CO2/km": "Implement energy-efficient manufacturing processes and reduce waste",
        "PM Risk": "Schedule preventive maintenance within 24 hours to avoid failures",
        "SC Resilience": "Diversify suppliers and increase inventory buffers",
        "TVR": "Analyze production variability sources and standardize processes",
        "Batt Efficiency": "Optimize battery cell production parameters and quality control",
        "Chg Utilization": "Reallocate charging stations based on demand patterns",
        "Security": "Investigate incidents immediately and strengthen security protocols"
    }
    return recommendations.get(kpi, "Review performance metrics and take corrective action")


# Full-screen toggle functionality
app.clientside_callback(
    """
    function(n_clicks, is_fullscreen_data) {
        // Return early if no click
        if (!n_clicks) {
            return is_fullscreen_data || {'is_fullscreen': false};
        }

        // Default to current state if available
        let is_fullscreen = false;
        if (is_fullscreen_data && typeof is_fullscreen_data === 'object') {
            is_fullscreen = !!is_fullscreen_data.is_fullscreen;
        }

        // Try to toggle fullscreen
        try {
            const elem = document.getElementById('main-content');

            // Check if already in fullscreen
            const isFullScreen = !!(
                document.fullscreenElement || 
                document.webkitFullscreenElement || 
                document.mozFullScreenElement ||
                document.msFullscreenElement
            );

            if (!isFullScreen) {
                // Enter fullscreen
                if (elem.requestFullscreen) {
                    elem.requestFullscreen();
                } else if (elem.mozRequestFullScreen) {
                    elem.mozRequestFullScreen();
                } else if (elem.webkitRequestFullscreen) {
                    elem.webkitRequestFullscreen();
                } else if (elem.msRequestFullscreen) {
                    elem.msRequestFullscreen();
                }
                return {'is_fullscreen': true};
            } else {
                // Exit fullscreen
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.mozCancelFullScreen) {
                    document.mozCancelFullScreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                } else if (document.msExitFullscreen) {
                    document.msExitFullscreen();
                }
                return {'is_fullscreen': false};
            }
        } catch (e) {
            console.error("Fullscreen error:", e);
            return {'is_fullscreen': false};
        }
    }
    """,
    Output('fullscreen-store', 'data'),
    Input('fullscreen-btn', 'n_clicks'),
    State('fullscreen-store', 'data')
)


@app.callback(
    Output('fullscreen-btn', 'children'),
    Input('fullscreen-store', 'data')
)
def update_fullscreen_button(data):
    if data and data.get('is_fullscreen', False):
        return html.I(className="bi bi-fullscreen-exit")
    return html.I(className="bi bi-fullscreen")


@app.callback(
    [Output('production-trends', 'figure'),
     Output('efficiency-forecast', 'figure'),
     Output('resource-utilization', 'figure'),
     Output('maintenance-forecast', 'children'),
     Output('anomaly-detection', 'children')],
    [Input('kpi-data', 'data'),
     Input('line-selector', 'value'),
     Input('url', 'pathname')],
    prevent_initial_call=True
)
def update_analytics_page(data, line_id, pathname):
    # Only update if we're on the analytics page
    if pathname != "/analytics":
        raise PreventUpdate

    # Return placeholder if no data
    if data is None:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            template="plotly_dark",
            height=300,
            title="Loading data...",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        anomaly_placeholder = dbc.Alert("Loading data...", color="info")
        maintenance_placeholder = dbc.Alert("Loading maintenance data...", color="info")
        return empty_fig, empty_fig, empty_fig, maintenance_placeholder, anomaly_placeholder

    try:
        line_info = PRODUCTION_LINES[line_id]

        # 1. Production Trends with Prediction
        categories = list(TARGETS.keys())
        fig_trends = go.Figure()

        # Add current values
        fig_trends.add_trace(go.Scatterpolar(
            r=[data[k] for k in categories],
            theta=categories,
            fill='toself',
            name='Current',
            line=dict(color=line_info["color"], width=2)
        ))

        # Add target values
        fig_trends.add_trace(go.Scatterpolar(
            r=[TARGETS[k] for k in categories],
            theta=categories,
            fill='toself',
            name='Target',
            line=dict(color='#00f2fe', dash='dash'),
            opacity=0.7
        ))

        # Add predicted values (24-hour projection)
        predicted_values = [predict_kpi_trend(data[k], TARGETS[k]) for k in categories]
        fig_trends.add_trace(go.Scatterpolar(
            r=predicted_values,
            theta=categories,
            fill='toself',
            name='Predicted (24h)',
            line=dict(color='#ff7de9', dash='dot'),
            opacity=0.9
        ))

        fig_trends.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=9)  # Smaller font size
                ),
                angularaxis=dict(
                    tickfont=dict(size=9),  # Smaller font size
                    gridcolor='rgba(255,255,255,0.1)'  # Added grid
                )
            ),
            showlegend=True,
            template="plotly_dark",
            height=400,
            title=dict(
                text=f"{line_info['name']} Performance Trends",
                y=0.98,  # Position title near the top of the plot area
                x=0.5,
                xanchor='center',
                yanchor='top'
            ),
            margin=dict(l=40, r=40, t=100, b=40),  # Increased top margin to make space for title and legend
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.15,  # Position legend above the plot area, relative to the top of the plot
                xanchor="center",
                x=0.5,  # Center legend horizontally
                font=dict(size=10),
                bgcolor='rgba(0,0,0,0.5)',  # Add a slight background for readability
                bordercolor='rgba(255,255,255,0.1)',
                borderwidth=1
            )
        )



              # 2. ENHANCED Performance Forecast with Failure Risk - BIGGER SIZE
        hours = list(range(0, 25, 2))  # More data points for better visibility
        production = [100 * (0.98 ** h) for h in hours]
        efficiency = [data["OEE"] * (0.992 ** h) for h in hours]

        # Calculate failure probability (TEMPORARY: FORCED HIGH VALUES FOR DEBUGGING)
        # This will ensure critical points are always generated for testing the marker visibility
        # We start at 40 and increase by 3 for each 2-hour step, ensuring it crosses 60 and 70
        failure_prob = [40 + (h * 3) for h in hours]
        failure_prob = [min(100, p) for p in failure_prob]  # Cap at 100%

        fig_forecast = go.Figure()

        # Production trace (Blue) - Associated with yaxis (primary left)
        fig_forecast.add_trace(go.Scatter(
            x=hours, y=production,
            mode='lines+markers',
            name='Units Produced',
            line=dict(color='#6495ED', width=3),  # Cornflower Blue
            marker=dict(symbol='circle', size=7),
            yaxis='y' # Primary y-axis
        ))

        # Efficiency trace (Purple) - Associated with yaxis2 (right)
        fig_forecast.add_trace(go.Scatter(
            x=hours, y=efficiency,
            mode='lines+markers',
            name='OEE Efficiency',
            line=dict(color='#BA55D3', width=3),  # Medium Orchid
            marker=dict(symbol='square', size=7),
            yaxis='y2' # Right y-axis
        ))

        # Failure probability trace (Crimson, NO FILL) - Associated with yaxis2 (right)
        fig_forecast.add_trace(go.Scatter(
            x=hours, y=failure_prob,
            mode='lines',
            name='Failure Risk',
            line=dict(color='#DC143C', width=3, dash='dot'),  # Crimson
            yaxis='y2' # Right y-axis
        ))

        # Add predicted failure points
        critical_points = []
        for i, prob in enumerate(failure_prob):
            if prob > 60: # Threshold for critical points
                critical_points.append((hours[i], prob))

        # print(f"DEBUG: critical_points = {critical_points}") # Diagnostic print - keep commented for now

        if critical_points: # Only add trace if there are critical points
            x_vals, y_vals = zip(*critical_points)
            fig_forecast.add_trace(go.Scatter(
                x=x_vals, y=y_vals,
                mode='markers',
                name='Critical Risk Point',
                marker=dict(
                    symbol='circle', # Changed to solid circle
                    size=12, # Slightly smaller but solid
                    color='#FFD700', # Solid gold color for high visibility
                    line=dict(width=1, color='white') # Thin white border for definition
                ),
                yaxis='y2' # Associated with the right y-axis
            ))

        # Add risk bands with improved visibility and cleaner colors
        fig_forecast.add_hrect(
            y0=0, y1=30,
            fillcolor="rgba(30, 144, 255, 0.1)", # Dodger Blue subtle
            layer="below",
            line_width=0,
            annotation_text="Low Risk",
            annotation_position="top left",
            annotation_font_size=10,
            annotation_font_color="#ffffff"
        )
        fig_forecast.add_hrect(
            y0=30, y1=70,
            fillcolor="rgba(255, 165, 0, 0.1)", # Orange subtle
            layer="below",
            line_width=0,
            annotation_text="Medium Risk",
            annotation_position="top left",
            annotation_font_size=10,
            annotation_font_color="#ffffff"
        )
        fig_forecast.add_hrect(
            y0=70, y1=100,
            fillcolor="rgba(255, 69, 0, 0.1)", # Red-Orange subtle
            layer="below",
            line_width=0,
            annotation_text="High Risk",
            annotation_position="top left",
            annotation_font_size=10,
            annotation_font_color="#ffffff"
        )

        fig_forecast.update_layout(
            title=dict(
                text='Production Forecast with Failure Risk',
                y=0.98,  # Position title at the very top
                x=0.5,
                xanchor='center',
                font=dict(size=16)
            ),
            xaxis_title='Hours Ahead',
            yaxis=dict(
                title='Units Produced',
                color='#6495ED',
                range=[0, max(production) * 1.1]
            ),
            yaxis2=dict(
                title='OEE (%) / Failure Risk (%)',
                overlaying='y',
                side='right',
                color='#FFFFFF',
                range=[0, 100],
                position=1.0,
                showgrid=False
            ),
            template="plotly_dark",
            height=450,  # Increased height
            margin=dict(l=20, r=120, t=100, b=40),  # Increased top margin
            paper_bgcolor='black',
            plot_bgcolor='black',
            legend=dict(
                orientation="h",
                y=1.1,  # Position legend ABOVE the plot area
                yanchor="bottom",  # Anchor to bottom of legend so it sits just above the plot
                x=0.5,  # Center legend horizontally
                xanchor="center",
                font=dict(size=10),
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='rgba(255,255,255,0.1)',
                borderwidth=1,
                itemsizing='constant',
                itemwidth=40
            )
        )

        # 3. Resource Utilization with Bottleneck Prediction
        resources = ['Robots', 'Personnel', 'Energy', 'Materials', 'Machines']
        utilization = [random.randint(60, 95) for _ in resources]

        # Calculate projected utilization
        projected = [u * (1 + random.uniform(0.05, 0.15)) for u in utilization]
        projected = [min(110, p) for p in projected]  # Cap at 110%

        # Generate bottlenecks for anomaly detection
        bottlenecks = predict_bottlenecks(utilization)

        fig_util = go.Figure()

        # Current utilization bars
        fig_util.add_trace(go.Bar(
            x=resources,
            y=utilization,
            name='Current',
            marker_color='#4facfe'
        ))

        # Projected utilization bars
        fig_util.add_trace(go.Bar(
            x=resources,
            y=[max(0, p - u) for u, p in zip(utilization, projected)],
            name='Projected Increase',
            marker_color='#ff7de9',
            text=[f"{p:.0f}%" for p in projected],
            textposition='outside',
            base=utilization
        ))

        # Add threshold line
        # Improved threshold line
        # Lighter threshold line with reduced opacity
        # White threshold line with lower opacity
        # White threshold line with consistent opacity for line and text
        fig_util.add_hline(
            y=85,
            line=dict(
                color="#FFFFFF",  # White line
                width=2,
                dash="dash"
            ),
            opacity=0.3,  # Line opacity at 0.3
            annotation=dict(
                text="Bottleneck Threshold",
                font=dict(
                    color="rgba(255,255,255,0.3)",  # White text with 0.3 opacity
                    size=12,
                    family="Arial"
                ),
                bgcolor="rgba(0,0,0,0.2)",  # Reduced background opacity
                bordercolor="rgba(255,255,255,0.3)",  # Border with 0.3 opacity
                borderwidth=1,
                borderpad=4
            ),
            annotation_position="top right"
        )

        fig_util.update_layout(
            barmode='stack',
            title=dict(
                text='Resource Utilization with Projection',
                y=0.98,  # Position title near the top of the plot area
                x=0.5,
                xanchor='center',
                yanchor='top'
            ),
            xaxis_title='Resource Type',
            yaxis_title='Utilization (%)',
            template="plotly_dark",
            height=400,
            yaxis_range=[0, 110],
            margin=dict(l=50, r=20, t=100, b=100),  # Increased top margin to make space for title and legend
            xaxis=dict(
                tickangle=-30,  # Rotate labels
                tickfont=dict(size=10)
            ),
            bargap=0.4,  # Space between bars
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.15,  # Position legend above the plot area, relative to the top of the plot
                xanchor="center",
                x=0.5,  # Center legend horizontally
                font=dict(size=10),
                bgcolor='rgba(0,0,0,0.5)',  # Add a slight background for readability
                bordercolor='rgba(255,255,255,0.1)',
                borderwidth=1
            )
        )



        # 4. COMPLETELY REDESIGNED Predictive Maintenance planner
        # Get component failure predictions
        failure_predictions = predict_component_failures(data, line_id)

        # Find the most critical components
        critical_components = [p for p in failure_predictions if p["risk"] > 50]
        warning_components = [p for p in failure_predictions if 30 <= p["risk"] <= 50]
        normal_components = [p for p in failure_predictions if p["risk"] < 30]

        # Create maintenance timeline cards
        maintenance_timeline = html.Div([
            # Maintenance timing header
            html.Div([
                html.H5("Maintenance Timeline", className="mb-3 text-center"),
                html.Div([
                    html.Span("Next 24 Hours", className="badge bg-danger me-2"),
                    html.Span("24-72 Hours", className="badge bg-warning me-2"),
                    html.Span("72+ Hours", className="badge bg-success")
                ], className="text-center mb-3")
            ]),

            # Timeline visualization
            html.Div([
                # Critical components (need attention in 24h)
                html.Div([
                    html.H6("Critical Priority", className="text-danger mb-3"),
                    html.Div([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.Span(c["component"], className="fw-bold"),
                                    dbc.Badge(f"{c['risk']:.1f}% Risk",
                                              color="danger",
                                              className="ms-auto")
                                ], className="d-flex justify-content-between align-items-center mb-2"),

                                dbc.Progress(
                                    value=c["risk"],
                                    color="danger",
                                    className="mb-2",
                                    style={"height": "8px"}
                                ),

                                html.Div([
                                    html.Small(f"Hours until failure: {c['hours']}"),
                                    html.Small([
                                        html.I(className="bi bi-tools me-1"),
                                        "Action required: Immediate"
                                    ], className="d-block mt-1")
                                ], className="small text-muted")
                            ])
                        ], className="mb-2 border-danger") for c in critical_components
                    ]) if critical_components else
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-check-circle me-2 text-success"),
                                html.Span("No critical components", className="text-muted")
                            ], className="d-flex align-items-center justify-content-center")
                        ])
                    ], className="mb-2")
                ], className="mb-4"),

                # Warning components (need attention in 24-72h)
                html.Div([
                    html.H6("Medium Priority", className="text-warning mb-3"),
                    html.Div([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.Span(c["component"], className="fw-bold"),
                                    dbc.Badge(f"{c['risk']:.1f}% Risk",
                                              color="warning",
                                              className="ms-auto")
                                ], className="d-flex justify-content-between align-items-center mb-2"),

                                dbc.Progress(
                                    value=c["risk"],
                                    color="warning",
                                    className="mb-2",
                                    style={"height": "8px"}
                                ),

                                html.Div([
                                    html.Small(f"Hours until failure: {c['hours']}"),
                                    html.Small([
                                        html.I(className="bi bi-calendar me-1"),
                                        "Schedule maintenance within 72 hours"
                                    ], className="d-block mt-1")
                                ], className="small text-muted")
                            ])
                        ], className="mb-2 border-warning") for c in warning_components[:3]
                    ]) if warning_components else html.Div("No medium priority maintenance needed")
                ], className="mb-3")
            ]),

            # Maintenance recommendations box
            dbc.Card([
                dbc.CardHeader("Recommended Maintenance Schedule"),
                dbc.CardBody([
                    html.Div([
                        html.Strong(f"{component['component']}:", className="me-2"),
                        html.Span(component['recommendation'])
                    ], className="mb-2") for component in failure_predictions[:3]
                ])
            ], className="mt-3")
        ])

        # 5. COMPLETELY REDESIGNED Component Failure Prediction
        # Create component-specific failure cards
        component_failures = html.Div([
            dbc.Row([
                # Left column - Component failure probabilities
                dbc.Col([
                    html.Div([
                        html.H5("Component Failure Risk Analysis", className="mb-3"),

                        # Component detail cards
                        html.Div([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.Div([
                                        html.Span(f"{component['component']}", className="fw-bold"),
                                        html.Span(f"Risk Level: {component['risk']:.1f}%",
                                                  className="badge rounded-pill bg-danger ms-2"
                                                  if component['risk'] > 50 else
                                                  "badge rounded-pill bg-warning ms-2"
                                                  if component['risk'] > 30 else
                                                  "badge rounded-pill bg-success ms-2")
                                    ], className="d-flex justify-content-between align-items-center"),
                                ]),
                                dbc.CardBody([
                                    # Hours until failure
                                    html.Div([
                                        html.Span(f"Time until failure: ", className="me-2"),
                                        html.Strong(f"{component['hours']} hours",
                                                    className="text-danger" if component['hours'] < 24 else
                                                    "text-warning" if component['hours'] < 72 else
                                                    "text-success")
                                    ], className="mb-2"),

                                    # Contributing factors
                                    html.Div([
                                        html.Small("Contributing Factors:", className="text-muted d-block mb-1"),
                                        html.Ul([
                                            html.Li([
                                                html.Strong("OEE: "),
                                                f"{data['OEE']:.1f}" +
                                                (" (critical)"
                                                 if data['OEE'] < TARGETS['OEE'] * 0.9 else "")
                                            ]) if component['component'] in [c for c in COMPONENT_KPI_MATRIX if
                                                                             'OEE' in COMPONENT_KPI_MATRIX[
                                                                                 c]] else None,
                                            html.Li([
                                                html.Strong("PM Risk: "),
                                                f"{data['PM Risk']:.1f}" +
                                                (" (critical)"
                                                 if data['PM Risk'] > TARGETS['PM Risk'] * 1.1 else "")
                                            ]) if component['component'] in [c for c in COMPONENT_KPI_MATRIX if
                                                                             'PM Risk' in COMPONENT_KPI_MATRIX[
                                                                                 c]] else None,
                                            html.Li([
                                                html.Strong("Batt Efficiency: "),
                                                f"{data['Batt Efficiency']:.1f}" +
                                                (" (critical)"
                                                 if data['Batt Efficiency'] < TARGETS['Batt Efficiency'] * 0.9 else "")
                                            ]) if component['component'] in [c for c in COMPONENT_KPI_MATRIX if
                                                                             'Batt Efficiency' in COMPONENT_KPI_MATRIX[
                                                                                 c]] else None,
                                        ])
                                    ])
                                ])
                            ], className="mb-3 shadow-sm") for component in failure_predictions[:4]
                        ])
                    ])
                ], width=7),

                # Right column - Visual timeline
                dbc.Col([
                    html.Div([
                        html.H5("Failure Timeline", className="mb-3"),

                        # Timeline visualization
                        dcc.Graph(
                            figure=go.Figure(
                                data=[
                                    go.Scatter(
                                        x=[component['hours'] for component in failure_predictions[:8]],
                                        y=[component['risk'] for component in failure_predictions[:8]],
                                        mode='markers+text',
                                        text=[component['component'] for component in failure_predictions[:8]],
                                        textposition='top center',
                                        marker=dict(
                                            size=16,
                                            color=[
                                                '#ff4136' if component['risk'] > 50 else
                                                '#ffdc00' if component['risk'] > 30 else
                                                '#2ecc40'
                                                for component in failure_predictions[:8]
                                            ],
                                            symbol='diamond',
                                            line=dict(width=1, color='white')
                                        ),
                                        hovertemplate='<b>%{text}</b><br>Hours: %{x}<br>Risk: %{y:.1f}%<extra></extra>'
                                    )
                                ],
                                layout=go.Layout(
                                    height=300,
                                    template='plotly_dark',
                                    xaxis=dict(
                                        title='Hours until Failure',
                                        showgrid=True,
                                        gridcolor='rgba(255,255,255,0.1)'
                                    ),
                                    yaxis=dict(
                                        title='Risk Level (%)',
                                        showgrid=True,
                                        gridcolor='rgba(255,255,255,0.1)',
                                        range=[0, 100]
                                    ),
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    margin=dict(l=40, r=20, t=10, b=40)
                                )
                            ),
                            config={'displayModeBar': False}
                        )
                    ])
                ], width=5)
            ])
        ])

        return fig_trends, fig_forecast, fig_util, maintenance_timeline, component_failures

    except Exception as e:
        # Create error figures and content
        error_fig = go.Figure()
        error_fig.update_layout(
            template="plotly_dark",
            height=300,
            title=f"Error: {str(e)}",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        error_content = dbc.Alert(f"Error loading data: {str(e)}", color="danger")
        return error_fig, error_fig, error_fig, error_content, error_content


# ====================== FACTORY STATUS CALLBACK ======================
@app.callback(
    Output('factory-status-panel', 'children'),
    [Input('line-selector', 'value'),
     Input('interval', 'n_intervals'),
     Input('adapter-modes-store', 'data')]  # Add adapter modes input
)
def update_factory_status(line_id, n, adapter_modes):
    # Get mode for current line
    mode = adapter_modes.get(line_id, 'virtual')

    # Get adapter for selected production line and mode
    adapter = get_adapter(line_id, mode)

    try:
        # Get status from the adapter
        status = adapter.get_status()

        # Status badge color
        status_color = "success" if status["status"] == "Connected" else "danger"

        # Mode badge color
        mode_color = "info" if status["mode"] == "Simulation" else "warning"

        # Heartbeat recency
        if "last_update" in status and status["last_update"] != "Never":
            try:
                last_time = datetime.strptime(status["last_update"], "%H:%M:%S")
                now_time = datetime.strptime(datetime.now().strftime("%H:%M:%S"), "%H:%M:%S")
                seconds_ago = (now_time - last_time).total_seconds()
                heartbeat_text = f"{int(seconds_ago)}s ago"
                heartbeat_color = "success" if seconds_ago < 10 else "warning" if seconds_ago < 30 else "danger"
            except:
                heartbeat_text = status["last_update"]
                heartbeat_color = "info"
        else:
            heartbeat_text = "Never"
            heartbeat_color = "danger"

        return html.Div([
            # Connection status
            html.Div([
                html.I(className="bi bi-plug me-2"),
                html.Strong("Status: "),
                dbc.Badge(status["status"], color=status_color, className="me-2"),
                html.Span(status["message"])
            ], className="mb-2"),

            # Adapter mode
            html.Div([
                html.I(className="bi bi-cpu me-2"),
                html.Strong("Mode: "),
                dbc.Badge(status["mode"], color=mode_color, className="me-2")
            ], className="mb-2"),

            # Heartbeat monitor
            html.Div([
                html.I(className="bi bi-heart-pulse me-2"),
                html.Strong("Heartbeat: "),
                dbc.Badge(heartbeat_text, color=heartbeat_color)
            ]),

            # NEW: Adapter type information
            html.Div([
                html.I(className="bi bi-info-circle me-2"),
                html.Strong("Adapter: "),
                html.Span("OPC-UA" if mode == "production" else "Virtual Simulator")
            ], className="mt-3")
        ])

    except Exception as e:
        return dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            f"Error getting factory status: {str(e)}"
        ], color="danger")



# ====================== RUN APP ======================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run_server(debug=False, host='0.0.0.0', port=port)

# ====================== RUN APP ======================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run_server(debug=False, host='0.0.0.0', port=port)