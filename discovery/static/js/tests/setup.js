require('@testing-library/jest-dom');

global.apiCall = jest.fn();
global.showAlert = jest.fn();

Object.defineProperty(window, 'location', {
    value: {
        reload: jest.fn()
    },
    writable: true
});

global.console = {
    ...console,
    log: jest.fn()
};
