# Anomaly Detection Implementation Guide

## 🎯 **Implementation Guidance for Anomaly Detection**

### **Phase 1: Create ML Utilities Module**

**Step 1: Create `discovery/ml_utils.py`**
- [ ] Main `AnomalyDetector` class with configurable thresholds
- [ ] Statistical methods: Z-score, IQR (Interquartile Range), Moving Average
- [ ] ML method: Isolation Forest for more sophisticated detection
- [ ] Helper functions for data cleaning and feature preparation

**Key Design Decisions:**
- **Statistical methods first** - easier to implement, interpret, and debug
- **Numeric value filtering** - handle mixed data types (your readings have "inactive", "0.0", etc.)
- **Sliding window approach** - use last 24-48 hours for real-time detection
- **Configurable thresholds** - different sensors need different sensitivity

### **Phase 2: Integration with Existing Models**

**Step 2: Leverage Existing Fields**
- [ ] Use `BACnetReading.anomaly_score` (FloatField) - store the calculated score
- [ ] Use `BACnetReading.is_anomaly` (BooleanField) - flag readings as anomalous
- [ ] Enhance `BACnetReading.data_quality_score` calculation

**Step 3: Update Data Collection Flow**
- [ ] Modify reading collection process to:
  1. **Collect new reading**
  2. **Run anomaly detection** on the new value
  3. **Store anomaly score and flag**
  4. **Trigger alerts if needed**

### **Phase 3: Algorithm Implementation Strategy**

**Statistical Anomaly Detection (Start Here):**

- [ ] **Z-Score Method**: Compare new reading to historical mean/std deviation
- [ ] **IQR Method**: Detect outliers beyond 1.5 * IQR from quartiles
- [ ] **Moving Average**: Compare to recent trend

**Why These Work Well for HVAC Data:**
- Temperature sensors have predictable daily/seasonal patterns
- HVAC systems have operational ranges (20-25°C typical)
- Binary sensors (on/off) need different handling than analog

### **Phase 4: Data Preparation Challenges**

**Handle Mixed Data Types:**
Your backup data shows:
- Numeric values: `31.235036849975586`, `6.5`, `71.42857360839844`
- Binary states: `inactive`, `active`
- Zero values: `0.0` (could be real readings or sensor off)

**Filtering Strategy:**
- [ ] Skip non-numeric strings for statistical analysis
- [ ] Handle temperature sensors differently than binary outputs
- [ ] Use `point.object_type` to determine appropriate algorithm

### **Phase 5: Real-time Integration Points**

**Where to Add Anomaly Detection:**

- [ ] **In BACnetService** - during reading collection
- [ ] **In Celery tasks** - for batch processing
- [ ] **In API views** - for on-demand analysis

**Performance Considerations:**
- [ ] Cache recent statistical calculations
- [ ] Use database aggregations for efficiency
- [ ] Only run ML methods on sufficient data (50+ readings)

### **Phase 6: Alert System Design**

**Use Existing `AlarmHistory` Model:**
- [ ] Set `alarm_type = "anomaly_detected"`
- [ ] Include anomaly score in message
- [ ] Set appropriate severity levels

**Severity Thresholds (Suggested):**
- [ ] `critical`: score > 0.9 (immediate attention)
- [ ] `high`: score > 0.8 (investigate soon)
- [ ] `medium`: score > 0.7 (monitor closely)
- [ ] `low`: score < 0.7 (normal variation)

---

## 🚀 **Recommended Implementation Order**

### **Week 1-2: Foundation**
1. [ ] **Start with Z-score detection** for temperature sensors
2. [ ] **Test with your backup data** to tune thresholds
3. [ ] **Add IQR method** for better outlier detection
4. [ ] **Integrate with data collection workflow**

### **Week 3: Enhancement**
5. [ ] **Add API endpoints** for querying anomalies
6. [ ] **Implement real-time alerts**
7. [ ] **Add ML-based detection** (Isolation Forest)

### **Week 4: Polish**
8. [ ] **Performance optimization**
9. [ ] **Documentation and testing**
10. [ ] **Dashboard integration**

---

## 💡 **Key Success Factors**

### **Data Quality First:**
- [ ] Clean and validate numeric values
- [ ] Handle sensor-specific patterns (HVAC schedules)
- [ ] Account for maintenance periods (legitimate "anomalies")

### **Start Simple:**
- [ ] Basic statistical methods are often more reliable than complex ML
- [ ] Focus on temperature/humidity sensors first (most predictable)
- [ ] Gradually add complexity based on results

### **Resume-Friendly Features:**
- [ ] Document algorithm choices and parameter tuning
- [ ] Show before/after anomaly detection accuracy
- [ ] Demonstrate real-time processing capabilities

---

## 📊 **Implementation Details**

### **Core Algorithm Parameters**

**Z-Score Anomaly Detection:**
```python
# Configuration parameters to implement
z_score_threshold = 2.5  # Standard deviations
lookback_hours = 24      # Historical data window
min_readings = 5         # Minimum readings for statistical analysis
```

**IQR Anomaly Detection:**
```python
# Configuration parameters to implement
iqr_multiplier = 1.5     # IQR outlier multiplier
quartile_method = "interpolation"  # Calculation method
```

**Moving Average Detection:**
```python
# Configuration parameters to implement
window_size = 10         # Number of recent readings
deviation_threshold = 2.0  # Standard deviations from moving avg
```

### **Data Filtering Logic**

**Numeric Value Extraction:**
- [ ] Handle string representations of numbers
- [ ] Skip binary state values ("inactive", "active", "on", "off")
- [ ] Handle empty/null values gracefully
- [ ] Convert units if necessary

**Sensor Type Handling:**
- [ ] `analogInput`: Use all statistical methods
- [ ] `analogOutput`: Use trend-based detection
- [ ] `analogValue`: Use calculated value analysis
- [ ] `binaryInput/Output`: Use state change frequency analysis

### **Integration Points**

**BACnetService Integration:**
- [ ] Add anomaly detection call in `collect_reading()` method
- [ ] Store anomaly score with each reading
- [ ] Trigger alerts for high-score anomalies

**Celery Task Integration:**
- [ ] Create `detect_anomalies_batch` task
- [ ] Schedule periodic anomaly analysis
- [ ] Background processing for ML methods

**API Endpoint Integration:**
- [ ] `/api/anomalies/` - List recent anomalies
- [ ] `/api/anomalies/stats/` - Anomaly statistics
- [ ] `/api/devices/{id}/anomalies/` - Device-specific anomalies

---

## 🔍 **Testing Strategy**

### **Unit Tests:**
- [ ] Test each anomaly detection algorithm
- [ ] Test data filtering and cleaning
- [ ] Test threshold configuration

### **Integration Tests:**
- [ ] Test with real sensor data patterns
- [ ] Test alert generation workflow
- [ ] Test API endpoint responses

### **Performance Tests:**
- [ ] Measure detection speed for real-time processing
- [ ] Test with large datasets (thousands of readings)
- [ ] Monitor memory usage during ML training

---

## 📈 **Success Metrics**

### **Technical KPIs:**
- [ ] Anomaly detection accuracy > 85%
- [ ] False positive rate < 10%
- [ ] Detection latency < 5 seconds
- [ ] API response time < 200ms

### **Business Impact:**
- [ ] Identify real HVAC system issues
- [ ] Reduce false alarms
- [ ] Enable predictive maintenance
- [ ] Improve energy efficiency monitoring

### **Portfolio Demonstrations:**
- [ ] Real-time anomaly dashboard
- [ ] Historical anomaly analysis
- [ ] Alert system demonstration
- [ ] Performance benchmarking results

---

## 🛠️ **Required Dependencies**

### **Add to requirements.txt:**
```python
# ML and statistical analysis
scikit-learn>=1.3.0
numpy>=1.24.0
scipy>=1.10.0

# Optional: Advanced time series
# statsmodels>=0.14.0  # For seasonal analysis
# prophet>=1.1.4       # For forecasting
```

### **Database Considerations:**
- [ ] Add indexes for anomaly queries
- [ ] Consider partitioning for large time-series datasets
- [ ] Optimize for real-time insertion and analysis

---

**Next Steps:** Start with Phase 1 - Create the ML utilities module with basic Z-score detection for temperature sensors.