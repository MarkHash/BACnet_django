/**
   * @jest-environment jsdom
*/

const { DeviceDetailManager } = require("../modules/device-detail.js");

describe('DeviceDetailManager', () => {
    let manager;

    beforeEach(() => {
        manager = new DeviceDetailManager();
        jest.clearAllMocks();
        document.body.innerHTML = '';
    });

    describe('Constructor', () => {
        test('should initialise with correct timeout values', () => {
            expect(manager.TIMEOUTS.BUTTON_RESET).toBe(3000);
            expect(manager.TIMEOUTS.POINT_CHECK_INTERVAL).toBe(2000);
            expect(manager.TIMEOUTS.DISCOVERY_TIMEOUT).toBe(30000);
            expect(manager.TIMEOUTS.REFRESH_INTERVAL).toBe(10000);
        });
    });

    describe('getDeviceId', () => {
        test('should return device ID when button exists', () => {
            document.body.innerHTML = `<button id="read-values-btn" data-device-id="12345">Read Values</button>`;
            const result = manager.getDeviceId();
            expect(result).toBe('12345');
        });
        test('should return null when button does not exists', () => {
            const result = manager.getDeviceId();
            expect(result).toBeNull();
        });
        test('should return null when button has no data-device-id', () => {
            document.body.innerHTML = `<button id="read-values-btn">Read Values</button>`;
            const result = manager.getDeviceId();
            expect(result).toBeNull();
        });
    });
        
    describe('updateLastUpdatedTime', () => {
        test('should update element with current time', () => {
            document.body.innerHTML = `<span id="values-last-updated">Old time</span>`;
            manager.updateLastUpdatedTime();
            const element = document.getElementById('values-last-updated');
            expect(element.textContent).toMatch(/^Last updated: /);
        });

        test('should handle missing element gracefully', () => {
            expect(() => manager.updateLastUpdatedTime()).not.toThrow();
        });
    });

    describe('updateSensorCards', () => {
        beforeEach(() => {
            document.body.innerHTML = `
                  <div data-point-id="1">
                      <div class="sensor-value">
                          <h4>Old Value</h4>
                      </div>
                      <div class="card-title">Old Name</div>
                  </div>
                  <div data-point-id="2">
                      <div class="sensor-value">
                          <h4>-</h4>
                      </div>
                      <div class="card-title">Point 2</div>
                  </div>
              `;
        });

        test('should update sensor card with display value', () => {
            const points = [{
                id: 1,
                display_value: '25.5°C',
                object_name: 'Temperature Sensor',
                identifier: 'AI:1'
              }];
              manager.updateSensorCards(points);
 
              const valueCell = document.querySelector('[data-point-id="1"] .sensor-value h4');
              const nameCell = document.querySelector('[data-point-id="1"] .card-title');

              expect(valueCell.textContent).toBe('25.5°C');
              expect(nameCell.textContent).toBe('Temperature Sensor');
        });

        test('should show dash when no display value', () => {
            const points = [{
                id: 2,
                display_value: null,
                object_name: '',
                identifier: 'AI:2'
            }];

            manager.updateSensorCards(points);

            const valueCell = document.querySelector('[data-point-id="2"] .sensor-value h4');
            const nameCell = document.querySelector('[data-point-id="2"] .card-title');

            expect(valueCell.textContent).toBe('-');
            expect(nameCell.textContent).toBe('AI:2');
        });

    test('should handle missing DOM elements gracefully', () => {
        const points = [{ id: 999, display_value: '123' }];

        expect(() => manager.updateSensorCards(points)).not.toThrow();
    });
        
    });

    describe('callApiAndHandleResponse', () => {
        test('should call onSuccess when API returns success', async () => {
            const mockResponse = { success: true, data: 'test' };
            global.apiCall.mockResolvedValue(mockResponse);

            const onSuccess = jest.fn();
            const onError = jest.fn();

            await manager.callApiAndHandleResponse('/test/', 'GET', onSuccess, onError);

            expect(onSuccess).toHaveBeenCalledWith(mockResponse);
            expect(onError).not.toHaveBeenCalled();
        });

        test('should call onError when API returns failure', async () => {
            const mockResponse = { success: false, message: 'Error occurred' };
            global.apiCall.mockResolvedValue(mockResponse);

            const onSuccess = jest.fn();
            const onError = jest.fn();

            await manager.callApiAndHandleResponse('/test/', 'GET', onSuccess, onError);

            expect(onError).toHaveBeenCalledWith('Error occurred');
            expect(onSuccess).not.toHaveBeenCalled();
        });
    });

    describe('updatePointTables', () => {
        beforeEach(() => {
            document.body.innerHTML = `
                <table class="table-sm">
                    <tbody>
                        <tr>
                            <td><code>1</code></td>
                            <td><strong>AI:1</strong></td>
                            <td>Old Name</td>
                        </tr>
                        <tr>
                            <td><code>2</code></td>
                            <td><strong>AI:2</strong></td>
                            <td><em class="text-muted">No Name</em></td>
                        </tr>
                    </tbody>
                </table>
            `;
        });

        test('should update point table with object name', () => {
            const points = [{
                identifier: 'AI:1',
                object_name: 'Temperature Sensor'
            }];

            manager.updatePointTables(points);

            const nameCell = document.querySelector('tbody tr:first-child td:last-child');
            expect(nameCell.textContent).toBe('Temperature Sensor');
        });

        test('should show "No Name" when object_name is empty', () => {
            const points = [{
                identifier: 'AI:2',
                object_name: ''
            }];

            manager.updatePointTables(points);

            const nameCell = document.querySelector('tbody tr:last-child td:last-child');
            expect(nameCell.innerHTML).toBe('<em class="text-muted">No Name</em>');
        });
    });
    describe('checkForNewPoints', () => {
        beforeEach(() => {
            document.body.innerHTML = `<button id="read-values-btn" data-device-id="123">Read Values</button>`;

            delete window.location;
            window.location = { reload: jest.fn() };
        });

        test('should reload page when new points found', async () => {
            const mockResponse = { success: true, total_points: 5 };
            global.apiCall.mockResolvedValue(mockResponse);

            await manager.checkForNewPoints();

            expect(global.apiCall).toHaveBeenCalledWith('/api/device-values/123/', 'GET');
            expect(window.location.reload).toHaveBeenCalled();
        });

        test('should not reload when no points found', async () => {
            const mockResponse = { success: true, total_points: 0 };
            global.apiCall.mockResolvedValue(mockResponse);

            await manager.checkForNewPoints();

            expect(window.location.reload).not.toHaveBeenCalled();
        });
    });

    describe('refreshSensorValues', () => {
        beforeEach(() => {
            document.body.innerHTML = `
                <button id="read-values-btn" data-device-id="456">Read Values</button>
                <span id="values-last-updated">Old time</span>
            `;
        });

        test('should update sensor display and timestamp', async () => {
            const mockResponse = {
                success: true,
                points: [{ id: 1, display_value: '25°C' }]
            };
            global.apiCall.mockResolvedValue(mockResponse);

            jest.spyOn(manager, 'updateSensorDisplay');
            jest.spyOn(manager, 'updateLastUpdatedTime');

            await manager.refreshSensorValues();

            expect(global.apiCall).toHaveBeenCalledWith('/api/device-values/456/', 'GET');
            expect(manager.updateSensorDisplay).toHaveBeenCalledWith(mockResponse.points);
            expect(manager.updateLastUpdatedTime).toHaveBeenCalled();
        });
    });
});