# Anomaly Dashboard Implementation Guide
**Date:** 2025-09-30
**Estimated Time:** 30-45 minutes
**Status:** Ready to implement - final piece for 100% complete anomaly detection

## 🎯 **Goal**
Create a web dashboard to visualize anomaly detection results, completing the full-stack anomaly detection feature.

## 📊 **Dashboard Features**

### **Core Features**
1. **Recent Anomalies Table** - Latest AlarmHistory records with full details
2. **Statistics Summary** - Total anomalies, severity breakdown, time-based counts
3. **Device Anomaly Ranking** - Top devices by anomaly count
4. **Interactive Filtering** - Time range (24h, 7d, 30d, all) and severity (high, medium, all)
5. **Real-time Data** - Shows current anomaly detection results from production system

### **Data Sources**
- **AlarmHistory Model** - Anomaly alarms with full diagnostic info
- **BACnetReading Model** - Combined anomaly scores for analysis
- **BACnetDevice/Point Models** - Device and sensor context

## 🛠 **Implementation Steps**

### **Step 1: Create Dashboard View**
**File:** `discovery/views.py`

Add this function:
```python
def anomaly_dashboard(request):
    """
    Dashboard view for displaying anomaly detection results and statistics.
    """
    from django.db.models import Count, Q
    from datetime import timedelta

    # Get filter parameters
    time_filter = request.GET.get('time', '24h')  # 24h, 7d, 30d, all
    severity_filter = request.GET.get('severity', 'all')  # high, medium, all

    # Base queryset for anomaly alarms
    base_qs = AlarmHistory.objects.filter(
        alarm_type='anomaly_detected'
    ).select_related('device', 'point').order_by('-triggered_at')

    # Apply time filtering
    if time_filter == '24h':
        cutoff_time = timezone.now() - timedelta(hours=24)
        base_qs = base_qs.filter(triggered_at__gte=cutoff_time)
    elif time_filter == '7d':
        cutoff_time = timezone.now() - timedelta(days=7)
        base_qs = base_qs.filter(triggered_at__gte=cutoff_time)
    elif time_filter == '30d':
        cutoff_time = timezone.now() - timedelta(days=30)
        base_qs = base_qs.filter(triggered_at__gte=cutoff_time)

    # Apply severity filtering
    if severity_filter != 'all':
        base_qs = base_qs.filter(severity=severity_filter)

    # Get recent anomalies (limit to 50 for dashboard)
    recent_anomalies = base_qs[:50]

    # Get statistics
    total_anomalies = base_qs.count()
    high_severity_count = base_qs.filter(severity='high').count()
    medium_severity_count = base_qs.filter(severity='medium').count()

    # Device anomaly summary
    device_stats = base_qs.values('device__device_id', 'device__address').annotate(
        anomaly_count=Count('id')
    ).order_by('-anomaly_count')[:10]

    context = {
        'recent_anomalies': recent_anomalies,
        'total_anomalies': total_anomalies,
        'high_severity_count': high_severity_count,
        'medium_severity_count': medium_severity_count,
        'device_stats': device_stats,
        'time_filter': time_filter,
        'severity_filter': severity_filter,
    }

    return render(request, 'discovery/anomaly_dashboard.html', context)
```

**Don't forget:** Add import if needed:
```python
from .models import AlarmHistory  # Add this if not already imported
```

### **Step 2: Create HTML Template**
**File:** `discovery/templates/discovery/anomaly_dashboard.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anomaly Detection Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .anomaly-high { background-color: #f8d7da; }
        .anomaly-medium { background-color: #fff3cd; }
        .stat-card { margin-bottom: 20px; }
        .filter-section { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-12">
                <h1 class="mt-3 mb-4">🚨 Anomaly Detection Dashboard</h1>

                <!-- Filter Section -->
                <div class="filter-section">
                    <form method="get" class="row g-3">
                        <div class="col-md-4">
                            <label for="time" class="form-label">Time Range:</label>
                            <select name="time" id="time" class="form-select">
                                <option value="24h" {% if time_filter == '24h' %}selected{% endif %}>Last 24 Hours</option>
                                <option value="7d" {% if time_filter == '7d' %}selected{% endif %}>Last 7 Days</option>
                                <option value="30d" {% if time_filter == '30d' %}selected{% endif %}>Last 30 Days</option>
                                <option value="all" {% if time_filter == 'all' %}selected{% endif %}>All Time</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label for="severity" class="form-label">Severity:</label>
                            <select name="severity" id="severity" class="form-select">
                                <option value="all" {% if severity_filter == 'all' %}selected{% endif %}>All Severities</option>
                                <option value="high" {% if severity_filter == 'high' %}selected{% endif %}>High Only</option>
                                <option value="medium" {% if severity_filter == 'medium' %}selected{% endif %}>Medium Only</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">&nbsp;</label>
                            <button type="submit" class="form-control btn btn-primary">Apply Filters</button>
                        </div>
                    </form>
                </div>

                <!-- Statistics Cards -->
                <div class="row stat-cards">
                    <div class="col-md-3">
                        <div class="card stat-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Total Anomalies</h5>
                                <h2 class="text-primary">{{ total_anomalies }}</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stat-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">High Severity</h5>
                                <h2 class="text-danger">{{ high_severity_count }}</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stat-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Medium Severity</h5>
                                <h2 class="text-warning">{{ medium_severity_count }}</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stat-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">System Status</h5>
                                <h3 class="{% if total_anomalies == 0 %}text-success{% else %}text-warning{% endif %}">
                                    {% if total_anomalies == 0 %}✅ Normal{% else %}⚠️ Monitoring{% endif %}
                                </h3>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Anomalies Table -->
                <div class="card">
                    <div class="card-header">
                        <h5>Recent Anomalies ({{ recent_anomalies|length }} shown)</h5>
                    </div>
                    <div class="card-body">
                        {% if recent_anomalies %}
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Timestamp</th>
                                        <th>Device</th>
                                        <th>Point</th>
                                        <th>Value</th>
                                        <th>Severity</th>
                                        <th>Anomaly Score</th>
                                        <th>Details</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for anomaly in recent_anomalies %}
                                    <tr class="{% if anomaly.severity == 'high' %}anomaly-high{% elif anomaly.severity == 'medium' %}anomaly-medium{% endif %}">
                                        <td>{{ anomaly.triggered_at|date:"M d, H:i" }}</td>
                                        <td>
                                            <strong>{{ anomaly.device.device_id }}</strong><br>
                                            <small class="text-muted">{{ anomaly.device.address }}</small>
                                        </td>
                                        <td>{{ anomaly.point.identifier }}</td>
                                        <td><strong>{{ anomaly.triggered_value }}</strong></td>
                                        <td>
                                            <span class="badge {% if anomaly.severity == 'high' %}bg-danger{% else %}bg-warning{% endif %}">
                                                {{ anomaly.severity|title }}
                                            </span>
                                        </td>
                                        <td>{{ anomaly.threshold_value }}</td>
                                        <td>
                                            <small>{{ anomaly.message }}</small>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        {% else %}
                        <div class="alert alert-success" role="alert">
                            <h4 class="alert-heading">🎉 No Anomalies Detected!</h4>
                            <p>Your BACnet system is operating normally. All sensor readings are within expected ranges.</p>
                        </div>
                        {% endif %}
                    </div>
                </div>

                <!-- Device Statistics -->
                {% if device_stats %}
                <div class="card mt-4">
                    <div class="card-header">
                        <h5>Top Devices by Anomaly Count</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Device ID</th>
                                        <th>Address</th>
                                        <th>Anomaly Count</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for device in device_stats %}
                                    <tr>
                                        <td><strong>{{ device.device__device_id }}</strong></td>
                                        <td>{{ device.device__address }}</td>
                                        <td>
                                            <span class="badge bg-secondary">{{ device.anomaly_count }}</span>
                                        </td>
                                        <td>
                                            {% if device.anomaly_count > 10 %}
                                                <span class="text-danger">⚠️ High Alert</span>
                                            {% elif device.anomaly_count > 5 %}
                                                <span class="text-warning">🔍 Monitor</span>
                                            {% else %}
                                                <span class="text-success">✅ Normal</span>
                                            {% endif %}
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                {% endif %}

                <!-- Navigation Back -->
                <div class="mt-4 mb-4">
                    <a href="{% url 'discovery:dashboard' %}" class="btn btn-secondary">← Back to Main Dashboard</a>
                    <a href="{% url 'discovery:device-status-api-v2' %}" class="btn btn-info">📊 API Status</a>
                    <a href="/api/docs/" class="btn btn-success">📖 API Documentation</a>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

### **Step 3: Add URL Routing**
**File:** `discovery/urls.py`

Add this line to your `urlpatterns`:
```python
urlpatterns = [
    # ... existing patterns ...
    path("anomaly-dashboard/", views.anomaly_dashboard, name="anomaly_dashboard"),
]
```

### **Step 4: Test the Dashboard**
1. **Start Django server:** `python manage.py runserver`
2. **Navigate to:** `http://127.0.0.1:8000/discovery/anomaly-dashboard/`
3. **Test filters:** Try different time ranges and severity filters
4. **Verify data:** Check that your AlarmHistory data displays correctly

## 🎯 **Expected Results**

### **If You Have Anomalies:**
- Statistics cards showing counts by severity
- Recent anomalies table with full diagnostic info
- Device rankings by anomaly frequency
- Interactive filtering working

### **If No Anomalies (Healthy System):**
- Green "No Anomalies Detected" success message
- Zero counts in statistics
- Clean, professional layout

## 🚀 **Enhancement Ideas (Optional)**

### **Quick Additions (5-10 minutes each):**
1. **Auto-refresh:** Add JavaScript to refresh every 30 seconds
2. **Export functionality:** Add CSV download button
3. **Charts:** Simple chart.js visualization of anomaly trends
4. **Search:** Add device/point search functionality

### **Advanced Features (Future):**
1. **Real-time updates:** WebSocket integration
2. **Anomaly acknowledgment:** Mark anomalies as reviewed
3. **Threshold adjustment:** Dynamic threshold configuration
4. **Notification settings:** Email/SMS alert configuration

## 📊 **Portfolio Impact**

This dashboard completes your anomaly detection feature with:
- ✅ **Full-stack demonstration:** Backend ML + Frontend visualization
- ✅ **Production-ready interface:** Professional design with Bootstrap
- ✅ **Interactive features:** Filtering, sorting, real-time data
- ✅ **Business value:** Operational monitoring for building management

## 🎉 **Success Criteria**

### **Completion Checklist:**
- [ ] Dashboard view function implemented
- [ ] HTML template created with all sections
- [ ] URL routing added
- [ ] Dashboard loads without errors
- [ ] Statistics display correctly
- [ ] Filtering works as expected
- [ ] Data from AlarmHistory displays properly
- [ ] Navigation links work

### **Demo Points for Interviews:**
1. **Real-time anomaly monitoring** - Show live detection results
2. **Ensemble ML algorithms** - Explain Z-score + IQR combination
3. **Production integration** - Demonstrate alarm system integration
4. **Data visualization** - Interactive filtering and statistics
5. **System architecture** - End-to-end data flow from sensors to dashboard

---

**Time Estimate:** 30-45 minutes total implementation
**Result:** 100% complete anomaly detection system ready for portfolio presentation

**Next Feature:** Energy Analytics Pipeline for advanced ML capabilities