class DeviceDetailManager {
    constructor() {
        this.TIMEOUTS = {
            BUTTON_RESET: 3000,
            POINT_CHECK_INTERVAL: 2000,
            DISCOVERY_TIMEOUT: 30000,
            REFRESH_INTERVAL: 10000
        };
    }

    callApiAndHandleResponse(url, method, onSuccess, onError) {
        return apiCall(url, method)
            .then(response => {
                if (response.success) {
                    onSuccess(response);
                } else {
                    onError(response.message);
                }
            })
            .catch(error => onError(error.message));
    }

    updateSensorCards(points) {
        points.forEach(point => {
            const row = document.querySelector(`div[data-point-id="${point.id}"]`);
            if (row) {
                const valueCell = row.querySelector('.sensor-value h4');
                if (valueCell) {
                    if (point.display_value) {
                        valueCell.textContent = point.display_value;
                    } else {
                        valueCell.textContent = '-';
                    }
                }

                const nameCell = row.querySelector('.card-title');
                if (nameCell) {
                    if (point.object_name && point.object_name.trim()) {
                        nameCell.textContent = point.object_name;
                    } else {
                        nameCell.textContent = point.identifier;
                    }
                }
            }
        });
    }

    updatePointTables(points) {
        points.forEach(point => {
            const typeTableRows = document.querySelectorAll('.table-sm tbody tr');
            typeTableRows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 3) {
                    const instanceNumber = cells[0].querySelector('code')?.textContent?.trim();
                    const identifier = cells[1].querySelector('strong')?.textContent?.trim();

                    if (identifier === point.identifier) {
                        const nameCell = cells[2];
                        if (nameCell) {
                            if (point.object_name && point.object_name.trim()) {
                                nameCell.textContent = point.object_name;
                            } else {
                                nameCell.innerHTML = '<em class="text-muted">No Name</em>';
                            }
                        }
                    }
                }
            });
        });
    }

    updateSensorDisplay(points) {
        this.updateSensorCards(points);
        this.updatePointTables(points);
        showAlert('Sensor values refreshed!', 'success');

    }

    getDeviceId() {
        const button = document.getElementById('read-values-btn');
        return button ? button.getAttribute('data-device-id') : null;
    }

    updateLastUpdatedTime() {
        const element = document.getElementById('values-last-updated');
        if (element) {
            element.textContent = 'Last updated: ' + new Date().toLocaleString();
        }
    }

    checkForNewPoints() {
        const deviceId = this.getDeviceId();
        const url = `/api/device-values/${deviceId}/`;

        return this.callApiAndHandleResponse(url, 'GET',
            (response) => {
                if (response.total_points > 0) {
                    location.reload();
                }
            },
            () => console.log('Still waiting for points')
        );
    }

    refreshSensorValues() {
        const deviceId = this.getDeviceId();
        const url = `/api/device-values/${deviceId}/`;

        return this.callApiAndHandleResponse(url, 'GET',
            (response) => {
                this.updateSensorDisplay(response.points);
                this.updateLastUpdatedTime();
            },
            (error) => showAlert('Error refreshing values: ' + error, 'warning')
        );
    }
}

module.exports = { DeviceDetailManager };
