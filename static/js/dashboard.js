/**
 * dashboard.js - Dashboard Management Module
 * Phase 5: Handles fetching, displaying, and managing pinned charts and reports
 */

const Dashboard = {
    pins: [],
    
    /**
     * Initialize dashboard
     */
    init() {
        console.log('[Dashboard] Initializing dashboard');
        
        // Load pins on page load
        this.loadPins();
        
        // Set up event listeners
        this.setupEventListeners();
    },
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                console.log('[Dashboard] Refreshing pins');
                this.loadPins();
            });
        }
    },
    
    /**
     * Load all pinned items from server
     */
    async loadPins() {
        console.log('[Dashboard] Loading pins from server');
        
        try {
            const response = await fetch('/get_pins');
            const result = await response.json();
            
            if (result.status === 'success') {
                this.pins = result.pins;
                console.log(`[Dashboard] Loaded ${this.pins.length} pins`);
                this.renderPins();
                this.updateStats();
            } else {
                console.error('[Dashboard] Failed to load pins:', result.error);
                this.showError('Failed to load pinned items');
            }
        } catch (error) {
            console.error('[Dashboard] Error loading pins:', error);
            this.showError('Error loading pinned items');
        }
    },
    
    /**
     * Render all pinned items
     */
    renderPins() {
        const container = document.getElementById('pinsContainer');
        const emptyState = document.getElementById('emptyState');
        
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        if (this.pins.length === 0) {
            // Show empty state
            container.classList.add('hidden');
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }
        
        // Hide empty state
        container.classList.remove('hidden');
        if (emptyState) emptyState.classList.add('hidden');
        
        // Create grid layout
        const grid = document.createElement('div');
        grid.className = 'grid grid-cols-1 lg:grid-cols-2 gap-6';
        
        // Render each pin
        this.pins.forEach(pin => {
            const pinCard = this.createPinCard(pin);
            grid.appendChild(pinCard);
        });
        
        container.appendChild(grid);
        
        // Render charts after DOM update
        setTimeout(() => {
            this.renderAllCharts();
        }, 100);
    },
    
    /**
     * Create a pin card element
     */
    createPinCard(pin) {
        const card = document.createElement('div');
        card.className = 'pin-card bg-white rounded-lg shadow-md overflow-hidden';
        card.dataset.pinId = pin.id;
        
        const typeIcon = pin.type === 'chart' ? '📊' : '📄';
        const typeColor = pin.type === 'chart' ? 'bg-green-100 text-green-800' : 'bg-purple-100 text-purple-800';
        
        // Format date
        const pinnedDate = new Date(pin.pinned_at).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        
        card.innerHTML = `
            <div class="p-6">
                <!-- Header -->
                <div class="flex justify-between items-start mb-4">
                    <div class="flex-1">
                        <div class="flex items-center space-x-2 mb-2">
                            <span class="text-2xl">${typeIcon}</span>
                            <span class="px-2 py-1 text-xs font-medium rounded-full ${typeColor}">
                                ${pin.type.toUpperCase()}
                            </span>
                        </div>
                        <h3 class="text-lg font-semibold text-gray-900">${this.escapeHtml(pin.title)}</h3>
                        <p class="text-sm text-gray-500 mt-1">Pinned on ${pinnedDate}</p>
                    </div>
                    <button 
                        class="delete-btn p-2 text-red-600 hover:bg-red-50 rounded-full transition"
                        onclick="Dashboard.deletePin('${pin.id}')"
                        title="Remove pin"
                    >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                </div>
                
                <!-- Content -->
                <div class="mt-4">
                    ${this.renderPinContent(pin)}
                </div>
            </div>
        `;
        
        return card;
    },
    
    /**
     * Render pin content based on type
     */
    renderPinContent(pin) {
        if (pin.type === 'chart' && pin.data) {
            // Chart placeholder - will be rendered by Plotly
            return `<div id="chart-${pin.id}" class="chart-container"></div>`;
        } else if (pin.type === 'report' && pin.data) {
            // Report summary
            return `
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="text-sm text-gray-700">
                        <p><strong>Type:</strong> ${pin.data.report_type || 'Data Report'}</p>
                        ${pin.data.summary ? `<p class="mt-2">${this.escapeHtml(pin.data.summary)}</p>` : ''}
                    </div>
                </div>
            `;
        } else {
            return `<p class="text-gray-500 italic">No preview available</p>`;
        }
    },
    
    /**
     * Render all charts using Plotly
     */
    renderAllCharts() {
        this.pins.forEach(pin => {
            if (pin.type === 'chart' && pin.data) {
                this.renderChart(pin);
            }
        });
    },
    
    /**
     * Render a single chart using Plotly
     */
    renderChart(pin) {
        const chartDiv = document.getElementById(`chart-${pin.id}`);
        if (!chartDiv) {
            console.warn(`[Dashboard] Chart container not found for pin ${pin.id}`);
            return;
        }
        
        try {
            // Extract Plotly data and layout
            const plotlyData = pin.data.plotly_data || pin.data.data || [];
            const plotlyLayout = pin.data.plotly_layout || pin.data.layout || {};
            
            // Set responsive layout
            const layout = {
                ...plotlyLayout,
                autosize: true,
                margin: { l: 50, r: 30, t: 30, b: 50 },
                height: 350
            };
            
            const config = {
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
            };
            
            // Render chart
            Plotly.newPlot(chartDiv, plotlyData, layout, config);
            console.log(`[Dashboard] Chart rendered for pin ${pin.id}`);
            
        } catch (error) {
            console.error(`[Dashboard] Error rendering chart for pin ${pin.id}:`, error);
            chartDiv.innerHTML = `<p class="text-red-500 text-sm">Error rendering chart</p>`;
        }
    },
    
    /**
     * Delete a pinned item
     */
    async deletePin(pinId) {
        if (!confirm('Are you sure you want to remove this pin?')) {
            return;
        }
        
        console.log(`[Dashboard] Deleting pin ${pinId}`);
        
        try {
            const response = await fetch(`/delete_pin/${pinId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                console.log(`[Dashboard] Pin deleted successfully: ${pinId}`);
                // Remove from local array
                this.pins = this.pins.filter(p => p.id !== pinId);
                // Re-render
                this.renderPins();
                this.updateStats();
                this.showSuccess('Pin removed successfully');
            } else {
                console.error('[Dashboard] Failed to delete pin:', result.error);
                this.showError('Failed to remove pin');
            }
        } catch (error) {
            console.error('[Dashboard] Error deleting pin:', error);
            this.showError('Error removing pin');
        }
    },
    
    /**
     * Update statistics
     */
    updateStats() {
        const totalPins = this.pins.length;
        const chartCount = this.pins.filter(p => p.type === 'chart').length;
        const reportCount = this.pins.filter(p => p.type === 'report').length;
        
        const totalPinsEl = document.getElementById('totalPins');
        const chartCountEl = document.getElementById('chartCount');
        const reportCountEl = document.getElementById('reportCount');
        
        if (totalPinsEl) totalPinsEl.textContent = totalPins;
        if (chartCountEl) chartCountEl.textContent = chartCount;
        if (reportCountEl) reportCountEl.textContent = reportCount;
        
        console.log(`[Dashboard] Stats updated - Total: ${totalPins}, Charts: ${chartCount}, Reports: ${reportCount}`);
    },
    
    /**
     * Show error message
     */
    showError(message) {
        // Simple alert for now - could be replaced with toast notifications
        alert(`Error: ${message}`);
    },
    
    /**
     * Show success message
     */
    showSuccess(message) {
        // Simple alert for now - could be replaced with toast notifications
        console.log(`[Dashboard] ${message}`);
    },
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Dashboard] DOM loaded, initializing...');
    Dashboard.init();
});

// Make Dashboard available globally
window.Dashboard = Dashboard;
